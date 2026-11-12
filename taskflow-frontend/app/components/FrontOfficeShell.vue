<script setup lang="ts">
import { computed, ref, watch } from 'vue'

// Reúne navegação, identificação da conta e adaptação do menu do membro.
const auth = useAuth()
const route = useRoute()
const mobileOpen = ref(false)
const trocarContaAberto = ref(false)
const notificacoesAbertas = ref(false)
const erroNotificacoes = ref('')
const notificacoes = ref<Notificacao[]>([])
const notificacoesNaoLidasTotal = ref(0)
const erroConta = ref('')
const api = useNuxtApp().$api
const config = useRuntimeConfig()
const apiBase = String(config.public.apiBase)
const avatarUrl = computed(() =>
  obterUrlAvatar(auth.user.value?.avatar_url, apiBase),
)
const avatarFalhou = ref(false)
const nomeConta = computed(() =>
  auth.user.value?.name.trim() || auth.user.value?.email || 'Utilizador',
)

interface Notificacao {
  id: string
  title: string
  message: string
  target: string
  read_at: string | null
}

async function carregarNotificacoes(): Promise<void> {
  erroNotificacoes.value = ''
  if (!auth.user.value) {
    notificacoes.value = []
    notificacoesNaoLidasTotal.value = 0
    return
  }
  try {
    const [items, unread] = await Promise.all([
      api<Notificacao[]>('/notifications/?limit=20'),
      api<{ count: number }>('/notifications/unread-count'),
    ])
    notificacoes.value = items
    notificacoesNaoLidasTotal.value = unread.count
  } catch (error) {
    console.error('Não foi possível carregar as notificações:', error)
    erroNotificacoes.value = 'Não foi possível carregar as notificações. Tente atualizar.'
  }
}

async function abrirNotificacao(item: Notificacao): Promise<void> {
  notificacoesAbertas.value = false
  if (item.read_at === null) {
    try {
      const atualizada = await api<Notificacao>(
        `/notifications/${item.id}/read`,
        { method: 'POST' },
      )
      item.read_at = atualizada.read_at
      notificacoesNaoLidasTotal.value = Math.max(
        0,
        notificacoesNaoLidasTotal.value - 1,
      )
    } catch (error) {
      console.error('Não foi possível marcar a notificação como lida:', error)
    }
  }
  await navigateTo(item.target)
}

watch(
  () => auth.user.value?.id,
  () => void carregarNotificacoes(),
  { immediate: true },
)

// Reinicia o fallback caso a conta ou o endereço da fotografia mude.
watch(avatarUrl, () => {
  avatarFalhou.value = false
})

const pageTitle = computed(() => {
  if (route.path === '/') return 'Dashboard'
  if (route.path.startsWith('/calendar')) return 'Calendário'
  if (route.path.startsWith('/projects')) return 'Projetos'
  if (route.path.startsWith('/teams')) return 'Equipas'
  if (route.path.startsWith('/tasks')) return 'Tarefas'
  if (route.path.startsWith('/my-work')) return 'O meu trabalho'
  if (route.path.startsWith('/settings')) return 'Definições'
  if (route.path.startsWith('/users')) return 'Utilizadores'
  if (route.path.startsWith('/reports')) return 'Relatórios'
  return 'Área de trabalho'
})

function isActivePath(path: string): boolean {
  return route.path === path ||
    (path === '/users' && route.path.startsWith('/users/'))
}

const navigation = [
  { label: 'Dashboard', to: '/', icon: 'dashboard', adminOnly: true },
  { label: 'Projetos', to: '/projects', icon: 'projects', adminOnly: false },
  { label: 'Tarefas', to: '/tasks', icon: 'tasks', adminOnly: false },
  { label: 'Calendário', to: '/calendar', icon: 'calendar', adminOnly: false },
  { label: 'O meu trabalho', to: '/my-work', icon: 'my-work', adminOnly: false },
  { label: 'Equipas', to: '/teams', icon: 'teams', adminOnly: false },
  { label: 'Relatórios', to: '/reports', icon: 'reports', adminOnly: true },
  { label: 'Utilizadores', to: '/users', icon: 'users', adminOnly: true },
  { label: 'Definições', to: '/settings', icon: 'settings', adminOnly: false },
] as const

