<script setup lang="ts">
const auth = useAuth()
const route = useRoute()
const email = ref('')
const password = ref('')
const erro = ref('')
const aEntrar = ref(false)

definePageMeta({
  layout: false,
})

async function entrar(): Promise<void> {
  erro.value = ''
  aEntrar.value = true

  try {
    const user = await auth.login(email.value, password.value)
    const redirect = typeof route.query.redirect === 'string'
      ? route.query.redirect
      : ''
    const urlRedirecionamento = redirect.startsWith('/')
      ? new URL(redirect, window.location.origin)
      : null
    const destino = urlRedirecionamento?.origin === window.location.origin
      ? `${urlRedirecionamento.pathname}${urlRedirecionamento.search}${urlRedirecionamento.hash}`
      : user.role === 'admin'
        ? '/'
        : '/my-work'

    await navigateTo(destino)
  } catch (error) {
    console.error('Erro ao iniciar sessão:', error)
    const detalhe =
      typeof error === 'object' &&
      error !== null &&
      'data' in error &&
      typeof error.data === 'object' &&
      error.data !== null &&
      'detail' in error.data &&
      typeof error.data.detail === 'string'
        ? error.data.detail
        : ''
    const statusCode =
      typeof error === 'object' && error !== null && 'statusCode' in error
        ? error.statusCode
        : undefined

    erro.value = statusCode === 401 || !detalhe
      ? 'Não foi possível iniciar sessão. Verifique o email e a palavra-passe.'
      : detalhe
  } finally {
    aEntrar.value = false
  }
}
</script>

<template>
  <main class="login-page">
    <section class="login-card">
      <div class="login-brand">
        <span class="brand-mark">T</span>
        <div><strong>TaskFlow</strong><span>Gestão de trabalho</span></div>
      </div>

      <span class="login-kicker">BEM-VINDO/A DE VOLTA</span>
      <h1>Iniciar sessão</h1>
      <p class="login-description">
        Entre para aceder à sua área de trabalho.
      </p>

      <form class="login-form" @submit.prevent="entrar">
        <label for="email">Email</label>
        <input
          id="email"
          v-model="email"
          type="email"
          autocomplete="username"
          placeholder="nome@exemplo.com"
          required
        />

        <label for="password">Palavra-passe</label>
        <input
          id="password"
          v-model="password"
          type="password"
          autocomplete="current-password"
          placeholder="A sua palavra-passe"
          required
        />

        <p v-if="erro" class="login-error" role="alert">{{ erro }}</p>

        <button type="submit" :disabled="aEntrar">
          {{ aEntrar ? 'A validar...' : 'Entrar na plataforma' }}
        </button>
      </form>

      <p class="login-footnote">
        O acesso é criado por um administrador da plataforma.
      </p>
    </section>
  </main>
</template>

<style scoped>
.login-page {
  display: grid;
  min-height: 100vh;
  padding: 24px;
  place-items: center;
  background:
    radial-gradient(ellipse at 18% 15%, rgb(99 102 241 / 13%), transparent 32%),
    #f4f6fb;
  color: #172b4d;
  font-family: Inter, 'Segoe UI', sans-serif;
}

.login-card {
  width: min(440px, 100%);
  padding: 38px;
  background: #fff;
  border: 1px solid #e5eaf2;
  border-radius: 20px;
  box-shadow: 0 18px 55px rgb(34 57 103 / 10%);
}

.login-brand {
  display: flex;
  align-items: center;
  gap: 11px;
  margin-bottom: 42px;
}

.brand-mark {
  display: grid;
  width: 42px;
  height: 42px;
  place-items: center;
  color: white;
  background: linear-gradient(145deg, #6485ff, #4164dc);
  border-radius: 13px;
  font-size: 21px;
  font-weight: 800;
}

.login-brand > div {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.login-brand strong { font-size: 16px; }
.login-brand > div span { color: #8b9ab1; font-size: 11px; }
.login-kicker { color: #6366f1; font-size: 10px; font-weight: 800; letter-spacing: .12em; }
.login-card h1 { margin: 9px 0 7px; font-size: 28px; letter-spacing: -.04em; }
.login-description { margin: 0 0 26px; color: #8492a8; font-size: 13px; }
.login-form { display: flex; flex-direction: column; gap: 9px; }
.login-form label { margin-top: 9px; color: #334155; font-size: 12px; font-weight: 700; }
.login-form input { min-height: 44px; padding: 0 12px; border: 1px solid #dfe5ef; border-radius: 9px; outline: 0; font-size: 13px; }
.login-form input:focus { border-color: #6366f1; box-shadow: 0 0 0 3px rgb(99 102 241 / 12%); }
.login-form button { min-height: 45px; margin-top: 13px; color: #fff; background: #4f46e5; border: 0; border-radius: 9px; font-size: 13px; font-weight: 750; cursor: pointer; }
.login-form button:disabled { opacity: .65; cursor: wait; }
.login-error { margin: 4px 0 0; color: #b91c1c; font-size: 12px; line-height: 1.5; }
.login-footnote { margin: 24px 0 0; color: #94a3b8; font-size: 11px; text-align: center; }

@media (max-width: 480px) {
  .login-page { padding: 14px; }
  .login-card { padding: 28px 22px; }
  .login-brand { margin-bottom: 32px; }
}
</style>
