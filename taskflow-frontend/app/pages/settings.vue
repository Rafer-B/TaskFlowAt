<script setup lang="ts">
import { scrollToPanel } from '~/composables/usePanelScroll'
import { computed, onMounted, ref, watch } from 'vue'

import type { AuthUser } from '~/composables/useAuth'
import {
  INTERFACE_PREFERENCES_KEY,
  aplicarAparencia,
  isThemeId,
  themes,
  type InterfacePreferences,
  type ThemeId,
} from '~/utils/interfacePreferences'

// Preferências locais e operações da conta usam fluxos separados e mensagens comuns.
definePageMeta({
  layout: 'admin',
})

const auth = useAuth()
const route = useRoute()
const api = useNuxtApp().$api
const config = useRuntimeConfig()
const apiBase = String(config.public.apiBase).replace(/\/+$/, '')
const preferences = ref<InterfacePreferences>({
  theme: 'calm',
  reducedMotion: false,
})
const fotografiaAEnviar = ref(false)
const fotografiaARemover = ref(false)
const perfilAAtualizar = ref(false)
const mostrarEdicaoPerfil = ref(false)
const palavraPasseAAtualizar = ref(false)
const mostrarFormularioPalavraPasse = ref(false)
const formularioPalavraPasseRef = ref<HTMLElement | null>(null)

async function alternarFormularioPalavraPasse(): Promise<void> {
  mostrarFormularioPalavraPasse.value = !mostrarFormularioPalavraPasse.value
  if (mostrarFormularioPalavraPasse.value) {
    await scrollToPanel(formularioPalavraPasseRef)
  }
}
const erro = ref('')
const sucesso = ref('')
const confirmarRemocaoFotografia = ref(false)
const avatarFalhou = ref(false)
const palavrasPasse = ref({
  atual: '',
  nova: '',
  confirmar: '',
})
const formularioPerfil = ref({
  name: '',
  email: '',
})

const utilizador = computed(() => auth.user.value)
const temaSelecionado = computed(() =>
  themes.find((theme) => theme.id === preferences.value.theme) ?? themes[0],
)
const avatarUrl = computed(() => {
  return obterUrlAvatar(utilizador.value?.avatar_url, apiBase)
})
watch(avatarUrl, () => {
  avatarFalhou.value = false
})
watch(
  () => route.query.editProfile,
  (value) => {
    if (value === '1') editarPerfil()
  },
)
const iniciais = computed(() =>
  utilizador.value?.name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part.charAt(0).toUpperCase())
    .join('') ?? 'U',
)

function aplicarPreferencias(): void {
  aplicarAparencia(preferences.value)
}

function guardarPreferencias(): void {
  erro.value = ''
  sucesso.value = ''
  aplicarPreferencias()

  try {
    localStorage.setItem(
      INTERFACE_PREFERENCES_KEY,
      JSON.stringify(preferences.value),
    )
    sucesso.value = 'Preferências guardadas neste navegador.'
  } catch (error) {
    console.error('Não foi possível guardar as preferências:', error)
    erro.value = 'As preferências foram aplicadas, mas não puderam ser guardadas neste navegador.'
  }
}

function carregarPreferencias(): void {
  try {
    // Valida cada campo persistido para ignorar valores antigos ou dados malformados.
    const stored = localStorage.getItem(INTERFACE_PREFERENCES_KEY)
    if (stored) {
      const parsed: unknown = JSON.parse(stored)
      if (typeof parsed === 'object' && parsed !== null) {
        if ('theme' in parsed && isThemeId(parsed.theme)) {
          preferences.value.theme = parsed.theme
        }
        if (
          'reducedMotion' in parsed &&
          typeof parsed.reducedMotion === 'boolean'
        ) {
          preferences.value.reducedMotion = parsed.reducedMotion
        }
      }
    }
  } catch (error) {
    console.error('Não foi possível carregar as preferências:', error)
    erro.value = 'Não foi possível carregar as preferências guardadas. Pode selecionar novas opções.'
  }

  aplicarPreferencias()
}

