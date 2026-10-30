
<script setup lang="ts">
const route = useRoute()
const mobileOpen = ref(false)

const pageTitle = computed(() => {
  if (route.path === '/') return 'Dashboard'
  if (route.path.startsWith('/projects')) return 'Projetos'
  if (route.path.startsWith('/tasks')) return 'Tarefas'
  if (route.path.startsWith('/users')) return 'Utilizadores'
  if (route.path.startsWith('/settings')) return 'Definições'
  return 'TaskFlow'
})

watch(
  () => route.fullPath,
  () => {
    mobileOpen.value = false
  },
)
</script>

<template>
  <div class="admin-shell">
    <AdminAppSidebar
      :mobile-open="mobileOpen"
      @close="mobileOpen = false"
    />

    <div class="admin-main">
      <AdminAppHeader
        :title="pageTitle"
        @toggle-sidebar="mobileOpen = !mobileOpen"
      />

      <main class="admin-content">
        <slot />
      </main>

      <footer class="admin-footer">
        <span>© {{ new Date().getFullYear() }} TaskFlow</span>
        <span>Gestão de projetos e tarefas académicas</span>
      </footer>
    </div>
  </div>
</template>

<style scoped>
.admin-shell {
  display: flex;
  min-height: 100vh;
  background: #f1f5fc;
  color: #172b4d;
}

.admin-main {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-width: 0;
  min-height: 100vh;
  background: #f1f5fc;
}

.admin-content {
  flex: 1;
  width: 100%;
  min-width: 0;
  padding: 24px;
  box-sizing: border-box;
}

.admin-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 10px;
  padding: 18px 28px;
  color: #7b8aa2;
  background: #fff;
  border-top: 1px solid #e2e9f5;
  font-size: 12px;
}

@media (max-width: 700px) {
  .admin-content {
    padding: 12px;
  }

  .admin-footer {
    padding: 16px;
  }
}
</style>
