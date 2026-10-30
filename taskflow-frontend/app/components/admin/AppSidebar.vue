
<script setup lang="ts">
const route = useRoute()

defineProps<{
  mobileOpen: boolean
}>()

const emit = defineEmits<{
  close: []
}>()

const mainLinks = [
  { label: 'Dashboard', to: '/', icon: '▦' },
  { label: 'Projetos', to: '/projects', icon: '▤' },
  { label: 'Tarefas', to: '/tasks', icon: '✓' },
  { label: 'Utilizadores', to: '/users', icon: '♙' },
]

const workspaceLinks = [
  { label: 'Calendário', icon: '▦' },
  { label: 'Equipa', icon: '♙' },
  { label: 'Relatórios', icon: '▥' },
]

function isActive(path: string) {
  if (path === '/') {
    return route.path === '/'
  }

  return route.path === path || route.path.startsWith(`${path}/`)
}
</script>

<template>
  <div
    v-if="mobileOpen"
    class="sidebar-backdrop"
    @click="emit('close')"
  ></div>

  <aside
    class="app-sidebar"
    :class="{ 'is-open': mobileOpen }"
    aria-label="Navegação principal"
  >
    <div class="sidebar-brand">
      <div class="brand-mark">T</div>

      <div class="brand-copy">
        <strong>TaskFlow</strong>
        <span>Workspace</span>
      </div>

      <button
        class="sidebar-close"
        aria-label="Fechar menu"
        @click="emit('close')"
      >
        ×
      </button>
    </div>

    <div class="sidebar-workspace">
      <div class="workspace-avatar">TF</div>

      <div class="workspace-copy">
        <strong>TaskFlow Académico</strong>
        <span>Área de trabalho</span>
      </div>

      <span class="workspace-chevron">⌄</span>
    </div>

    <nav class="sidebar-nav">
      <p class="sidebar-section-label">MENU PRINCIPAL</p>

      <NuxtLink
        v-for="link in mainLinks"
        :key="link.to"
        :to="link.to"
        class="sidebar-link"
        :class="{ 'is-active': isActive(link.to) }"
        :aria-current="isActive(link.to) ? 'page' : undefined"
        @click="emit('close')"
      >
        <span class="sidebar-link-icon" aria-hidden="true">
          {{ link.icon }}
        </span>

        <span>{{ link.label }}</span>

        <span
          v-if="isActive(link.to)"
          class="active-indicator"
        ></span>
      </NuxtLink>

      <p class="sidebar-section-label workspace-label">
        ESPAÇO DE TRABALHO
      </p>

      <div
        v-for="link in workspaceLinks"
        :key="link.label"
        class="sidebar-link sidebar-link-upcoming"
        :title="`${link.label} — disponível numa próxima fase`"
        aria-disabled="true"
      >
        <span class="sidebar-link-icon" aria-hidden="true">
          {{ link.icon }}
        </span>

        <span>{{ link.label }}</span>

        <span class="upcoming-dot"></span>
      </div>
    </nav>

    <div class="sidebar-bottom">
      <NuxtLink
        to="/settings"
        class="sidebar-link sidebar-settings"
        :class="{ 'is-active': isActive('/settings') }"
        @click="emit('close')"
      >
        <span class="sidebar-link-icon" aria-hidden="true">⚙</span>
        <span>Definições</span>
      </NuxtLink>

      <div class="sidebar-help">
        <div class="help-symbol">?</div>

        <div>
          <strong>Precisa de ajuda?</strong>
          <span>Consulte o suporte</span>
        </div>
      </div>

      <div class="sidebar-version">
        TASKFLOW · V1.0
      </div>
    </div>
  </aside>
</template>

<style scoped>
.app-sidebar {
  position: sticky;
  top: 0;
  display: flex;
  flex: 0 0 258px;
  flex-direction: column;
  width: 258px;
  height: 100vh;
  padding: 22px 16px 14px;
  box-sizing: border-box;
  overflow-y: auto;
  color: #e7edfa;
  background: #192a49;
  border-right: 1px solid #263957;
  z-index: 50;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 54px;
  margin-bottom: 26px;
  padding: 0 7px;
}