function obterMensagemErro(error: unknown): string {
  if (typeof error === 'object' && error !== null && 'data' in error) {
    const data = error.data
    if (
      typeof data === 'object' &&
      data !== null &&
      'detail' in data &&
      typeof data.detail === 'string'
    ) {
      return data.detail
    }
  }

  if (error instanceof Error) return error.message
  return 'Ocorreu um erro ao comunicar com a API.'
}

function editarPerfil(): void {
  if (!utilizador.value) return
  formularioPerfil.value = {
    name: utilizador.value.name,
    email: utilizador.value.email,
  }
  erro.value = ''
  sucesso.value = ''
  mostrarEdicaoPerfil.value = true
}

async function guardarPerfil(): Promise<void> {
  if (!utilizador.value || perfilAAtualizar.value) return
  erro.value = ''
  sucesso.value = ''
  perfilAAtualizar.value = true

  try {
    // A resposta canónica substitui a sessão local, incluindo alterações no nome ou email.
    const updatedUser = await api<AuthUser>('/users/me/profile', {
      method: 'PATCH',
      body: {
        name: formularioPerfil.value.name.trim(),
        email: formularioPerfil.value.email.trim(),
      },
    })
    auth.user.value = updatedUser
    formularioPerfil.value = {
      name: updatedUser.name,
      email: updatedUser.email,
    }
    mostrarEdicaoPerfil.value = false
    sucesso.value = 'Perfil atualizado com sucesso.'
  } catch (error) {
    console.error('Erro ao atualizar o próprio perfil:', error)
    erro.value = obterMensagemErro(error)
  } finally {
    perfilAAtualizar.value = false
  }
}

async function carregarFotografia(event: Event): Promise<void> {
  erro.value = ''
  sucesso.value = ''

  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file || !utilizador.value) return

  // Limita formatos e tamanho antes de enviar o ficheiro em multipart/form-data.
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
    erro.value = 'Formato inválido. Escolha uma imagem JPG, PNG ou WEBP.'
    input.value = ''
    return
  }

  if (file.size > 5 * 1024 * 1024) {
    erro.value = 'A fotografia não pode ultrapassar 5 MB.'
    input.value = ''
    return
  }

  const form = new FormData()
  form.append('file', file)
  fotografiaAEnviar.value = true

  try {
    const updatedUser = await api<AuthUser>(
      `/users/${utilizador.value.id}/avatar`,
      { method: 'POST', body: form },
    )
    auth.user.value = updatedUser
    sucesso.value = 'Fotografia de perfil atualizada com sucesso.'
  } catch (error) {
    console.error('Erro ao atualizar fotografia de perfil:', error)
    erro.value = obterMensagemErro(error)
  } finally {
    fotografiaAEnviar.value = false
    input.value = ''
  }
}

async function removerFotografia(): Promise<void> {
  if (!utilizador.value?.avatar_url || fotografiaARemover.value) return
  if (!confirmarRemocaoFotografia.value) {
    confirmarRemocaoFotografia.value = true
    return
  }

  erro.value = ''
  sucesso.value = ''
  fotografiaARemover.value = true

  try {
    const updatedUser = await api<AuthUser>('/users/me/avatar', {
      method: 'DELETE',
    })
    auth.user.value = updatedUser
    confirmarRemocaoFotografia.value = false
    sucesso.value = 'Fotografia de perfil removida com sucesso.'
  } catch (error) {
    console.error('Erro ao remover fotografia de perfil:', error)
    erro.value = obterMensagemErro(error)
  } finally {
    fotografiaARemover.value = false
  }
}

function cancelarRemocaoFotografia(): void {
  confirmarRemocaoFotografia.value = false
}

