
<script setup lang="ts">
// Escolhe a navegação administrativa ou a área de membro conforme o papel autenticado.
const route = useRoute()
const auth = useAuth()
const mobileOpen = ref(false)

const pageTitle = computed(() => {
  if (route.path === '/') return 'Dashboard'
  if (route.path.startsWith('/my-work')) return 'A minha área'
  if (route.path.startsWith('/calendar')) return 'Calendário'
  if (route.path.startsWith('/projects')) return 'Projetos'
  if (route.path.startsWith('/teams')) return 'Equipas'
  if (route.path.startsWith('/reports')) return 'Relatórios'
  if (route.path.startsWith('/tasks')) return 'Tarefas'
  if (route.path.startsWith('/users')) return 'Utilizadores'
  if (route.path.startsWith('/settings')) return 'Definições'
  return 'TaskFlow'
})

watch(
  () => route.fullPath,
  () => {
    // A mudança de rota também dispensa o menu móvel aberto.
    mobileOpen.value = false
  },
)
</script>

<template>
  <div class="admin-shell">
    <ClientOnly>
      <template v-if="auth.user.value?.role === 'admin'">
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
      </template>

      <FrontOfficeShell v-else>
        <slot />
      </FrontOfficeShell>

      <template #fallback>
        <div class="auth-layout-loading" aria-busy="true" aria-label="A carregar sessão"></div>
      </template>
    </ClientOnly>
  </div>
</template>

<style scoped>
.admin-shell {
  display: flex;
  width: 100%;
  min-width: 0;
  min-height: 100vh;
  background: var(--tf-bg);
  color: #172b4d;
}

.auth-layout-loading {
  width: 100%;
  min-height: 100vh;
  background: var(--tf-bg);
}

.admin-main {
  display: flex;
  width: 0;
  flex: 1 1 0%;
  flex-direction: column;
  min-width: 0;
  min-height: 100vh;
  background: var(--tf-bg);
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