.brand-mark {
  display: grid;
  flex: 0 0 42px;
  width: 42px;
  height: 42px;
  place-items: center;
  color: #fff;
  background: linear-gradient(145deg, #6485ff, #4164dc);
  border-radius: 13px;
  box-shadow: 0 5px 15px rgb(65 100 220 / 25%);
  font-size: 21px;
  font-weight: 800;
}

.brand-copy,
.workspace-copy {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 4px;
}

.brand-copy strong {
  color: #fff;
  font-size: 17px;
  font-weight: 800;
  letter-spacing: -0.03em;
}

.brand-copy span {
  color: #9eafca;
  font-size: 11px;
}

.sidebar-close {
  display: none;
  margin-left: auto;
  padding: 5px 9px;
  color: #e7edfa;
  background: transparent;
  border: 0;
  border-radius: 8px;
  font-size: 25px;
  cursor: pointer;
}

.sidebar-workspace {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 13px 10px;
  margin-bottom: 25px;
  background: #223756;
  border: 1px solid #304564;
  border-radius: 12px;
}

.workspace-avatar {
  display: grid;
  flex: 0 0 36px;
  width: 36px;
  height: 36px;
  place-items: center;
  color: #dbeafe;
  background: #36548a;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 800;
}

.workspace-copy {
  flex: 1;
}

.workspace-copy strong {
  color: #f1f5ff;
  font-size: 11px;
  font-weight: 700;
}

.workspace-copy span {
  color: #a9bad3;
  font-size: 10px;
}

.workspace-chevron {
  color: #a9bad3;
  font-size: 17px;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.sidebar-section-label {
  margin: 0 0 9px;
  padding: 0 10px;
  color: #91a4c2;
  font-size: 9px;
  font-weight: 800;
  letter-spacing: 0.12em;
}

.workspace-label {
  margin-top: 27px;
  margin-bottom: 9px;
}

.sidebar-link {
  position: relative;
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 44px;
  padding: 0 12px;
  color: #bdcbe0;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
  text-decoration: none;
  transition:
    color 0.18s ease,
    background 0.18s ease,
    border-color 0.18s ease;
}

.sidebar-link:not(.sidebar-link-upcoming):hover {
  color: #fff;
  background: #263b5d;
}

.sidebar-link.is-active {
  color: #fff;
  background: #34579a;
  border-color: #4168b0;
  box-shadow: inset 3px 0 0 #83a5ff;
}

.sidebar-link-icon {
  display: grid;
  flex: 0 0 22px;
  width: 22px;
  place-items: center;
  color: #9db7ee;
  font-size: 19px;
  line-height: 1;
}

.sidebar-link.is-active .sidebar-link-icon {
  color: #fff;
}

.active-indicator {
  width: 6px;
  height: 6px;
  margin-left: auto;
  background: #a9c4ff;
  border-radius: 50%;
}

.sidebar-link-upcoming {
  color: #8294b0;
  cursor: default;
}

.sidebar-link-upcoming .sidebar-link-icon {
  color: #8294b0;
}

.upcoming-dot {
  width: 5px;
  height: 5px;
  margin-left: auto;
  background: #647997;
  border-radius: 50%;
}

.sidebar-bottom {
  display: flex;
  flex-direction: column;
  gap: 9px;
  margin-top: auto;
  padding-top: 28px;
}

.sidebar-settings {
  margin-bottom: 10px;
}

.sidebar-help {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 13px 10px;
  background: #223756;
  border: 1px solid #304564;
  border-radius: 11px;
}

.help-symbol {
  display: grid;
  flex: 0 0 30px;
  width: 30px;
  height: 30px;
  place-items: center;
  color: #c9d9ff;
  background: #36548a;
  border-radius: 9px;
  font-size: 14px;
  font-weight: 800;
}

.sidebar-help > div:last-child {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.sidebar-help strong {
  color: #edf3ff;
  font-size: 10px;
}

.sidebar-help span {
  color: #9eafca;
  font-size: 10px;
}

.sidebar-version {
  padding: 13px 5px 0;
  color: #8294b0;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.09em;
  text-align: center;
}

.sidebar-backdrop {
  position: fixed;
  inset: 0;
  background: rgb(9 21 40 / 55%);
  backdrop-filter: blur(3px);
  z-index: 90;
}

@media (max-width: 900px) {
  .app-sidebar {
    position: fixed;
    top: 0;
    bottom: 0;
    left: 0;
    width: min(290px, 85vw);
    height: 100dvh;
    transform: translateX(-105%);
    visibility: hidden;
    transition:
      transform 0.25s ease,
      visibility 0.25s ease;
    z-index: 100;
  }

  .app-sidebar.is-open {
    transform: translateX(0);
    visibility: visible;
  }

  .sidebar-close {
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }
}

@media (prefers-reduced-motion: reduce) {
  .app-sidebar,
  .sidebar-link {
    transition: none;
  }
}
</style>