async function atualizarPalavraPasse(): Promise<void> {
  erro.value = ''
  sucesso.value = ''

  // Confirmação local evita atualizar a conta com uma palavra-passe digitada incorretamente.
  if (palavrasPasse.value.nova !== palavrasPasse.value.confirmar) {
    erro.value = 'A nova palavra-passe e a confirmação não coincidem.'
    return
  }

  palavraPasseAAtualizar.value = true

  try {
    await api<AuthUser>('/users/me/password', {
      method: 'PATCH',
      body: {
        current_password: palavrasPasse.value.atual,
        new_password: palavrasPasse.value.nova,
      },
    })
    palavrasPasse.value = { atual: '', nova: '', confirmar: '' }
    sucesso.value = 'Palavra-passe atualizada com sucesso.'
    mostrarFormularioPalavraPasse.value = false
  } catch (error) {
    console.error('Erro ao atualizar palavra-passe:', error)
    erro.value = obterMensagemErro(error)
  } finally {
    palavraPasseAAtualizar.value = false
  }
}

function formatarData(data: string | undefined): string {
  if (!data) return 'Indisponível'
  const parsed = new Date(data)
  if (Number.isNaN(parsed.getTime())) return 'Indisponível'

  return new Intl.DateTimeFormat('pt-PT', {
    day: '2-digit',
    month: 'long',
    year: 'numeric',
  }).format(parsed)
}

onMounted(() => {
  carregarPreferencias()
  if (route.query.editProfile === '1') editarPerfil()
})
</script>

