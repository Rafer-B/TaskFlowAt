
<script setup lang="ts">
definePageMeta({
  layout: 'admin',
})

interface Utilizador {
  id: number
  name: string
  email: string
  avatar_url: string | null
  is_active: boolean
  created_at: string
}

interface UtilizadorCreate {
  name: string
  email: string
  password: string
}

const config = useRuntimeConfig()
const apiBase = String(config.public.apiBase).replace(/\/+$/, '')

const utilizadores = ref<Utilizador[]>([])
const carregando = ref(true)
const submetendo = ref(false)

const erro = ref('')
const sucesso = ref('')

const pesquisa = ref('')
const mostrarFormulario = ref(false)

const utilizadorAAtualizar = ref<number | null>(null)
const fotografiasComErro = ref<number[]>([])

const formulario = reactive<UtilizadorCreate>({
  name: '',
  email: '',
  password: '',
})

const utilizadoresFiltrados = computed(() => {
  const termo = pesquisa.value.trim().toLowerCase()

  if (!termo) return utilizadores.value

  return utilizadores.value.filter((u) =>
    u.name.toLowerCase().includes(termo) ||
    u.email.toLowerCase().includes(termo),
  )
})

const totalAtivos = computed(
  () => utilizadores.value.filter((u) => u.is_active).length,
)

const totalInativos = computed(
  () => utilizadores.value.filter((u) => !u.is_active).length,
)

function obterUrlFotografia(avatarUrl: string | null): string {
  if (!avatarUrl) return ''

  if (avatarUrl.startsWith('http://') || avatarUrl.startsWith('https://')) {
    return avatarUrl
  }

  const caminho = avatarUrl.startsWith('/')
    ? avatarUrl
    : `/${avatarUrl}`

  return `${apiBase}${caminho}`
}

function fotografiaFalhou(utilizadorId: number) {
  if (!fotografiasComErro.value.includes(utilizadorId)) {
    fotografiasComErro.value.push(utilizadorId)
  }
}

function fotografiaCarregada(utilizadorId: number) {
  fotografiasComErro.value = fotografiasComErro.value.filter(
    (id) => id !== utilizadorId,
  )
}

function obterIniciais(nome: string): string {
  return nome
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((parte) => parte.charAt(0).toUpperCase())
    .join('')
}

function limparMensagens() {
  erro.value = ''
  sucesso.value = ''
}

function obterMensagemErro(error: unknown): string {
  const resposta = error as {
    data?: {
      detail?: string | { msg?: string }[]
    }
    message?: string
  }

  const detalhe = resposta?.data?.detail

  if (typeof detalhe === 'string') {
    return detalhe
  }

  if (Array.isArray(detalhe)) {
    return detalhe
      .map((item) => item.msg ?? 'Dados inválidos')
      .join(' ')
  }

  return resposta?.message ?? 'Ocorreu um erro ao comunicar com a API.'
}

