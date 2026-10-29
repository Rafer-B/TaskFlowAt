
<script setup lang="ts">
defineProps<{
  title: string
}>()

defineEmits<{
  toggleSidebar: []
}>()

const searchQuery = ref('')
</script>

<template>
  <header class="app-header">
    <div class="header-left">
      <button
        class="mobile-menu-button"
        aria-label="Abrir menu"
        @click="$emit('toggleSidebar')"
      >
        ☰
      </button>

      <div class="header-heading">
        <span class="header-eyebrow">TASKFLOW / BACK-OFFICE</span>
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
        <kbd>⌘ K</kbd>
      </label>

      <button
        class="header-icon-button"
        aria-label="Notificações"
        title="Notificações"
      >
        ♧
        <span class="notification-dot" />
      </button>

      <div class="header-divider" />

      <div class="header-profile">
        <div class="profile-avatar">AD</div>
        <div class="profile-copy">
          <strong>Administrador</strong>
          <span>Gestão da plataforma</span>
        </div>
        <span class="profile-chevron">⌄</span>
      </div>
    </div>
  </header>
</template>