<template>
  <main class="settings-page">
    <header class="page-hero settings-hero">
      <div class="hero-kicker">
        <span class="dot" aria-hidden="true"></span>
        TaskFlow <span class="hero-separator">/</span> Configuração
      </div>
      <h1>Definições</h1>
      <p>Personalize a sua conta e a forma como utiliza o TaskFlow.</p>
    </header>

    <p v-if="erro" class="settings-message settings-error" role="alert">
      {{ erro }}
    </p>
    <p v-if="sucesso" class="settings-message settings-success" role="status">
      {{ sucesso }}
    </p>

    <section class="settings-section" aria-labelledby="account-heading">
      <div class="settings-section-heading">
        <h2 id="account-heading">A minha conta</h2>
        <p>Consulte os seus dados e faça a gestão da fotografia de perfil.</p>
      </div>

      <article class="content-card account-card">
        <label
          class="account-avatar-picker"
          title="Clique para alterar a fotografia"
        >
          <div class="account-avatar">
            <img
              v-if="avatarUrl && !avatarFalhou"
              :src="avatarUrl"
              :alt="`Fotografia de ${utilizador?.name ?? 'perfil'}`"
              @error="avatarFalhou = true"
            />
            <span v-else>{{ iniciais }}</span>
          </div>
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp"
            aria-label="Alterar fotografia de perfil"
            :disabled="fotografiaAEnviar || fotografiaARemover || !utilizador"
            @change="carregarFotografia"
          />
        </label>

        <div class="account-details">
          <h3>{{ utilizador?.name ?? 'Utilizador' }}</h3>
          <p>{{ utilizador?.email ?? 'Email indisponível' }}</p>
          <div class="account-tags">
            <span>{{ utilizador?.role === 'admin' ? 'Administrador' : 'Membro' }}</span>
            <span :class="{ 'account-inactive': !utilizador?.is_active }">
              {{ utilizador?.is_active ? 'Conta ativa' : 'Conta inativa' }}
            </span>
          </div>
        </div>

        <div class="avatar-actions">
          <button
            v-if="!mostrarEdicaoPerfil"
            type="button"
            class="btn btn-outline"
            @click="editarPerfil"
          >
            Editar perfil
          </button>
          <button
            v-else
            type="button"
            class="btn btn-outline"
            :disabled="perfilAAtualizar"
            @click="mostrarEdicaoPerfil = false"
          >
            Cancelar edição
          </button>
          <label class="btn btn-outline avatar-upload" :class="{ uploading: fotografiaAEnviar }">
            {{ fotografiaAEnviar ? 'A carregar...' : 'Alterar fotografia' }}
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp"
              :disabled="fotografiaAEnviar || fotografiaARemover || !utilizador"
              @change="carregarFotografia"
            />
          </label>
          <button
            v-if="utilizador?.avatar_url"
            type="button"
            class="remove-avatar-button"
            :disabled="fotografiaAEnviar || fotografiaARemover"
            @click="removerFotografia"
          >
            {{ fotografiaARemover ? 'A remover...' : 'Remover fotografia' }}
          </button>
          <div v-if="confirmarRemocaoFotografia" class="inline-confirm" role="group" aria-label="Confirmar remoção da fotografia">
            <span>Remover a fotografia de perfil?</span>
            <button type="button" class="remove-avatar-button" :disabled="fotografiaARemover" @click="removerFotografia">Confirmar</button>
            <button type="button" class="btn btn-outline" :disabled="fotografiaARemover" @click="cancelarRemocaoFotografia">Cancelar</button>
          </div>
        </div>

        <form
          v-if="mostrarEdicaoPerfil"
          class="profile-edit-form"
          @submit.prevent="guardarPerfil"
        >
          <label>
            <span>Nome completo</span>
            <input
              v-model="formularioPerfil.name"
              type="text"
              name="profile-name"
              autocomplete="name"
              minlength="2"
              maxlength="100"
              required
              :disabled="perfilAAtualizar"
            />
          </label>
          <label>
            <span>Endereço de email</span>
            <input
              v-model="formularioPerfil.email"
              type="email"
              name="profile-email"
              autocomplete="email"
              required
              :disabled="perfilAAtualizar"
            />
          </label>
          <button
            type="submit"
            class="btn btn-primary"
            :disabled="perfilAAtualizar"
          >
            {{ perfilAAtualizar ? 'A guardar...' : 'Guardar perfil' }}
          </button>
        </form>

        <dl class="account-meta">
          <div>
            <dt>Identificador</dt>
            <dd>{{ utilizador ? `#${utilizador.id}` : 'Indisponível' }}</dd>
          </div>
          <div>
            <dt>Conta criada</dt>
            <dd>{{ formatarData(utilizador?.created_at) }}</dd>
          </div>
        </dl>
      </article>
    </section>

    <section class="settings-section" aria-labelledby="password-heading">
      <div class="settings-section-heading password-section-heading">
        <div>
          <h2 id="password-heading">Alterar palavra-passe</h2>
          <p>Por segurança, confirme a palavra-passe atual antes de escolher uma nova.</p>
        </div>
        <button
          type="button"
          class="btn btn-outline"
          :aria-expanded="mostrarFormularioPalavraPasse"
          aria-controls="password-form"
          @click="alternarFormularioPalavraPasse"
        >
          {{ mostrarFormularioPalavraPasse ? 'Cancelar' : 'Alterar palavra-passe' }}
        </button>
      </div>

      <form
        v-if="mostrarFormularioPalavraPasse"
        ref="formularioPalavraPasseRef"
        id="password-form"
        class="content-card password-card"
        @submit.prevent="atualizarPalavraPasse"
      >
        <label>
          <span>Palavra-passe atual</span>
          <input
            v-model="palavrasPasse.atual"
            type="password"
            name="current-password"
            autocomplete="current-password"
            required
            maxlength="128"
            :disabled="palavraPasseAAtualizar"
          />
        </label>
        <label>
          <span>Nova palavra-passe</span>
          <input
            v-model="palavrasPasse.nova"
            type="password"
            name="new-password"
            autocomplete="new-password"
            required
            minlength="8"
            maxlength="128"
            :disabled="palavraPasseAAtualizar"
          />
          <small>Utilize pelo menos 8 caracteres.</small>
        </label>
        <label>
          <span>Confirmar nova palavra-passe</span>
          <input
            v-model="palavrasPasse.confirmar"
            type="password"
            name="confirm-password"
            autocomplete="new-password"
            required
            minlength="8"
            maxlength="128"
            :disabled="palavraPasseAAtualizar"
          />
        </label>
        <button
          type="submit"
          class="btn btn-primary password-submit"
          :disabled="palavraPasseAAtualizar"
        >
          {{ palavraPasseAAtualizar ? 'A atualizar...' : 'Atualizar palavra-passe' }}
        </button>
      </form>
    </section>

    <section class="settings-section" aria-labelledby="appearance-heading">
      <div class="settings-section-heading">
        <h2 id="appearance-heading">Aparência e acessibilidade</h2>
        <p>Estas preferências são guardadas apenas neste navegador.</p>
      </div>

      <article class="content-card appearance-card">
        <fieldset class="theme-fieldset">
          <legend>Fundo do sistema</legend>
          <p class="settings-help">
            Escolha um fundo suave e superfícies menos brancas para reduzir o brilho.
          </p>

          <div class="theme-options">
            <label
              v-for="theme in themes"
              :key="theme.id"
              class="theme-option"
              :class="{ 'theme-option-selected': preferences.theme === theme.id }"
            >
              <input
                v-model="preferences.theme"
                type="radio"
                name="theme"
                :value="theme.id"
                @change="guardarPreferencias"
              />
              <span
                class="theme-preview"
                :style="{
                  '--preview-color': theme.background,
                  '--preview-surface': theme.surface,
                }"
                aria-hidden="true"
              >
                <i></i><i></i><i></i>
              </span>
              <span class="theme-copy">
                <strong>{{ theme.name }}</strong>
                <small>{{ theme.description }}</small>
              </span>
              <span class="theme-selected-mark" aria-hidden="true">
                {{ preferences.theme === theme.id ? '✓' : '' }}
              </span>
            </label>
          </div>
        </fieldset>

        <div class="motion-setting">
          <div>
            <strong>Reduzir animações</strong>
            <p class="settings-help">
              Reduz transições e movimentos na interface para uma navegação
              mais confortável.
            </p>
          </div>
          <label class="switch">
            <input
              v-model="preferences.reducedMotion"
              type="checkbox"
              @change="guardarPreferencias"
            />
            <span class="switch-track" aria-hidden="true"></span>
            <span class="sr-only">Reduzir animações</span>
          </label>
        </div>
        <p class="current-theme">
          Fundo selecionado: <strong>{{ temaSelecionado?.name ?? 'Padrão' }}</strong>
        </p>
      </article>
    </section>
  </main>
