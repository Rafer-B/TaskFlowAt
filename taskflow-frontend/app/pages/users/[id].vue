<script setup lang="ts">
import { fetchAllPages } from '~/composables/usePaginatedApi'
definePageMeta({
  layout: 'admin',
})

interface Utilizador {
  id: string
  name: string
  email: string
  role: 'admin' | 'member'
  avatar_url: string | null
  is_active: boolean
  created_at: string
}

interface TarefaAssociada {
  id: string
  project_id: string
  title: string
  status: 'to_do' | 'in_progress' | 'completed' | 'blocked'
  priority: 'low' | 'medium' | 'high'
  due_date: string | null
}

interface ProjetoResumo {
  id: string
  name: string
}

interface EquipaResumo {
  id: string
  name: string
  member_count: number
}

interface MembroEquipaResumo {
  user_id: string
}

const route = useRoute()
const api = useNuxtApp().$api
const config = useRuntimeConfig()
const apiBase = String(config.public.apiBase).replace(/\/+$/, '')
const auth = useAuth()

const utilizador = ref<Utilizador | null>(null)
const tarefas = ref<TarefaAssociada[]>([])
const projetos = ref<ProjetoResumo[]>([])
const equipas = ref<EquipaResumo[]>([])
const carregando = ref(true)
const carregarAssociacoes = ref(false)
const submetendo = ref(false)
const editar = ref(false)
const erro = ref('')
const erroAssociacoes = ref('')
const sucesso = ref('')
const nome = ref('')
const email = ref('')
let pedidoAtual = 0

function obterMensagemErro(error: unknown): string {
  const resposta = error as {
    data?: { detail?: string | { msg?: string }[] }
    message?: string
  }
  const detalhe = resposta?.data?.detail

  if (typeof detalhe === 'string') return detalhe
  if (Array.isArray(detalhe)) {
    return detalhe.map((item) => item.msg ?? 'Dados inválidos').join(' ')
  }
  return resposta?.message ?? 'Ocorreu um erro ao comunicar com a API.'
}

