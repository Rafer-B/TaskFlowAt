<script setup lang="ts">
const auth = useAuth()
const route = useRoute()
const mobileOpen = ref(false)

const pageTitle = computed(() => {
  if (route.path.startsWith('/front-office')) return 'Painel'
  if (route.path.startsWith('/calendar')) return 'Calendário'
  if (route.path.startsWith('/projects')) return 'Projetos'
  if (route.path.startsWith('/teams')) return 'Equipas'
  if (route.path.startsWith('/tasks')) return 'Tarefas'
  if (route.path.startsWith('/my-work')) return 'O meu trabalho'
  return 'Área de trabalho'
})

const navigation = [
  { label: 'Painel', to: '/front-office', icon: '▦' },
  { label: 'Calendário', to: '/calendar', icon: '▣' },
  { label: 'Projetos', to: '/projects', icon: '▤' },
  { label: 'Equipas', to: '/teams', icon: '♙' },
  { label: 'Tarefas', to: '/tasks', icon: '✓' },
  { label: 'O meu trabalho', to: '/my-work', icon: '✦' },
]

watch(
  () => route.fullPath,
  () => {
    mobileOpen.value = false
  },
)
</script>

<template>
  <div class="front-office-shell">
    <button
      v-if="mobileOpen"
      class="sidebar-backdrop"
      type="button"
      aria-label="Fechar menu"
      @click="mobileOpen = false"
    />

    <aside class="front-sidebar" :class="{ 'sidebar-open': mobileOpen }">
      <NuxtLink class="sidebar-brand" to="/front-office">
        <span class="brand-mark">T</span>
        <span class="brand-copy">
          <strong>TaskFlow</strong>
          <small>ESPAÇO COLABORATIVO</small>
        </span>
      </NuxtLink>

      <div class="sidebar-caption">MENU PRINCIPAL</div>
      <nav class="sidebar-navigation" aria-label="Navegação do front-office">
        <NuxtLink
          v-for="item in navigation"
          :key="item.to"
          :to="item.to"
          class="sidebar-link"
          :class="{ 'sidebar-link-active': route.path.startsWith(item.to) }"
          :aria-current="route.path.startsWith(item.to) ? 'page' : undefined"
        >
          <span class="sidebar-icon" aria-hidden="true">{{ item.icon }}</span>
          {{ item.label }}
        </NuxtLink>
      </nav>

      <div class="sidebar-bottom">
        <div class="sidebar-help">
          <span aria-hidden="true">?</span>
          <div>
            <strong>Trabalhe em equipa</strong>
            <small>Acompanhe os seus projetos</small>
          </div>
        </div>
        <div class="sidebar-version">TASKFLOW · FRONT-OFFICE</div>
      </div>
    </aside>

    <div class="front-main">
      <header class="front-topbar">
        <button
          class="menu-toggle"
          type="button"
          aria-label="Abrir menu"
          :aria-expanded="mobileOpen"
          @click="mobileOpen = !mobileOpen"
        >
          <span></span><span></span><span></span>
        </button>
        <div class="topbar-title">
          <span> TASKFLOW / FRONT-OFFICE</span>
          <strong>{{ pageTitle }}</strong>
        </div>
        <div class="topbar-account">
          <span class="account-avatar">
            {{ auth.user.value?.name.slice(0, 1).toUpperCase() ?? 'U' }}
          </span>
          <span class="account-copy">
            <strong>{{ auth.user.value?.name ?? 'Utilizador' }}</strong>
            <small>Utilizador</small>
          </span>
          <button class="logout-button" type="button" @click="auth.logout">
            Terminar sessão
          </button>
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
.front-office-shell { display: flex; min-height: 100vh; color: #172b4d; background: #f1f5fc; font-family: var(--tf-font, 'Segoe UI', sans-serif); }
.front-sidebar { position: sticky; z-index: 20; top: 0; display: flex; width: 258px; height: 100vh; flex: 0 0 258px; flex-direction: column; padding: 25px 16px 15px; background: #fff; border-right: 1px solid #e8edf5; }
.sidebar-brand { display: flex; align-items: center; gap: 11px; padding: 0 8px 29px; text-decoration: none; }
.brand-mark { display: grid; width: 40px; height: 40px; place-items: center; color: #fff; background: linear-gradient(145deg, #6678ef, #4f58d4); border-radius: 12px; box-shadow: 0 5px 12px rgb(79 70 229 / 22%); font-size: 19px; font-weight: 800; }
.brand-copy { display: flex; flex-direction: column; gap: 4px; }
.brand-copy strong { color: #1e2d49; font-size: 15px; letter-spacing: -.03em; }
.brand-copy small { color: #98a3b6; font-size: 8px; font-weight: 750; letter-spacing: .12em; }
.sidebar-caption { padding: 0 11px; margin-bottom: 10px; color: #9aa5b7; font-size: 9px; font-weight: 800; letter-spacing: .12em; }
.sidebar-navigation { display: grid; gap: 5px; }
.sidebar-link { display: flex; min-height: 43px; align-items: center; gap: 12px; padding: 0 12px; color: #67758d; border-radius: 9px; font-size: 12px; font-weight: 600; text-decoration: none; transition: background .18s ease, color .18s ease; }
.sidebar-link:hover { color: #4f58d4; background: #f5f6ff; }
.sidebar-link-active { color: #4e57d1; background: #eef0ff; font-weight: 700; }
.sidebar-icon { display: grid; width: 20px; place-items: center; font-size: 16px; }
.sidebar-bottom { margin-top: auto; }
.sidebar-help { display: flex; align-items: center; gap: 10px; padding: 12px 10px; background: #f7f8ff; border: 1px solid #eceeff; border-radius: 10px; }
.sidebar-help > span { display: grid; width: 25px; height: 25px; place-items: center; color: #5965d9; background: #e9ebff; border-radius: 8px; font-size: 12px; font-weight: 800; }
.sidebar-help div { display: grid; gap: 3px; }
.sidebar-help strong { color: #44516a; font-size: 10px; }
.sidebar-help small { color: #8d98aa; font-size: 9px; }
.sidebar-version { padding: 17px 7px 0; color: #a4adbc; font-size: 8px; font-weight: 700; letter-spacing: .08em; }
.front-main { display: flex; min-width: 0; min-height: 100vh; flex: 1; flex-direction: column; background: #f1f5fc; }
.front-topbar { position: sticky; z-index: 10; top: 0; display: flex; min-height: 76px; align-items: center; justify-content: space-between; gap: 16px; padding: 10px 30px; background: rgb(255 255 255 / 96%); border-bottom: 1px solid #e8edf5; backdrop-filter: blur(12px); }
.topbar-title { display: grid; gap: 5px; }
.topbar-title > span { color: #94a0b3; font-size: 8px; font-weight: 750; letter-spacing: .12em; }
.topbar-title > strong { color: #263650; font-size: 17px; font-weight: 700; letter-spacing: -.025em; }
.topbar-account { display: flex; align-items: center; gap: 10px; }
.account-avatar { display: grid; width: 36px; height: 36px; place-items: center; color: #505bd0; background: #eef0ff; border-radius: 50%; font-size: 13px; font-weight: 800; }
.account-copy { display: grid; gap: 3px; }
.account-copy strong { max-width: 150px; overflow: hidden; color: #35435c; font-size: 11px; text-overflow: ellipsis; white-space: nowrap; }
.account-copy small { color: #98a3b5; font-size: 9px; }
.logout-button { padding: 8px 11px; color: #6c788d; background: #fff; border: 1px solid #e1e7f0; border-radius: 8px; font-size: 10px; font-weight: 600; cursor: pointer; transition: background .18s ease, color .18s ease; }
.logout-button:hover { color: #4e57d1; background: #f6f7ff; }
.front-content { width: 100%; min-width: 0; flex: 1; padding: 24px; box-sizing: border-box; }
.front-footer { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 10px; padding: 18px 28px; color: #7b8aa2; background: #fff; border-top: 1px solid #e2e9f5; font-size: 12px; }
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
  .account-copy { display: none; }
  .logout-button { padding: 7px 8px; font-size: 9px; }
  .front-content { padding: 12px; }
  .front-footer { padding: 16px; }
}

@media (prefers-reduced-motion: reduce) {
  .sidebar-link, .logout-button, .front-sidebar { transition: none; }
}
</style>