</template>

<style scoped>
.settings-page {
  width: min(1120px, 100%);
  margin: 0 auto;
  padding: 16px 4px 40px;
}

.settings-hero {
  margin-bottom: 24px;
}

.settings-section {
  margin-top: 24px;
}

.settings-section-heading {
  margin: 0 0 12px 2px;
}

.settings-section-heading h2 {
  margin: 0 0 5px;
  color: var(--tf-text);
  font-size: 17px;
}

.settings-section-heading p,
.settings-help {
  margin: 0;
  color: var(--tf-text-muted);
  font-size: 13px;
  line-height: 1.55;
}

.account-card {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 18px;
  padding: 24px;
}

.account-avatar {
  display: grid;
  width: 76px;
  height: 76px;
  overflow: hidden;
  place-items: center;
  color: #505bd0;
  background: #eef0ff;
  border-radius: 50%;
  font-size: 22px;
  font-weight: 750;
}

.account-avatar-picker {
  position: relative;
  display: block;
  width: 76px;
  height: 76px;
  border-radius: 50%;
  cursor: pointer;
}

.account-avatar-picker input {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
}

.account-avatar-picker input:focus-visible {
  outline: 2px solid var(--tf-primary);
  outline-offset: 3px;
  border-radius: 50%;
}

.account-avatar-picker input:disabled {
  cursor: wait;
}

.account-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.account-details h3 {
  margin: 0 0 5px;
  color: var(--tf-text);
  font-size: 16px;
}

.account-details {
  display: block;
  min-width: 0;
  padding: 0;
  text-align: left;
  background: transparent;
  border: 0;
  border-radius: 8px;
}

.account-details > p {
  margin: 0;
  color: var(--tf-text-muted);
  font-size: 13px;
}

.account-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  margin-top: 10px;
}