function formatarData(data: string): string {
  const valor = new Date(data)

  if (Number.isNaN(valor.getTime())) {
    return 'Data indisponível'
  }

  return new Intl.DateTimeFormat('pt-PT', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(valor)
}

async function carregarUtilizadores() {
  carregando.value = true
  erro.value = ''

  try {
    utilizadores.value = await $fetch<Utilizador[]>(
      `${apiBase}/users/`,
    )

    fotografiasComErro.value = []
  } catch (error) {
    console.error('Erro ao carregar utilizadores:', error)
    erro.value = obterMensagemErro(error)
  } finally {
    carregando.value = false
  }
}

async function carregarFotografia(
  utilizador: Utilizador,
  evento: Event,
) {
  limparMensagens()

  const input = evento.target as HTMLInputElement
  const ficheiro = input.files?.[0]

  if (!ficheiro) return

  const formatosPermitidos = [
    'image/jpeg',
    'image/png',
    'image/webp',
  ]

  if (!formatosPermitidos.includes(ficheiro.type)) {
    erro.value = 'Formato inválido. Escolhe uma imagem JPG, PNG ou WEBP.'
    input.value = ''
    return
  }

  if (ficheiro.size > 5 * 1024 * 1024) {
    erro.value = 'A fotografia não pode ultrapassar 5 MB.'
    input.value = ''
    return
  }

  const dados = new FormData()
  dados.append('file', ficheiro)

  utilizadorAAtualizar.value = utilizador.id

  try {
    const resposta = await $fetch<Partial<Utilizador>>(
      `${apiBase}/users/${utilizador.id}/avatar`,
      {
        method: 'POST',
        body: dados,
      },
    )

    const indice = utilizadores.value.findIndex(
      (u) => u.id === utilizador.id,
    )

    if (indice !== -1) {
      utilizadores.value[indice] = {
        ...utilizadores.value[indice],
        ...resposta,
        avatar_url: resposta.avatar_url ?? utilizadores.value[indice].avatar_url,
      }

      fotografiasComErro.value = fotografiasComErro.value.filter(
        (id) => id !== utilizador.id,
      )
    }

    sucesso.value = 'Fotografia de perfil atualizada com sucesso!'
  } catch (error) {
    console.error('Erro ao carregar fotografia:', error)
    erro.value = obterMensagemErro(error)
  } finally {
    utilizadorAAtualizar.value = null
    input.value = ''
  }
}

function abrirFormulario() {
  limparMensagens()
  mostrarFormulario.value = true
}

function fecharFormulario() {
  mostrarFormulario.value = false
  formulario.name = ''
  formulario.email = ''
  formulario.password = ''
}

async function criarUtilizador() {
  limparMensagens()

  if (formulario.name.trim().length < 2) {
    erro.value = 'O nome deve ter pelo menos 2 caracteres.'
    return
  }

  if (!formulario.email.trim()) {
    erro.value = 'Introduz um endereço de email.'
    return
  }

  if (formulario.password.length < 8) {
    erro.value = 'A palavra-passe deve ter pelo menos 8 caracteres.'
    return
  }

  submetendo.value = true

  try {
    const novoUtilizador = await $fetch<Utilizador>(
      `${apiBase}/users/`,
      {
        method: 'POST',
        body: {
          name: formulario.name.trim(),
          email: formulario.email.trim().toLowerCase(),
          password: formulario.password,
        },
      },
    )

    utilizadores.value.unshift(novoUtilizador)

    sucesso.value = 'Utilizador criado com sucesso!'
    fecharFormulario()
  } catch (error) {
    console.error('Erro ao criar utilizador:', error)
    erro.value = obterMensagemErro(error)
  } finally {
    submetendo.value = false
  }
}

onMounted(carregarUtilizadores)
</script>

<template>
  <div class="users-page">
    <header class="page-heading">
      <div>
        <span class="eyebrow">GESTÃO DA PLATAFORMA</span>
        <h2>Utilizadores</h2>
        <p>
          Consulte e registe os utilizadores da plataforma TaskFlow.
        </p>
      </div>

      <button class="primary-button" @click="abrirFormulario">
        <span>＋</span>
        Novo utilizador
      </button>
    </header>

    <section class="stats-grid">
      <article class="stat-card">
        <div class="stat-icon total-icon">♙</div>
        <div>
          <span>Total de utilizadores</span>
          <strong>{{ utilizadores.length }}</strong>
        </div>
      </article>

      <article class="stat-card">
        <div class="stat-icon active-icon">✓</div>
        <div>
          <span>Utilizadores ativos</span>
          <strong>{{ totalAtivos }}</strong>
        </div>
      </article>

      <article class="stat-card">
        <div class="stat-icon inactive-icon">○</div>
        <div>
          <span>Utilizadores inativos</span>
          <strong>{{ totalInativos }}</strong>
        </div>
      </article>
    </section>

    <div v-if="erro" class="message error-message" role="alert">
      <span>!</span>
      {{ erro }}
      <button @click="erro = ''" aria-label="Fechar mensagem">×</button>
    </div>

    <div v-if="sucesso" class="message success-message" role="status">
      <span>✓</span>
      {{ sucesso }}
      <button @click="sucesso = ''" aria-label="Fechar mensagem">×</button>
    </div>

    <section class="users-panel">
      <div class="panel-heading">
        <div>
          <h3>Lista de utilizadores</h3>
          <p>Utilizadores registados na base de dados.</p>
        </div>

        <label class="search-field">
          <span>⌕</span>
          <input
            v-model="pesquisa"
            type="search"
            placeholder="Pesquisar nome ou email..."
          />
        </label>
      </div>

      <div v-if="carregando" class="empty-state">
        <span class="loader"></span>
        <p>A carregar utilizadores...</p>
      </div>

      <div
        v-else-if="utilizadoresFiltrados.length === 0"
        class="empty-state"
      >
        <div class="empty-icon">♙</div>
        <h3>
          {{
            pesquisa
              ? 'Nenhum resultado encontrado'
              : 'Ainda não existem utilizadores'
          }}
        </h3>
        <p>
          {{
            pesquisa
              ? 'Experimenta pesquisar por outro nome ou email.'
              : 'Cria o primeiro utilizador para começar.'
          }}
        </p>
      </div>

      <div v-else class="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>UTILIZADOR</th>
              <th>EMAIL</th>
              <th>DATA DE REGISTO</th>
              <th>ESTADO</th>
            </tr>
          </thead>

          <tbody>
            <tr
              v-for="utilizador in utilizadoresFiltrados"
              :key="utilizador.id"
            >
              <td>
                <div class="user-cell">
                  <div class="user-avatar">
                    <img
                      v-if="utilizador.avatar_url && !fotografiasComErro.includes(utilizador.id)"
                      :src="obterUrlFotografia(utilizador.avatar_url)"
                      :alt="`Fotografia de ${utilizador.name}`"
                      @error="fotografiaFalhou(utilizador.id)"
                      @load="fotografiaCarregada(utilizador.id)"
                    />

                    <span v-else>
                      {{ obterIniciais(utilizador.name) }}
                    </span>
                  </div>

                  <div class="user-name">
                    <strong>{{ utilizador.name }}</strong>
                    <span>ID #{{ utilizador.id }}</span>

                    <label
                      class="avatar-upload"
                      :class="{
                        uploading: utilizadorAAtualizar === utilizador.id,
                      }"
                    >
                      {{
                        utilizadorAAtualizar === utilizador.id
                          ? 'A carregar fotografia...'
                          : 'Alterar fotografia'
                      }}

                      <input
                        type="file"
                        accept="image/jpeg,image/png,image/webp"
                        :disabled="utilizadorAAtualizar === utilizador.id"
                        @change="carregarFotografia(utilizador, $event)"
                      />
                    </label>
                  </div>
                </div>
              </td>

              <td class="email-cell">{{ utilizador.email }}</td>

              <td class="date-cell">
                {{ formatarData(utilizador.created_at) }}
              </td>

              <td>
                <span
                  class="status-badge"
                  :class="
                    utilizador.is_active
                      ? 'status-active'
                      : 'status-inactive'
                  "
                >
                  <span></span>
                  {{ utilizador.is_active ? 'Ativo' : 'Inativo' }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="panel-footer">
        <span>
          A apresentar {{ utilizadoresFiltrados.length }}
          de {{ utilizadores.length }} utilizadores
        </span>

        <button
          class="refresh-button"
          :disabled="carregando"
          @click="carregarUtilizadores"
        >
          ↻ Atualizar lista
        </button>
      </div>
    </section>

    <div
      v-if="mostrarFormulario"
      class="modal-backdrop"
      @click.self="fecharFormulario"
    >
      <section
        class="user-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
      >
        <div class="modal-heading">
          <div>
            <span class="eyebrow">GESTÃO DE ACESSOS</span>
            <h2 id="modal-title">Novo utilizador</h2>
            <p>Preenche os dados para registar um utilizador.</p>
          </div>

          <button
            class="modal-close"
            aria-label="Fechar formulário"
            @click="fecharFormulario"
          >
            ×
          </button>
        </div>

        <form @submit.prevent="criarUtilizador">
          <div class="form-group">
            <label for="name">Nome completo</label>
            <input
              id="name"
              v-model="formulario.name"
              type="text"
              minlength="2"
              maxlength="100"
              placeholder="Ex.: João Silva"
              required
            />
          </div>

          <div class="form-group">
            <label for="email">Endereço de email</label>
            <input
              id="email"
              v-model="formulario.email"
              type="email"
              placeholder="nome@exemplo.com"
              required
            />
          </div>

          <div class="form-group">
            <label for="password">Palavra-passe</label>
            <input
              id="password"
              v-model="formulario.password"
              type="password"
              minlength="8"
              maxlength="128"
              placeholder="Mínimo de 8 caracteres"
              required
            />
            <small>
              A palavra-passe será enviada à API para ser guardada com hash.
            </small>
          </div>

          <div class="modal-actions">
            <button
              type="button"
              class="secondary-button"
              :disabled="submetendo"
              @click="fecharFormulario"
            >
              Cancelar
            </button>

            <button
              type="submit"
              class="primary-button"
              :disabled="submetendo"
            >
              {{ submetendo ? 'A criar...' : 'Criar utilizador' }}
            </button>
          </div>
        </form>
      </section>
    </div>
  </div>
</template>

<style scoped>
.users-page {
  display: flex;
  flex-direction: column;
  gap: 22px;
  max-width: 1500px;
  margin: 0 auto;
  color: #172b4d;
}

.page-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}

