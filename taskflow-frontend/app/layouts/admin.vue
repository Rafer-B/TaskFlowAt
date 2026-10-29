
<script setup lang="ts">
const route = useRoute()
const mobileOpen = ref(false)

const pageTitle = computed(() => {
  if (route.path === '/') return 'Dashboard'
  if (route.path.startsWith('/projects')) return 'Projetos'
  if (route.path.startsWith('/tasks')) return 'Tarefas'
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