function formatarData(data: string): string {
  const valor = new Date(data)
  if (Number.isNaN(valor.getTime())) return 'Data indisponível'
  return new Intl.DateTimeFormat('pt-PT', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(valor)
}

function obterIniciais(valor: string): string {
  return valor
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((parte) => parte.charAt(0).toUpperCase())
    .join('')
}

function obterUrlFotografia(avatarUrl: string | null): string {
  return obterUrlAvatar(avatarUrl, apiBase)
}

function rotuloEstado(estado: TarefaAssociada['status']): string {
  const rotulos: Record<TarefaAssociada['status'], string> = {
    to_do: 'Por fazer',
    in_progress: 'Em curso',
    completed: 'Concluída',
    blocked: 'Bloqueada',
  }
  return rotulos[estado]
}

function rotuloPrioridade(prioridade: TarefaAssociada['priority']): string {
  const rotulos: Record<TarefaAssociada['priority'], string> = {
    low: 'Baixa',
    medium: 'Média',
    high: 'Alta',
  }
  return rotulos[prioridade]
}

function nomeProjeto(projectId: string): string {
  return projetos.value.find((projeto) => projeto.id === projectId)?.name
    ?? `Projeto #${projectId}`
}

async function carregarPerfil(userId: string): Promise<void> {
  const pedido = ++pedidoAtual
  carregando.value = true
  carregarAssociacoes.value = false
  erro.value = ''
  erroAssociacoes.value = ''
  sucesso.value = ''
  editar.value = false
  utilizador.value = null
  tarefas.value = []
  projetos.value = []
  equipas.value = []

  if (!userId) {
    erro.value = 'O identificador do utilizador é inválido.'
    carregando.value = false
    return
  }

  try {
    const utilizadores = await fetchAllPages<Utilizador>('/users/')
    if (pedido !== pedidoAtual) return

    const encontrado = utilizadores.find((item) => item.id === userId)
    if (!encontrado) {
      erro.value = 'Utilizador não encontrado.'
      return
    }

    utilizador.value = encontrado
    nome.value = encontrado.name
    email.value = encontrado.email
    carregarAssociacoes.value = true

    try {
      const [tarefasDoUtilizador, projetosVisiveis, equipasVisiveis] = await Promise.all([
        fetchAllPages<TarefaAssociada>(`/tasks/?assigned_to=${userId}`),
        fetchAllPages<ProjetoResumo>('/projects/'),
        fetchAllPages<EquipaResumo>('/teams/'),
      ])
      const equipasDoUtilizador = await Promise.all(
        equipasVisiveis.map(async (equipa) => {
          const membros = await fetchAllPages<MembroEquipaResumo>(
            `/teams/${equipa.id}/members`,
          )
          return membros.some((membro) => membro.user_id === userId)
            ? equipa
            : null
        }),
      )

      if (pedido !== pedidoAtual) return
      tarefas.value = tarefasDoUtilizador
      projetos.value = projetosVisiveis
      equipas.value = equipasDoUtilizador.filter(
        (equipa): equipa is EquipaResumo => equipa !== null,
      )
    } catch (error) {
      console.error('Erro ao carregar tarefas e equipas do utilizador:', error)
      if (pedido === pedidoAtual) erroAssociacoes.value = obterMensagemErro(error)
    } finally {
      if (pedido === pedidoAtual) carregarAssociacoes.value = false
    }
  } catch (error) {
    console.error('Erro ao carregar perfil do utilizador:', error)
    if (pedido === pedidoAtual) erro.value = obterMensagemErro(error)
  } finally {
    if (pedido === pedidoAtual) carregando.value = false
  }
}

async function guardarPerfil(): Promise<void> {
  if (!utilizador.value) return
  erro.value = ''
  sucesso.value = ''

  if (nome.value.trim().length < 2) {
    erro.value = 'O nome deve ter pelo menos 2 caracteres.'
    return
  }
  if (!email.value.trim()) {
    erro.value = 'Introduza um endereço de email.'
    return
  }

  submetendo.value = true
  try {
    const atualizado = await api<Utilizador>(`/users/${utilizador.value.id}`, {
      method: 'PATCH',
      body: {
        name: nome.value.trim(),
        email: email.value.trim().toLowerCase(),
      },
    })
    utilizador.value = atualizado
    nome.value = atualizado.name
    email.value = atualizado.email
    if (auth.user.value?.id === atualizado.id) {
      auth.user.value.name = atualizado.name
      auth.user.value.email = atualizado.email
    }
    editar.value = false
    sucesso.value = 'Perfil atualizado com sucesso.'
  } catch (error) {
    console.error('Erro ao atualizar perfil do utilizador:', error)
    erro.value = obterMensagemErro(error)
  } finally {
    submetendo.value = false
  }
}

function cancelarEdicao(): void {
  if (!utilizador.value) return
  nome.value = utilizador.value.name
  email.value = utilizador.value.email
  editar.value = false
  erro.value = ''
}

watch(
  () => route.params.id,
  (id) => {
    const valor = Array.isArray(id) ? id[0] : id
    void carregarPerfil(valor ?? '')
  },
)

onMounted(() => {
  const id = Array.isArray(route.params.id) ? route.params.id[0] : route.params.id
  void carregarPerfil(id ?? '')
})
</script>

<template>
  <div class="user-detail-page">
    <NuxtLink class="back-link" to="/users">← Voltar aos utilizadores</NuxtLink>

    <div v-if="carregando" class="page-state">
      <span class="loader"></span>
      A carregar perfil...
    </div>
    <div v-else-if="erro && !utilizador" class="page-message error-message" role="alert">
      {{ erro }}
    </div>

    <template v-else-if="utilizador">
      <header class="page-heading">
        <div>
          <span class="eyebrow">GESTÃO DA PLATAFORMA · PERFIL</span>
          <h1>{{ utilizador.name }}</h1>
          <p>Dados da conta, tarefas atribuídas e equipas.</p>
        </div>
        <button
          v-if="!editar"
          class="primary-button"
          type="button"
          @click="editar = true; erro = ''; sucesso = ''"
        >
          Editar perfil
        </button>
      </header>

      <div v-if="erro" class="page-message error-message" role="alert">{{ erro }}</div>
      <div v-if="sucesso" class="page-message success-message" role="status">{{ sucesso }}</div>

      <section class="profile-card">
        <div class="profile-identity">
          <div class="user-avatar">
            <img
              v-if="utilizador.avatar_url"
              :src="obterUrlFotografia(utilizador.avatar_url)"
              :alt="`Fotografia de ${utilizador.name}`"
            />
            <span v-else>{{ obterIniciais(utilizador.name) }}</span>
          </div>
          <div class="identity-copy">
            <strong>{{ utilizador.name }}</strong>
            <span>{{ utilizador.email }}</span>
          </div>
          <span class="status-badge" :class="utilizador.is_active ? 'status-active' : 'status-inactive'">
            <span></span>{{ utilizador.is_active ? 'Ativo' : 'Inativo' }}
          </span>
        </div>

        <form v-if="editar" class="profile-form" @submit.prevent="guardarPerfil">
          <label>
            Nome completo
            <input v-model="nome" type="text" minlength="2" maxlength="100" required />
          </label>
          <label>
            Endereço de email
            <input v-model="email" type="email" maxlength="254" required />
          </label>
          <div class="form-actions">
            <button class="secondary-button" type="button" :disabled="submetendo" @click="cancelarEdicao">
              Cancelar
            </button>
            <button class="primary-button" type="submit" :disabled="submetendo">
              {{ submetendo ? 'A guardar...' : 'Guardar alterações' }}
            </button>
          </div>
        </form>

        <dl v-else class="profile-details">
          <div><dt>Perfil</dt><dd>{{ utilizador.role === 'admin' ? 'Administrador' : 'Utilizador · front-office' }}</dd></div>
          <div><dt>Data de registo</dt><dd>{{ formatarData(utilizador.created_at) }}</dd></div>
          <div><dt>Fotografia</dt><dd>{{ utilizador.avatar_url ? 'Configurada' : 'Sem fotografia' }}</dd></div>
        </dl>
      </section>

      <section class="associations-section">
        <header class="section-heading">
          <div>
            <span class="eyebrow">ATIVIDADE</span>
            <h2>Trabalho e equipa</h2>
            <p>Tarefas atribuídas e equipas a que pertence.</p>
          </div>
          <span class="association-count">{{ tarefas.length }} tarefas · {{ equipas.length }} equipas</span>
        </header>

        <div v-if="carregarAssociacoes" class="page-state">
          <span class="loader"></span>
          A carregar tarefas e equipas...
        </div>
        <div v-else-if="erroAssociacoes" class="page-message error-message" role="alert">
          <span>{{ erroAssociacoes }}</span>
          <button class="secondary-button" type="button" @click="carregarPerfil(utilizador.id)">
            Tentar novamente
          </button>
        </div>
        <div v-else class="association-columns">
          <section class="association-group">
            <h3>Equipas</h3>
            <div v-if="equipas.length" class="association-list">
              <article v-for="equipa in equipas" :key="equipa.id" class="association-card">
                <span class="association-icon">♧</span>
                <span class="association-copy">
                  <strong>{{ equipa.name }}</strong>
                  <small>{{ equipa.member_count }} membros</small>
                </span>
              </article>
            </div>
            <p v-else class="empty-note">Este utilizador ainda não pertence a uma equipa.</p>
          </section>

          <section class="association-group">
            <h3>Tarefas atribuídas</h3>
            <div v-if="tarefas.length" class="association-list">
              <article v-for="tarefa in tarefas" :key="tarefa.id" class="association-card">
                <span class="association-icon task-icon">✓</span>
                <span class="association-copy">
                  <strong>{{ tarefa.title }}</strong>
                  <small>
                    {{ nomeProjeto(tarefa.project_id) }} · {{ rotuloEstado(tarefa.status) }} ·
                    Prioridade {{ rotuloPrioridade(tarefa.priority).toLowerCase() }}
                  </small>
                </span>
                <span v-if="tarefa.due_date" class="task-due-date">{{ formatarData(tarefa.due_date) }}</span>
              </article>
            </div>
            <p v-else class="empty-note">Este utilizador não tem tarefas atribuídas.</p>
          </section>
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.user-detail-page { display: grid; max-width: 1200px; gap: 20px; margin: 0 auto; color: #172b4d; }
.back-link { width: fit-content; color: #536da5; font-size: 12px; font-weight: 700; text-decoration: none; }
.back-link:hover { color: #344f8a; text-decoration: underline; }
.page-heading, .section-heading { display: flex; align-items: center; justify-content: space-between; gap: 16px; }
.eyebrow { color: #7185aa; font-size: 10px; font-weight: 800; letter-spacing: .12em; }
.page-heading h1, .section-heading h2 { margin: 7px 0; color: #263957; font-size: 25px; font-weight: 800; letter-spacing: -.04em; }
.page-heading p, .section-heading p { margin: 0; color: #8795aa; font-size: 12px; }
.profile-card, .associations-section { padding: 21px; background: #fff; border: 1px solid #e5ebf4; border-radius: 13px; box-shadow: 0 3px 12px rgb(30 55 90 / 3%); }
.profile-identity { display: flex; align-items: center; gap: 14px; padding: 4px 2px 18px; border-bottom: 1px solid #edf0f5; }
.user-avatar { display: grid; width: 54px; height: 54px; flex: 0 0 54px; overflow: hidden; place-items: center; color: #4164dc; background: #edf1ff; border-radius: 50%; font-size: 15px; font-weight: 800; }
.user-avatar img { width: 100%; height: 100%; object-fit: cover; }
.identity-copy { display: grid; min-width: 0; flex: 1; gap: 5px; }
.identity-copy strong { overflow: hidden; color: #263957; font-size: 15px; text-overflow: ellipsis; }
.identity-copy > span { overflow-wrap: anywhere; color: #8795aa; font-size: 11px; }
.status-badge { display: inline-flex; align-items: center; gap: 6px; padding: 5px 8px; border-radius: 999px; font-size: 10px; font-weight: 700; }
.status-badge > span { width: 6px; height: 6px; border-radius: 50%; }
.status-active { color: #16865c; background: #e8f7ef; }
.status-active > span { background: #20a36c; }
.status-inactive { color: #a36d20; background: #fff5e5; }
.status-inactive > span { background: #d89a36; }
.profile-details { display: flex; flex-wrap: wrap; gap: 28px; margin: 18px 0 0; }
.profile-details > div { display: grid; gap: 5px; }
.profile-details dt { color: #8795aa; font-size: 10px; font-weight: 700; }
.profile-details dd { margin: 0; color: #263957; font-size: 12px; }
.profile-form { display: grid; max-width: 540px; gap: 14px; padding-top: 18px; }
.profile-form label { display: grid; gap: 6px; color: #53657f; font-size: 11px; font-weight: 700; }
.profile-form input { min-height: 40px; padding: 0 11px; color: #263957; background: #fff; border: 1px solid #dce4ef; border-radius: 8px; font: inherit; }
.form-actions { display: flex; justify-content: flex-end; gap: 9px; margin-top: 5px; }
.primary-button, .secondary-button { display: inline-flex; min-height: 39px; align-items: center; justify-content: center; padding: 0 14px; border-radius: 8px; font-size: 11px; font-weight: 700; cursor: pointer; }
.primary-button { color: #fff; background: linear-gradient(135deg, var(--tf-primary), var(--tf-primary-hover)); border: 1px solid var(--tf-primary-hover); }
.secondary-button { color: #53657f; background: #fff; border: 1px solid #dce4ef; }
.primary-button:disabled, .secondary-button:disabled { opacity: .6; cursor: not-allowed; }
.associations-section { display: grid; gap: 20px; }
.association-count { flex: 0 0 auto; padding: 7px 9px; color: #53657f; background: #f3f6fb; border-radius: 7px; font-size: 10px; font-weight: 700; }
.association-columns { display: grid; grid-template-columns: minmax(0, .8fr) minmax(0, 1.5fr); gap: 24px; }
.association-group { display: grid; align-content: start; gap: 10px; }
.association-group h3 { margin: 0; color: #7185aa; font-size: 10px; font-weight: 800; letter-spacing: .06em; text-transform: uppercase; }
.association-list { display: grid; gap: 7px; }
.association-card { display: flex; min-width: 0; align-items: center; gap: 10px; padding: 10px; background: #fbfcfe; border: 1px solid #e8edf5; border-radius: 9px; }
.association-icon { display: grid; width: 30px; height: 30px; flex: 0 0 30px; place-items: center; color: #4164dc; background: #edf1ff; border-radius: 8px; font-size: 15px; }
.task-icon { color: #16865c; background: #e8f7ef; }
.association-copy { display: grid; min-width: 0; flex: 1; gap: 4px; }
.association-copy strong, .association-copy small { overflow: hidden; text-overflow: ellipsis; }
.association-copy strong { color: #263957; font-size: 11px; }
.association-copy small { color: #8795aa; font-size: 9px; white-space: normal; }
.task-due-date { flex: 0 0 auto; color: #7185aa; font-size: 9px; }
.empty-note { margin: 0; color: #8795aa; font-size: 11px; }
.page-state { display: flex; min-height: 110px; align-items: center; justify-content: center; gap: 10px; color: #8795aa; font-size: 12px; }
.loader { width: 20px; height: 20px; border: 3px solid #e2e8f0; border-top-color: #536dd2; border-radius: 50%; animation: spin .8s linear infinite; }
.page-message { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 12px; border: 1px solid; border-radius: 8px; font-size: 11px; }
.error-message { color: #b42318; background: #fff0ef; border-color: #f7d2ce; }
.success-message { color: #16865c; background: #eaf8f0; border-color: #c8ebd7; }
@keyframes spin { to { transform: rotate(360deg); } }
@media (max-width: 700px) {
  .page-heading, .section-heading { align-items: flex-start; flex-direction: column; }
  .association-columns { grid-template-columns: 1fr; gap: 20px; }
  .profile-identity { flex-wrap: wrap; }
  .association-card { align-items: flex-start; }
  .task-due-date { align-self: center; }
}
</style>