.eyebrow {
  color: #7185aa;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.12em;
}

.page-heading h2 {
  margin: 7px 0;
  font-size: 27px;
  font-weight: 800;
  letter-spacing: -0.04em;
}

.page-heading p,
.panel-heading p {
  margin: 0;
  color: #8795aa;
  font-size: 13px;
}

.primary-button,
.secondary-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 42px;
  padding: 0 17px;
  border-radius: 9px;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: 0.2s ease;
}

.primary-button {
  color: #fff;
  background: #4164dc;
  border: 1px solid #4164dc;
}

.primary-button:hover:not(:disabled) {
  background: #3152c2;
}

.primary-button:disabled,
.secondary-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.primary-button > span {
  font-size: 19px;
}

.secondary-button {
  color: #53657f;
  background: #fff;
  border: 1px solid #dce4ef;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 14px;
  min-height: 105px;
  padding: 20px;
  background: #fff;
  border: 1px solid #e5ebf4;
  border-radius: 13px;
  box-shadow: 0 3px 12px rgb(30 55 90 / 3%);
}

.stat-icon {
  display: grid;
  flex: 0 0 43px;
  width: 43px;
  height: 43px;
  place-items: center;
  border-radius: 12px;
  font-size: 20px;
}

.total-icon {
  color: #4164dc;
  background: #edf1ff;
}