.account-tags span {
  padding: 4px 9px;
  color: var(--tf-primary);
  background: var(--tf-primary-soft);
  border-radius: 999px;
  font-size: 11px;
  font-weight: 650;
}

.account-tags .account-inactive {
  color: var(--tf-danger);
  background: var(--tf-danger-soft);
}

.profile-edit-form {
  display: grid;
  grid-column: 1 / -1;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  align-items: end;
  gap: 14px;
  padding-top: 18px;
  border-top: 1px solid var(--tf-border);
}

.profile-edit-form label {
  display: grid;
  gap: 7px;
  color: var(--tf-text);
  font-size: 12px;
  font-weight: 650;
}

.profile-edit-form input {
  width: 100%;
  min-width: 0;
  padding: 10px 11px;
  color: var(--tf-text);
  background: #fff;
  border: 1px solid var(--tf-border);
  border-radius: 9px;
  font: inherit;
  font-weight: 400;
}

.profile-edit-form input:focus {
  border-color: var(--tf-primary);
  outline: 2px solid var(--tf-primary-soft);
}

.profile-edit-form button {
  justify-self: start;
}

.avatar-upload {
  position: relative;
  overflow: hidden;
  cursor: pointer;
  white-space: nowrap;
}

.avatar-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}

.remove-avatar-button {
  padding: 9px 12px;
  color: var(--tf-danger);
  background: var(--tf-danger-soft);
  border: 1px solid transparent;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 650;
  cursor: pointer;
}

.remove-avatar-button:hover:not(:disabled) {
  border-color: var(--tf-danger);
}

.remove-avatar-button:disabled {
  cursor: wait;
  opacity: 0.65;
}

.avatar-upload input {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
}

.avatar-upload:focus-within {
  outline: 2px solid var(--tf-primary);
  outline-offset: 3px;
}

.avatar-upload.uploading {
  cursor: wait;
  opacity: 0.7;
}

.account-meta {
  display: grid;
  grid-column: 1 / -1;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  margin: 4px 0 0;
  padding-top: 17px;
  border-top: 1px solid var(--tf-border);
}

.account-meta div {
  display: grid;
  gap: 5px;
}

.account-meta dt {
  color: var(--tf-text-muted);
  font-size: 11px;
  font-weight: 650;
}

.account-meta dd {
  margin: 0;
  color: var(--tf-text);
  font-size: 12px;
}

.appearance-card {
  padding: 24px;
}

.password-card {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  align-items: start;
  gap: 16px;
  padding: 24px;
  scroll-margin-top: 96px;
}

.password-section-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.password-section-heading .btn {
  flex: 0 0 auto;
}

.password-card > label {
  display: grid;
  gap: 7px;
  color: var(--tf-text);
  font-size: 12px;
  font-weight: 650;
}

.password-card input {
  width: 100%;
  min-width: 0;
  height: 40px;
  padding: 0 11px;
  color: var(--tf-text);
  background: var(--tf-surface);
  border: 1px solid var(--tf-border);
  border-radius: 9px;
  outline: none;
  font-size: 13px;
}

.password-card input:focus {
  border-color: var(--tf-primary);
  box-shadow: 0 0 0 3px var(--tf-primary-soft);
}

.password-card input:disabled {
  background: var(--tf-border-soft);
}

.password-card small {
  color: var(--tf-text-muted);
  font-size: 10px;
  font-weight: 400;
}

.password-submit {
  justify-self: start;
}

.theme-fieldset {
  min-width: 0;
  margin: 0;
  padding: 0;
  border: 0;
}

.theme-fieldset legend {
  margin-bottom: 5px;
  color: var(--tf-text);
  font-size: 14px;
  font-weight: 700;
}

.theme-options {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-top: 16px;
}

.theme-option {
  position: relative;
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 12px;
  min-width: 0;
  padding: 12px;
  border: 1px solid var(--tf-border);
  border-radius: 12px;
  cursor: pointer;
  transition: border-color var(--tf-transition), box-shadow var(--tf-transition);
}

.theme-option-selected {
  border-color: var(--tf-primary);
  box-shadow: 0 0 0 2px var(--tf-primary-soft);
}

