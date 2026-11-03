
<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import type { AuthUser } from '~/composables/useAuth'

const route = useRoute()
const auth = useAuth()
const config = useRuntimeConfig()
const apiBase = String(config.public.apiBase)
const api = useNuxtApp().$api
const avatarUrl = computed(() =>
  obterUrlAvatar(auth.user.value?.avatar_url, apiBase),
)
const avatarFalhou = ref(false)
const fotografiaAEnviar = ref(false)
const mensagemFotografia = ref('')
const erroFotografia = ref(false)

watch(avatarUrl, () => {
  avatarFalhou.value = false
})

defineProps<{
  title: string
}>()

const emit = defineEmits<{
  toggleSidebar: []
}>()

const searchQuery = ref('')

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

async function carregarFotografia(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  mensagemFotografia.value = ''

  if (!file || !auth.user.value) return

  if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
    erroFotografia.value = true
    mensagemFotografia.value = 'Escolha uma imagem JPG, PNG ou WEBP.'
    input.value = ''
    return
  }

  if (file.size > 5 * 1024 * 1024) {
    erroFotografia.value = true
    mensagemFotografia.value = 'A fotografia não pode ultrapassar 5 MB.'
    input.value = ''
    return
  }

  const form = new FormData()
  form.append('file', file)
  fotografiaAEnviar.value = true

  try {
    const updatedUser = await api<AuthUser>(
      `/users/${auth.user.value.id}/avatar`,
      { method: 'POST', body: form },
    )
    auth.user.value = updatedUser
    erroFotografia.value = false
    mensagemFotografia.value = 'Fotografia atualizada.'
  } catch (error) {
    console.error('Erro ao atualizar fotografia de perfil:', error)
    erroFotografia.value = true
    mensagemFotografia.value = obterMensagemErro(error)
  } finally {
    fotografiaAEnviar.value = false
    input.value = ''
  }
}
</script>

<template>
  <header class="app-header">
    <div class="header-left">
      <button
        class="mobile-menu-button"
        aria-label="Abrir menu"
        @click="emit('toggleSidebar')"
      >
        ☰
      </button>

      <div class="header-heading">
        <span class="header-eyebrow">
          TASKFLOW /
          {{ route.path.startsWith('/my-work') ? 'FRONT-OFFICE' : 'BACK-OFFICE' }}
        </span>

        <h1>{{ title }}</h1>
      </div>
    </div>

    <div class="header-actions">
      <label class="header-search">
        <span aria-hidden="true">⌕</span>

        <input
          v-model="searchQuery"
          type="search"
          placeholder="Pesquisar..."
          aria-label="Pesquisar"
        />

        <kbd>Ctrl K</kbd>
      </label>

      <button
        class="header-icon-button"
        type="button"
        aria-label="Notificações"
        title="Notificações — disponível numa próxima fase"
        disabled
      >
        ♧
      </button>

      <div class="header-divider"></div>

      <div class="header-profile">
        <label
          class="profile-avatar-change"
          :class="{ 'is-uploading': fotografiaAEnviar }"
          :title="fotografiaAEnviar ? 'A carregar fotografia...' : 'Alterar fotografia'"
        >
          <div class="profile-avatar">
            <img
              v-if="avatarUrl && !avatarFalhou"
              :src="avatarUrl"
              :alt="`Fotografia de ${auth.user.value?.name ?? 'administrador'}`"
              @error="avatarFalhou = true"
            />
            <span v-else>
              {{ auth.user.value?.name.slice(0, 1).toUpperCase() ?? 'A' }}
            </span>
          </div>
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp"
            aria-label="Alterar fotografia de perfil"
            :disabled="fotografiaAEnviar || !auth.user.value"
            @change="carregarFotografia"
          />
        </label>

        <NuxtLink
          to="/settings?editProfile=1"
          class="header-profile-link"
          aria-label="Editar perfil"
          title="Editar perfil"
        >
          <div class="profile-copy">
            <strong>{{ auth.user.value?.name ?? 'Administrador' }}</strong>
            <span>Administrador</span>
          </div>
        </NuxtLink>
        <span
          v-if="mensagemFotografia"
          class="profile-upload-message"
          :class="{ 'is-error': erroFotografia }"
          :role="erroFotografia ? 'alert' : 'status'"
        >
          {{ mensagemFotografia }}
        </span>

        <button
          class="logout-button"
          type="button"
          title="Terminar sessão"
          aria-label="Terminar sessão"
          @click="auth.logout"
        >
          <SidebarIcon name="logout" />
        </button>
      </div>
    </div>
  </header>