.active-icon {
  color: #16865c;
  background: #e8f7ef;
}

.inactive-icon {
  color: #bd8530;
  background: #fff5e5;
}

.stat-card > div:last-child {
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.stat-card span {
  color: #8795aa;
  font-size: 11px;
}

.stat-card strong {
  color: #172b4d;
  font-size: 25px;
  line-height: 1;
}

.users-panel {
  overflow: hidden;
  background: #fff;
  border: 1px solid #e5ebf4;
  border-radius: 13px;
  box-shadow: 0 3px 12px rgb(30 55 90 / 3%);
}

.panel-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 21px 23px;
  border-bottom: 1px solid #edf0f5;
}

.panel-heading h3 {
  margin: 0 0 6px;
  font-size: 15px;
  font-weight: 800;
}

.search-field {
  display: flex;
  align-items: center;
  gap: 9px;
  width: min(300px, 100%);
  height: 39px;
  padding: 0 11px;
  color: #8493a9;
  background: #f7f9fc;
  border: 1px solid #e5ebf3;
  border-radius: 8px;
}

.search-field input {
  width: 100%;
  min-width: 0;
  color: #263957;
  background: transparent;
  border: 0;
  outline: none;
  font-size: 11px;
}

.table-wrapper {
  width: 100%;
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

thead {
  background: #f9fafc;
}

th {
  padding: 13px 20px;
  color: #91a0b4;
  font-size: 9px;
  font-weight: 800;
  letter-spacing: 0.08em;
  white-space: nowrap;
}

td {
  padding: 15px 20px;
  border-top: 1px solid #edf0f5;
  font-size: 12px;
  white-space: nowrap;
}

tbody tr:hover {
  background: #fbfcff;
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 11px;
}

.user-avatar {
  display: flex;
  flex: 0 0 42px;
  width: 42px;
  height: 42px;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  color: #4164dc;
  background: #edf1ff;
  border-radius: 50%;
  font-size: 11px;
  font-weight: 800;
}

.user-avatar img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
}

.user-avatar > span {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
}

