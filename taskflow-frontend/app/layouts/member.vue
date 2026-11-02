<script setup lang="ts">
const auth = useAuth()
</script>

<template>
  <div class="member-shell">
    <header class="member-topbar">
      <NuxtLink class="member-brand" to="/my-work">
        <span class="brand-mark">T</span>
        <span><strong>TaskFlow</strong><small>Área de trabalho</small></span>
      </NuxtLink>

      <div class="member-account">
        <div class="account-avatar">
          {{ auth.user.value?.name.slice(0, 1).toUpperCase() ?? 'U' }}
        </div>
        <div class="account-copy">
          <strong>{{ auth.user.value?.name ?? 'Utilizador' }}</strong>
          <span>Utilizador</span>
        </div>
        <button type="button" @click="auth.logout">Terminar sessão</button>
      </div>
    </header>

    <main class="member-content">
      <slot />
    </main>

    <footer class="member-footer">
      © {{ new Date().getFullYear() }} TaskFlow · Área de trabalho do utilizador
    </footer>
  </div>
</template>

<style scoped>
.member-shell { min-height: 100vh; color: #172b4d; background: #f1f5fc; }
.member-topbar { display: flex; min-height: 72px; align-items: center; justify-content: space-between; gap: 16px; padding: 10px max(24px, calc((100% - 1320px) / 2)); background: #fff; border-bottom: 1px solid #e2e9f5; }
.member-brand, .member-account { display: flex; align-items: center; gap: 11px; }
.brand-mark { display: grid; width: 39px; height: 39px; place-items: center; color: #fff; background: linear-gradient(145deg, #6485ff, #4164dc); border-radius: 12px; font-size: 19px; font-weight: 800; }
.member-brand > span:last-child, .account-copy { display: flex; flex-direction: column; gap: 3px; }
.member-brand strong { color: #172b4d; font-size: 14px; }
.member-brand small, .account-copy span { color: #8795aa; font-size: 10px; }
.member-account { gap: 9px; }
.account-avatar { display: grid; width: 34px; height: 34px; place-items: center; color: #4f46e5; background: #eef2ff; border-radius: 50%; font-size: 13px; font-weight: 800; }
.account-copy strong { color: #334155; font-size: 11px; }
.member-account button { margin-left: 8px; padding: 8px 11px; color: #64748b; background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; font-size: 10px; cursor: pointer; }
.member-account button:hover { color: #4338ca; background: #f8faff; }
.member-content { width: min(1360px, 100%); margin: 0 auto; padding: 24px; }
.member-footer { padding: 17px 24px; color: #94a3b8; background: #fff; border-top: 1px solid #e2e9f5; font-size: 11px; text-align: center; }

@media (max-width: 700px) {
  .member-topbar { padding: 10px 14px; }
  .account-copy { display: none; }
  .member-account button { margin-left: 0; }
  .member-content { padding: 14px; }
}
</style>
