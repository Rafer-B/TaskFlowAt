
<script setup lang="ts">
defineProps<{
  title: string
}>()

const emit = defineEmits<{
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
        @click="emit('toggleSidebar')"
      >
        ☰
      </button>

      <div class="header-heading">
        <span class="header-eyebrow">
          TASKFLOW / BACK-OFFICE
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
  display: flex;
  align-items: center;
  gap: 10px;
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