.user-name {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.user-name strong {
  color: #263957;
  font-size: 12px;
}

.user-name > span {
  color: #9aa7ba;
  font-size: 10px;
}

.avatar-upload {
  display: inline-block;
  width: fit-content;
  margin-top: 3px;
  color: #4164dc;
  font-size: 10px;
  font-weight: 600;
  cursor: pointer;
}

.avatar-upload:hover {
  color: #3152c2;
  text-decoration: underline;
}

.avatar-upload input {
  display: none;
}

.avatar-upload.uploading {
  opacity: 0.6;
  cursor: wait;
}

.email-cell,
.date-cell {
  color: #66768e;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 6px 9px;
  border-radius: 20px;
  font-size: 10px;
  font-weight: 700;
}

.status-badge > span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.status-active {
  color: #16865c;
  background: #e9f7ef;
}

.status-active > span {
  background: #20a36e;
}

.status-inactive {
  color: #a36d20;
  background: #fff5e5;
}

.status-inactive > span {
  background: #d89a36;
}

.panel-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 15px 22px;
  color: #8b99ad;
  border-top: 1px solid #edf0f5;
  font-size: 10px;
}

.refresh-button {
  color: #4164dc;
  background: transparent;
  border: 0;
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
}

.refresh-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 230px;
  padding: 25px;
  text-align: center;
}

.empty-state h3 {
  margin: 12px 0 6px;
  font-size: 14px;
}

.empty-state p {
  margin: 0;
  color: #8b99ad;
  font-size: 11px;
}

.empty-icon {
  display: grid;
  width: 45px;
  height: 45px;
  place-items: center;
  color: #4164dc;
  background: #edf1ff;
  border-radius: 13px;
  font-size: 23px;
}

.loader {
  width: 24px;
  height: 24px;
  border: 3px solid #e3eafa;
  border-top-color: #4164dc;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.message {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 9px;
  font-size: 12px;
}

.message button {
  margin-left: auto;
  color: inherit;
  background: transparent;
  border: 0;
  font-size: 18px;
  cursor: pointer;
}

.error-message {
  color: #b42318;
  background: #fff0ef;
  border: 1px solid #f7d2ce;
}

.success-message {
  color: #16865c;
  background: #eaf8f0;
  border: 1px solid #c8ebd7;
}

.modal-backdrop {
  position: fixed;
  inset: 0;
  display: grid;
  place-items: center;
  padding: 18px;
  background: rgb(13 27 49 / 55%);
  backdrop-filter: blur(3px);
  z-index: 200;
}

.user-modal {
  width: min(100%, 480px);
  padding: 25px;
  background: #fff;
  border: 1px solid #e5ebf4;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgb(0 0 0 / 18%);
}

.modal-heading {
  display: flex;
  justify-content: space-between;
  gap: 15px;
  margin-bottom: 25px;
}

.modal-heading h2 {
  margin: 7px 0;
  color: #172b4d;
  font-size: 22px;
}

.modal-heading p {
  margin: 0;
  color: #8795aa;
  font-size: 12px;
}

.modal-close {
  width: 32px;
  height: 32px;
  color: #728198;
  background: #f3f6fa;
  border: 0;
  border-radius: 8px;
  font-size: 21px;
  cursor: pointer;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 18px;
}

.form-group label {
  color: #354966;
  font-size: 11px;
  font-weight: 700;
}

.form-group input {
  width: 100%;
  height: 43px;
  padding: 0 12px;
  box-sizing: border-box;
  color: #263957;
  background: #fbfcfe;
  border: 1px solid #dce4ef;
  border-radius: 8px;
  outline: none;
  font: inherit;
  font-size: 12px;
}

.form-group input:focus {
  border-color: #6485ff;
  box-shadow: 0 0 0 3px rgb(100 133 255 / 12%);
}

.form-group small {
  color: #8b99ad;
  font-size: 10px;
  line-height: 1.5;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 25px;
  padding-top: 18px;
  border-top: 1px solid #edf0f5;
}

@media (max-width: 750px) {
  .stats-grid {
    grid-template-columns: 1fr;
    gap: 10px;
  }

  .stat-card {
    min-height: 82px;
  }

  .page-heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .panel-heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .search-field {
    width: 100%;
    box-sizing: border-box;
  }
}

@media (max-width: 480px) {
  .page-heading h2 {
    font-size: 23px;
  }

  .primary-button {
    width: 100%;
  }

  .user-modal {
    padding: 19px;
  }

  .modal-actions {
    flex-direction: column-reverse;
  }

  .modal-actions button {
    width: 100%;
  }

  .panel-footer {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