const navigationVisivel = computed(() =>
  navigation.filter(
    (item) => !item.adminOnly || auth.user.value?.role === 'admin',
  ),
)

const tipoConta = computed(() =>
  auth.user.value?.role === 'admin' ? 'Administrador' : 'Utilizador',
)

const contasGuardadas = computed(() => auth.carregarContasGuardadas())

async function selecionarConta(email: string): Promise<void> {
  trocarContaAberto.value = false
  await navigateTo({
    path: '/login',
    query: { switchAccount: '1', email },
  })
}

async function adicionarConta(): Promise<void> {
  trocarContaAberto.value = false
  await navigateTo('/login?switchAccount=1')
}

async function terminarSessao(): Promise<void> {
  trocarContaAberto.value = false
  erroConta.value = ''
  try {
    await auth.logout()
  } catch (error) {
    console.error('Não foi possível terminar a sessão:', error)
    erroConta.value = 'Não foi possível terminar a sessão. Verifique a ligação e tente novamente.'
  }
}

// Fecha o menu móvel ao navegar, para não o deixar aberto sobre a nova página.
watch(
  () => route.fullPath,
  () => {
    mobileOpen.value = false
    trocarContaAberto.value = false
  },
)
</script>

<template>
  <!-- O painel lateral e o cabeçalho partilham a área de conteúdo das páginas. -->
  <div class="front-office-shell">
    <button
      v-if="mobileOpen"
      class="sidebar-backdrop"
      type="button"
      aria-label="Fechar menu"
      @click="mobileOpen = false"
    />

    <aside class="front-sidebar" :class="{ 'sidebar-open': mobileOpen }">
      <NuxtLink class="sidebar-brand" to="/my-work">
        <span class="brand-mark">T</span>
        <span class="brand-copy">
          <strong>TaskFlow</strong>
          <small>ESPAÇO COLABORATIVO</small>
        </span>
      </NuxtLink>

      <div class="sidebar-caption">MENU PRINCIPAL</div>
      <nav class="sidebar-navigation" aria-label="Navegação do front-office">
        <NuxtLink
          v-for="item in navigationVisivel"
          :key="item.to"
          :to="item.to"
          class="sidebar-link"
          :class="{ 'sidebar-link-active': isActivePath(item.to) }"
          :aria-current="isActivePath(item.to) ? 'page' : undefined"
        >
          <span class="sidebar-icon">
            <SidebarIcon :name="item.icon" />
          </span>
          {{ item.label }}
        </NuxtLink>
      </nav>

      <div class="sidebar-bottom">
        <div class="sidebar-help">
          <span>
            <SidebarIcon name="help" />
          </span>
          <div>
            <strong>Trabalhe em equipa</strong>
            <small>Acompanhe os seus projetos</small>
          </div>
        </div>
        <div class="sidebar-version">TASKFLOW · ÁREA DE TRABALHO</div>
      </div>
    </aside>

    <div class="front-main">
      <header class="front-topbar">
        <button
          class="menu-toggle"
          type="button"
          aria-label="Abrir menu"
          title="Abrir menu"
          :aria-expanded="mobileOpen"
          @click="mobileOpen = !mobileOpen"
        >
          <span></span><span></span><span></span>
        </button>
        <div class="topbar-title">
          <span>TASKFLOW / ÁREA DE TRABALHO</span>
          <strong>{{ pageTitle }}</strong>
        </div>
        <div class="front-notifications">
          <button
            class="front-notification-trigger"
            type="button"
            aria-label="Notificações"
            title="Notificações"
            :aria-expanded="notificacoesAbertas"
            @click="notificacoesAbertas = !notificacoesAbertas"
          >
            <SidebarIcon name="notifications" />
            <span v-if="notificacoesNaoLidasTotal" class="front-notification-count">
              {{ notificacoesNaoLidasTotal > 9 ? '9+' : notificacoesNaoLidasTotal }}
            </span>
          </button>
          <section
            v-if="notificacoesAbertas"
            class="front-notification-panel"
            aria-label="Notificações recentes"
          >
            <header>
              <strong>Notificações</strong>
              <button
                class="icon-action"
                type="button"
                aria-label="Atualizar notificações"
                title="Atualizar notificações"
                data-tooltip="Atualizar notificações"
                @click="carregarNotificacoes"
              >
                <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                  <path d="M20 7v5h-5M4 17v-5h5" />
                  <path d="M5.5 9a7 7 0 0 1 11.7-2L20 12M4 12l2.8 5a7 7 0 0 0 11.7-2" />
                </svg>
              </button>
            </header>
            <p v-if="erroNotificacoes" class="front-notification-error" role="alert">
              {{ erroNotificacoes }}
            </p>
            <p v-if="!notificacoes.length" class="front-notification-empty">
              Não tem notificações.
            </p>
            <button
              v-for="item in notificacoes"
              :key="item.id"
              class="front-notification-item"
              :class="{ 'is-unread': item.read_at === null }"
              type="button"
              @click="abrirNotificacao(item)"
            >
              <strong>{{ item.title }}</strong>
              <span>{{ item.message }}</span>
            </button>
          </section>
        </div>
        <div class="topbar-account">
          <button
            class="account-trigger"
            type="button"
            :aria-expanded="trocarContaAberto"
            aria-haspopup="menu"
            aria-controls="account-switcher"
            aria-label="Conta ativa; abrir alternância de contas"
            @click="trocarContaAberto = !trocarContaAberto"
          >
            <span class="account-avatar">
            <img
              v-if="avatarUrl && !avatarFalhou"
              :src="avatarUrl"
              :alt="`Fotografia de ${auth.user.value?.name ?? 'utilizador'}`"
              @error="avatarFalhou = true"
            />
            <span v-else>
              {{ nomeConta.slice(0, 1).toUpperCase() }}
            </span>
            </span>
            <span class="account-copy">
            <strong>{{ nomeConta }}</strong>
            <small>{{ tipoConta }}</small>
            </span>
          </button>
          <button
            class="switch-account-button icon-action"
            type="button"
            aria-label="Trocar conta"
            title="Trocar conta"
            data-tooltip="Trocar conta"
            @click="trocarContaAberto = !trocarContaAberto"
          >
            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M16 3l4 4-4 4M4 7h16M8 21l-4-4 4-4M20 17H4" />
            </svg>
          </button>
          <div v-if="trocarContaAberto" id="account-switcher" class="account-switcher" role="menu" aria-label="Trocar de conta">
            <p class="account-switcher-title">Contas nesta sessão</p>
            <p v-if="erroConta" class="switcher-error" role="alert">{{ erroConta }}</p>
            <button
              v-for="conta in contasGuardadas"
              :key="conta.user.id"
              class="saved-account"
              role="menuitem"
              type="button"
              :class="{ 'is-current': conta.user.id === auth.user.value?.id }"
              :disabled="conta.user.id === auth.user.value?.id"
              @click="selecionarConta(conta.user.email)"
            >
              <span class="saved-account-avatar">{{ conta.user.name.slice(0, 1).toUpperCase() }}</span>
              <span class="saved-account-copy">
                <strong>{{ conta.user.name }}</strong>
                <small>{{ conta.user.email }}</small>
              </span>
              <span v-if="conta.user.id === auth.user.value?.id">Atual</span>
            </button>
            <button
              class="add-account-button icon-action"
              type="button"
              role="menuitem"
              aria-label="Adicionar outra conta"
              title="Adicionar outra conta"
              data-tooltip="Adicionar outra conta"
              @click="adicionarConta"
            >
              <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <path d="M12 5v14M5 12h14" />
              </svg>
            </button>
            <button
              class="logout-account-button icon-action"
              type="button"
              role="menuitem"
              aria-label="Terminar sessão"
              title="Terminar sessão"
              data-tooltip="Terminar sessão"
              @click="terminarSessao"
            >
              <SidebarIcon name="logout" />
            </button>
          </div>
        </div>
      </header>

      <main class="front-content">
        <slot />
      </main>

      <footer class="front-footer">
        <span>© {{ new Date().getFullYear() }} TaskFlow</span>
        <span>Área de trabalho colaborativa</span>
      </footer>
    </div>
  </div>