</template>

<style scoped>
.app-header {
  position: sticky;
  top: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  min-height: 82px;
  padding: 14px 28px;
  background: #fff;
  border-bottom: 1px solid #e2e9f5;
  z-index: 40;
}

.header-left,
.header-actions {
  display: flex;
  align-items: center;
}

.header-left {
  gap: 15px;
}

.header-heading {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.header-eyebrow {
  color: #8b9ab1;
  font-size: 9px;
  font-weight: 800;
  letter-spacing: 0.12em;
}

.header-heading h1 {
  margin: 0;
  color: #172b4d;
  font-size: 21px;
  font-weight: 800;
  letter-spacing: -0.04em;
}

.header-actions {
  gap: 19px;
}

.header-search {
  display: flex;
  align-items: center;
  gap: 9px;
  width: 225px;
  height: 38px;
  padding: 0 10px;
  color: #8b9ab1;
  background: #f5f7fb;
  border: 1px solid #e6ebf3;
  border-radius: 9px;
}

.header-search input {
  width: 100%;
  min-width: 0;
  color: #172b4d;
  background: transparent;
  border: 0;
  outline: none;
  font: inherit;
  font-size: 12px;
}

.header-search input::placeholder {
  color: #9aa7ba;
}

.header-search kbd {
  flex-shrink: 0;
  padding: 3px 5px;
  color: #8492a8;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  font-size: 9px;
}

.header-icon-button {
  position: relative;
  width: 36px;
  height: 36px;
  color: #64748b;
  background: transparent;
  border: 0;
  border-radius: 9px;
  font-size: 20px;
}

.header-icon-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.header-divider {
  width: 1px;
  height: 35px;
  background: #e5eaf2;
}

.header-profile {
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
}

.profile-avatar-change {
  position: relative;
  display: block;
  flex: 0 0 38px;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  cursor: pointer;
}

.profile-avatar-change input {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
}

.profile-avatar-change input:focus-visible {
  outline: 2px solid #6485ff;
  outline-offset: 3px;
  border-radius: 50%;
}

.profile-avatar-change.is-uploading {
  cursor: wait;
  opacity: 0.65;
}

.header-profile-link {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px;
  color: inherit;
  border-radius: 10px;
  text-decoration: none;
}

.header-profile-link:hover,
.header-profile-link:focus-visible {
  background: #f5f7fb;
}

.header-profile-link:focus-visible {
  outline: 2px solid #6485ff;
  outline-offset: 2px;
}

.profile-upload-message {
  position: absolute;
  z-index: 2;
  top: calc(100% + 10px);
  right: 42px;
  width: max-content;
  max-width: min(300px, calc(100vw - 40px));
  padding: 9px 12px;
  color: #166534;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 8px;
  box-shadow: 0 5px 16px rgb(23 43 77 / 12%);
  font-size: 11px;
}

.profile-upload-message.is-error {
  color: #b42318;
  background: #fff5f4;
  border-color: #fecdca;
}

.profile-avatar {
  display: grid;
  flex: 0 0 38px;
  width: 38px;
  height: 38px;
  place-items: center;
  color: #fff;
  background: linear-gradient(145deg, #6485ff, #4164dc);
  border-radius: 50%;
  font-size: 11px;
  font-weight: 800;
}

.profile-avatar img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
}

.profile-avatar span {
  line-height: 1;
}

.profile-copy {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.profile-copy strong {
  color: #263957;
  font-size: 11px;
}

.profile-copy span {
  color: #91a0b5;
  font-size: 10px;
}

.profile-chevron {
  color: #91a0b5;
  font-size: 17px;
}

.logout-button {
  display: grid;
  width: 34px;
  height: 34px;
  place-items: center;
  color: #64748b;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 9px;
  cursor: pointer;
}

.logout-button:hover {
  color: #4338ca;
  background: #eef2ff;
}

.mobile-menu-button {
  display: none;
  width: 38px;
  height: 38px;
  color: #263957;
  background: #f1f5fc;
  border: 1px solid #e2e9f5;
  border-radius: 9px;
  font-size: 18px;
  cursor: pointer;
}

@media (max-width: 900px) {
  .mobile-menu-button {
    display: inline-grid;
    place-items: center;
  }
}

@media (max-width: 650px) {
  .app-header {
    min-height: 72px;
    padding: 12px 14px;
  }

  .header-actions {
    gap: 10px;
  }

  .header-search,
  .header-divider,
  .profile-copy,
  .profile-chevron {
    display: none;
  }

  .header-heading h1 {
    font-size: 18px;
  }
}
</style>
