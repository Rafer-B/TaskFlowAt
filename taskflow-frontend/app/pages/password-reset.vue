<script setup lang="ts">
const api = useNuxtApp().$api
const email = ref('')
const token = ref('')
const newPassword = ref('')
const confirmingPassword = ref('')
const submitting = ref(false)
const errorMessage = ref('')
const success = ref(false)

definePageMeta({ layout: false })

async function resetPassword(): Promise<void> {
  errorMessage.value = ''
  if (newPassword.value !== confirmingPassword.value) {
    errorMessage.value = 'As palavras-passe não coincidem.'
    return
  }

  submitting.value = true
  try {
    await api('/auth/password-reset', {
      method: 'POST',
      body: {
        email: email.value.trim().toLowerCase(),
        token: token.value.trim(),
        new_password: newPassword.value,
      },
    })
    success.value = true
  } catch (error) {
    console.error('Não foi possível repor a palavra-passe:', error)
    const data = typeof error === 'object' && error !== null && 'data' in error
      ? error.data
      : null
    errorMessage.value =
      typeof data === 'object' && data !== null &&
      'detail' in data && typeof data.detail === 'string'
        ? data.detail
        : 'Não foi possível concluir a reposição. Verifique os dados ou peça um novo token ao administrador.'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <main class="reset-page">
    <section class="reset-card" aria-labelledby="reset-title">
      <NuxtLink class="brand" to="/login" aria-label="TaskFlow — iniciar sessão">
        <span class="brand-mark">T</span>
        <span><strong>TaskFlow</strong><small>RECUPERAÇÃO DE ACESSO</small></span>
      </NuxtLink>

      <template v-if="success">
        <div class="status-icon success-icon" aria-hidden="true">✓</div>
        <h1 id="reset-title">Palavra-passe atualizada</h1>
        <p>A sua palavra-passe foi alterada. Já pode iniciar sessão com a nova credencial.</p>
        <NuxtLink class="submit-button" to="/login">Voltar ao início de sessão</NuxtLink>
      </template>

      <template v-else>
        <div class="status-icon" aria-hidden="true">↻</div>
        <h1 id="reset-title">Recuperar acesso</h1>
        <p>Introduza o token de uso único fornecido pelo administrador da plataforma.</p>

        <form @submit.prevent="resetPassword">
          <label for="reset-email">Endereço de email</label>
          <input id="reset-email" v-model="email" type="email" autocomplete="username" required />

          <label for="reset-token">Token de recuperação</label>
          <input
            id="reset-token"
            v-model="token"
            type="text"
            autocomplete="one-time-code"
            minlength="32"
            maxlength="128"
            required
          />

          <label for="new-password">Nova palavra-passe</label>
          <input
            id="new-password"
            v-model="newPassword"
            type="password"
            autocomplete="new-password"
            minlength="12"
            maxlength="128"
            required
          />

          <label for="confirm-password">Confirmar palavra-passe</label>
          <input
            id="confirm-password"
            v-model="confirmingPassword"
            type="password"
            autocomplete="new-password"
            minlength="12"
            maxlength="128"
            required
          />

          <p v-if="errorMessage" class="error-message" role="alert">{{ errorMessage }}</p>
          <button class="submit-button" type="submit" :disabled="submitting">
            {{ submitting ? 'A atualizar…' : 'Atualizar palavra-passe' }}
          </button>
        </form>

        <NuxtLink class="back-link" to="/login">Voltar ao início de sessão</NuxtLink>
      </template>
    </section>
  </main>
</template>

<style scoped>
.reset-page {
  display: grid;
  min-height: 100vh;
  padding: 24px;
  place-items: center;
  background:
    radial-gradient(ellipse at 10% 10%, rgb(199 210 254 / 45%), transparent 34%),
    #f5f7fc;
  color: #172b4d;
  font-family: var(--tf-font, 'Segoe UI', sans-serif);
}

.reset-card {
  width: min(460px, 100%);
  padding: 38px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 20px;
  box-shadow: 0 24px 70px rgb(32 47 85 / 12%);
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 36px;
  color: inherit;
  text-decoration: none;
}

.brand-mark,
.status-icon {
  display: grid;
  width: 42px;
  height: 42px;
  place-items: center;
  color: #fff;
  background: linear-gradient(145deg, #6485ff, #4164dc);
  border-radius: 13px;
  font-size: 20px;
  font-weight: 800;
}

.brand > span:last-child {
  display: grid;
  gap: 3px;
}

.brand strong { font-size: 17px; }
.brand small { color: #8390a5; font-size: 9px; font-weight: 750; letter-spacing: .1em; }
.status-icon { margin-bottom: 18px; color: #4e57d1; background: #eef0ff; font-size: 22px; }
.success-icon { color: #147d55; background: #e8f7ef; }
h1 { margin: 0; font-size: 25px; letter-spacing: -.03em; }
.reset-card > p { margin: 10px 0 24px; color: #718096; font-size: 13px; line-height: 1.6; }
form { display: grid; gap: 9px; }
label { margin-top: 7px; color: #34445c; font-size: 11px; font-weight: 700; }
input { width: 100%; padding: 11px 12px; color: #263650; background: #fff; border: 1px solid #dce3ed; border-radius: 9px; font: inherit; font-size: 13px; }
input:focus { outline: 3px solid rgb(99 102 241 / 15%); border-color: #6875e5; }
.submit-button { display: inline-flex; min-height: 44px; align-items: center; justify-content: center; margin-top: 12px; padding: 0 16px; color: #fff; background: #4e57d1; border: 0; border-radius: 9px; font: inherit; font-size: 12px; font-weight: 750; text-decoration: none; cursor: pointer; }
.submit-button:hover:not(:disabled) { background: #3e46b8; }
.submit-button:disabled { opacity: .65; cursor: wait; }
.error-message { margin: 8px 0 0; color: #b42318; font-size: 12px; }
.back-link { display: block; width: fit-content; margin: 20px auto 0; color: #4e57d1; font-size: 12px; font-weight: 650; text-decoration: none; }
.back-link:hover { text-decoration: underline; }

@media (max-width: 520px) {
  .reset-card { padding: 28px 22px; }
}
</style>