.theme-option input {
  position: absolute;
  width: 1px;
  height: 1px;
  opacity: 0;
}

.theme-option:focus-within {
  outline: 2px solid var(--tf-primary);
  outline-offset: 2px;
}

.theme-preview {
  display: flex;
  grid-column: 1 / -1;
  align-items: flex-start;
  gap: 4px;
  height: 56px;
  padding: 8px;
  background: var(--preview-color);
  border: 1px solid var(--tf-border);
  border-radius: 8px;
}

.theme-preview i {
  width: 24%;
  height: 100%;
  background: var(--preview-surface);
  border: 1px solid rgb(100 116 139 / 12%);
  border-radius: 4px;
}

.theme-preview i:first-child {
  width: 18%;
}

.theme-preview i:last-child {
  width: 45%;
  height: 65%;
}

.theme-copy {
  display: grid;
  gap: 4px;
  min-width: 0;
}

.theme-copy strong {
  color: var(--tf-text);
  font-size: 12px;
}

.theme-copy small {
  color: var(--tf-text-muted);
  font-size: 10px;
  line-height: 1.45;
}

.theme-selected-mark {
  display: grid;
  width: 19px;
  height: 19px;
  place-items: center;
  color: #fff;
  background: var(--tf-primary);
  border-radius: 50%;
  font-size: 11px;
}

.motion-setting {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  margin-top: 22px;
  padding-top: 19px;
  border-top: 1px solid var(--tf-border);
}

.motion-setting strong {
  display: block;
  margin-bottom: 5px;
  color: var(--tf-text);
  font-size: 13px;
}

.switch {
  position: relative;
  display: inline-flex;
  flex: 0 0 auto;
  width: 44px;
  height: 25px;
  cursor: pointer;
}

.switch input {
  position: absolute;
  width: 1px;
  height: 1px;
  opacity: 0;
}

.switch-track {
  width: 100%;
  height: 100%;
  background: #cbd5e1;
  border-radius: 999px;
  transition: background var(--tf-transition);
}

.switch-track::after {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 19px;
  height: 19px;
  background: #fff;
  border-radius: 50%;
  content: '';
  transition: transform var(--tf-transition);
}

.switch input:checked + .switch-track {
  background: var(--tf-primary);
}

.switch input:checked + .switch-track::after {
  transform: translateX(19px);
}

.switch input:focus-visible + .switch-track {
  outline: 2px solid var(--tf-primary);
  outline-offset: 3px;
}

.current-theme {
  margin: 15px 0 0;
  color: var(--tf-text-muted);
  font-size: 11px;
}

.current-theme strong {
  color: var(--tf-text);
}

.settings-message {
  margin: 0 0 14px;
  padding: 12px 15px;
  border-radius: 10px;
  font-size: 13px;
}

.settings-error {
  color: var(--tf-danger);
  background: var(--tf-danger-soft);
}

.settings-success {
  color: var(--tf-success);
  background: var(--tf-success-soft);
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
}

@media (max-width: 720px) {
  .settings-page {
    padding: 8px 0 24px;
  }

  .account-card {
    grid-template-columns: auto minmax(0, 1fr);
    gap: 14px;
    padding: 18px;
  }

  .account-avatar {
    width: 60px;
    height: 60px;
  }

  .account-avatar-picker {
    width: 60px;
    height: 60px;
  }

  .avatar-upload {
    justify-self: start;
  }

  .avatar-actions {
    grid-column: 1 / -1;
    justify-content: flex-start;
  }

  .profile-edit-form {
    grid-template-columns: 1fr;
  }

  .theme-options {
    grid-template-columns: 1fr;
  }

  .theme-option {
    grid-template-columns: 90px minmax(0, 1fr) auto;
    align-items: center;
  }

  .theme-preview {
    grid-column: auto;
  }

  .account-meta {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .appearance-card {
    padding: 18px;
  }

  .password-card {
    grid-template-columns: 1fr;
    padding: 18px;
  }

  .password-section-heading {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
