
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
]

const workspaceLinks = [
  { label: 'Calendário', icon: '▦' },
  { label: 'Equipa', icon: '♙' },
  { label: 'Relatórios', icon: '▥' },
]
</script>

<template>
  <div
    v-if="mobileOpen"
    class="sidebar-backdrop"
    @click="emit('close')"
  />

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
        :class="{ 'is-active': route.path === link.to }"
        :aria-current="route.path === link.to ? 'page' : undefined"
        @click="emit('close')"
      >
        <span class="sidebar-link-icon" aria-hidden="true">
          {{ link.icon }}
        </span>
        <span>{{ link.label }}</span>
        <span
          v-if="route.path === link.to"
          class="active-indicator"
        />
      </NuxtLink>

      <p class="sidebar-section-label workspace-label">ESPAÇO DE TRABALHO</p>

      <div
        v-for="link in workspaceLinks"
        :key="link.label"
        class="sidebar-link sidebar-link-upcoming"
        :title="`${link.label} — disponível numa próxima fase`"
      >
        <span class="sidebar-link-icon" aria-hidden="true">
          {{ link.icon }}
        </span>
        <span>{{ link.label }}</span>
        <span class="upcoming-dot" />
      </div>
    </nav>

    <div class="sidebar-bottom">
      <NuxtLink
        to="/settings"
        class="sidebar-link sidebar-settings"
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

      <div class="sidebar-version">TASKFLOW · V1.0</div>
    </div>
  </aside>
</template>