</template>

<style scoped>
.front-office-shell { display: flex; width: 100%; min-width: 0; min-height: 100vh; color: #172b4d; background: var(--tf-bg); font-family: var(--tf-font, 'Segoe UI', sans-serif); }
.front-sidebar { position: sticky; z-index: 20; top: 0; display: flex; width: 258px; height: 100vh; flex: 0 0 258px; flex-direction: column; padding: 22px 16px 14px; color: #e7edfa; background: #192a49; border-right: 1px solid #263957; }
.sidebar-brand { display: flex; min-height: 54px; align-items: center; gap: 12px; margin-bottom: 26px; padding: 0 7px; text-decoration: none; }
.brand-mark { display: grid; width: 42px; height: 42px; flex: 0 0 42px; place-items: center; color: #fff; background: linear-gradient(145deg, #6485ff, #4164dc); border-radius: 13px; box-shadow: 0 5px 15px rgb(65 100 220 / 25%); font-size: 21px; font-weight: 800; }
.brand-copy { display: flex; flex-direction: column; gap: 4px; }
.brand-copy strong { color: #fff; font-size: 17px; font-weight: 800; letter-spacing: -.03em; }
.brand-copy small { color: #9eafca; font-size: 9px; font-weight: 700; letter-spacing: .12em; }
.sidebar-caption { padding: 0 10px; margin-bottom: 9px; color: #91a4c2; font-size: 10px; font-weight: 800; letter-spacing: .12em; }
.sidebar-navigation { display: grid; gap: 5px; }
.sidebar-link { position: relative; display: flex; min-height: 44px; align-items: center; gap: 12px; padding: 0 12px; color: #bdcbe0; border: 1px solid transparent; border-radius: 10px; font-size: 14px; font-weight: 600; text-decoration: none; transition: background .18s ease, color .18s ease, border-color .18s ease; }
.sidebar-link:hover { color: #fff; background: #263b5d; }
.sidebar-link-active { color: #fff; background: #34579a; border-color: #4168b0; box-shadow: inset 3px 0 0 #83a5ff; font-weight: 750; }
.sidebar-icon { display: grid; width: 22px; flex: 0 0 22px; place-items: center; color: #9db7ee; font-size: 19px; }
.sidebar-link-active .sidebar-icon { color: #fff; }
.sidebar-bottom { margin-top: auto; padding-top: 28px; }
.sidebar-help { display: flex; align-items: center; gap: 10px; padding: 13px 10px; background: #223756; border: 1px solid #304564; border-radius: 10px; }
.sidebar-help > span { display: grid; width: 25px; height: 25px; flex: 0 0 25px; place-items: center; color: #dbeafe; background: #36548a; border-radius: 8px; font-size: 12px; font-weight: 800; }
.sidebar-help div { display: grid; gap: 3px; }
.sidebar-help strong { color: #f1f5ff; font-size: 11px; }
.sidebar-help small { color: #a9bad3; font-size: 10px; }
.sidebar-version { padding: 13px 5px 0; color: #91a4c2; font-size: 9px; font-weight: 700; letter-spacing: .09em; }
.front-main { display: flex; width: 0; min-width: 0; min-height: 100vh; flex: 1 1 0%; flex-direction: column; background: var(--tf-bg); }
.front-topbar { position: sticky; z-index: 10; top: 0; display: flex; min-height: 76px; align-items: center; justify-content: space-between; gap: 16px; padding: 10px 30px; background: var(--tf-surface); border-bottom: 1px solid var(--tf-border); backdrop-filter: blur(12px); }
.topbar-title { display: grid; gap: 5px; }
.topbar-title > span { color: #94a0b3; font-size: 10px; font-weight: 750; letter-spacing: .12em; }
.topbar-title > strong { color: #263650; font-size: 17px; font-weight: 700; letter-spacing: -.025em; }
.front-notifications { position: relative; margin-left: auto; }
.front-notification-trigger { position: relative; display: grid; width: 38px; height: 38px; place-items: center; color: #62718a; background: #f7f8fc; border: 1px solid #e6eaf1; border-radius: 10px; cursor: pointer; }
.front-notification-trigger:hover { color: #4e57d1; background: #f0f2ff; }
.front-notification-count { position: absolute; top: -5px; right: -5px; min-width: 17px; padding: 2px 4px; color: #fff; background: #dc4058; border: 2px solid #fff; border-radius: 10px; font-size: 8px; font-weight: 800; }
.front-notification-panel { position: absolute; z-index: 40; top: calc(100% + 12px); right: 0; display: grid; width: min(340px, calc(100vw - 28px)); max-height: 420px; overflow-y: auto; padding: 10px; background: #fff; border: 1px solid #dde5f0; border-radius: 12px; box-shadow: 0 18px 38px rgb(36 54 80 / 16%); }
.front-notification-panel > header { display: flex; align-items: center; justify-content: space-between; padding: 7px 8px 10px; border-bottom: 1px solid #edf0f5; }
.front-notification-panel > header strong { color: #34445c; font-size: 12px; }
.front-notification-panel > header button { color: #4e57d1; background: transparent; border: 0; cursor: pointer; }
.icon-action { position: relative; display: grid; width: 36px; height: 36px; flex: 0 0 36px; place-items: center; padding: 0; color: #4e57d1; background: #fff; border: 1px solid #d8def8; border-radius: 9px; cursor: pointer; transition: background .18s ease, color .18s ease, border-color .18s ease; }
.icon-action svg { width: 17px; height: 17px; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.icon-action:hover { color: #3730a3; background: #f1f3ff; border-color: #bfc8f5; }
.icon-action:focus-visible { outline: 3px solid rgb(99 102 241 / 25%); outline-offset: 2px; }
.icon-action[data-tooltip]::after { position: absolute; z-index: 60; top: calc(100% + 8px); left: 50%; width: max-content; max-width: 200px; padding: 6px 9px; color: #fff; background: #192a49; border-radius: 6px; box-shadow: 0 4px 12px rgb(25 42 73 / 18%); content: attr(data-tooltip); font-size: 10px; font-weight: 600; line-height: 1.3; opacity: 0; pointer-events: none; transform: translate(-50%, -3px); transition: opacity .15s ease, transform .15s ease; }
.icon-action[data-tooltip]:hover::after, .icon-action[data-tooltip]:focus-visible::after { opacity: 1; transform: translate(-50%, 0); }
.front-notification-empty { padding: 15px 8px; color: #8390a5; font-size: 11px; }
.front-notification-error { margin: 8px; padding: 9px; color: #a53636; background: #fff4f3; border-radius: 7px; font-size: 10px; line-height: 1.4; }
.front-notification-item { display: grid; gap: 5px; padding: 10px 8px; color: #46556d; background: #fff; border: 0; border-bottom: 1px solid #f0f2f6; text-align: left; cursor: pointer; }
.front-notification-item:hover { background: #f8f9fd; }
.front-notification-item.is-unread { background: #f3f5ff; }
.front-notification-item strong { color: #34445c; font-size: 11px; }
.front-notification-item span { color: #7b879a; font-size: 10px; line-height: 1.5; }
.topbar-account { position: relative; display: flex; align-items: center; gap: 10px; }
.account-trigger { display: flex; align-items: center; gap: 10px; min-width: 0; padding: 3px; color: inherit; background: transparent; border: 0; border-radius: 9px; cursor: pointer; }
.account-trigger:hover { background: #f6f8fc; }
.account-avatar { display: grid; width: 36px; height: 36px; overflow: hidden; place-items: center; color: #505bd0; background: #eef0ff; border-radius: 50%; font-size: 13px; font-weight: 800; }
.account-avatar img { width: 100%; height: 100%; object-fit: cover; }
.account-copy { display: grid; gap: 3px; }
.account-copy strong { max-width: 150px; overflow: hidden; color: #35435c; font-size: 12px; text-overflow: ellipsis; white-space: nowrap; }
.account-copy small { color: #98a3b5; font-size: 10px; }
.logout-account-button { color: #a53636; border-color: #f0d7d5; }
.logout-account-button:hover { color: #8d2929; background: #fff4f3; border-color: #f1cccc; }
.account-switcher { position: absolute; z-index: 30; top: calc(100% + 12px); right: 0; display: grid; width: min(310px, calc(100vw - 28px)); gap: 6px; padding: 12px; background: #fff; border: 1px solid #dde5f0; border-radius: 12px; box-shadow: 0 18px 38px rgb(36 54 80 / 16%); }
.account-switcher-title { margin: 0 0 3px; padding: 0 4px; color: #8290a6; font-size: 9px; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }
.saved-account { display: flex; width: 100%; align-items: center; gap: 9px; padding: 8px; color: #35435c; background: #fff; border: 1px solid transparent; border-radius: 9px; text-align: left; cursor: pointer; }
.saved-account:hover:not(:disabled) { background: #f5f7fc; border-color: #e0e7f2; }
.saved-account.is-current { background: #eef1ff; cursor: default; }
.saved-account:disabled { opacity: 1; }
.saved-account-avatar { display: grid; width: 30px; height: 30px; flex: 0 0 30px; place-items: center; color: #4f46e5; background: #e9eaff; border-radius: 50%; font-size: 11px; font-weight: 800; }
.saved-account-copy { display: grid; min-width: 0; gap: 2px; }
.saved-account-copy strong, .saved-account-copy small { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.saved-account-copy strong { font-size: 11px; }
.saved-account-copy small { color: #8390a5; font-size: 9px; }
.saved-account > span:last-child { margin-left: auto; color: #5b65d8; font-size: 9px; font-weight: 750; }
.switcher-error { margin: 3px 0; padding: 8px; color: #a53636; background: #fff4f3; border-radius: 7px; font-size: 9px; line-height: 1.4; }
.add-account-button, .logout-account-button { width: 100%; height: 36px; margin-top: 3px; }
.front-content { width: 100%; min-width: 0; flex: 1; padding: 24px; box-sizing: border-box; }
.front-footer { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 10px; padding: 18px 28px; color: #7b8aa2; background: var(--tf-surface); border-top: 1px solid var(--tf-border); font-size: 12px; }
.menu-toggle, .sidebar-backdrop { display: none; }

@media (max-width: 760px) {
  .front-sidebar { position: fixed; flex: none; transform: translateX(-100%); transition: transform .22s ease; }
  .front-sidebar.sidebar-open { transform: translateX(0); }
  .sidebar-backdrop { position: fixed; z-index: 15; inset: 0; display: block; background: rgb(15 23 42 / 42%); border: 0; }
  .front-main { margin-left: 0; }
  .front-topbar { min-height: 66px; padding: 9px 14px; }
  .menu-toggle { display: grid; width: 35px; height: 35px; flex: 0 0 35px; align-content: center; gap: 4px; padding: 7px; background: #f5f6fb; border: 1px solid #e8edf5; border-radius: 8px; cursor: pointer; }
  .menu-toggle span { height: 2px; background: #52617b; border-radius: 2px; }
  .topbar-title { margin-right: auto; }
  .topbar-title > span { font-size: 7px; }
  .topbar-title > strong { font-size: 15px; }
  .topbar-account { gap: 7px; }
  .account-copy { min-width: 0; }
  .account-copy strong { max-width: 82px; font-size: 11px; }
  .account-copy small { display: none; }
  .front-content { padding: 12px; }
  .front-footer { padding: 16px; }
}

@media (prefers-reduced-motion: reduce) {
  .sidebar-link, .switch-account-button, .add-account-button, .logout-account-button, .account-trigger, .front-sidebar { transition: none; }
}
</style>
