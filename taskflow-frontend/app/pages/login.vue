<script setup lang="ts">
import type { AuthUser } from '~/composables/useAuth'
import { homeForRole } from '~/utils/access'

// Gere credenciais, feedback do formulário e destino após autenticação.
const auth = useAuth()
const route = useRoute()
const aAdicionarConta = computed(() => route.query.switchAccount === '1')
const email = ref('')
const password = ref('')
const erro = ref('')
const aEntrar = ref(false)
const mostrarPalavraPasse = ref(false)
const desafioDoisFatores = ref('')
const codigoDoisFatores = ref('')
const metodosDoisFatores = ref<Array<'authenticator' | 'email'>>([])
const metodoDoisFatores = ref<'authenticator' | 'email'>('authenticator')
const codigoEmailEnviado = ref(false)
const aguardaDoisFatores = computed(() => Boolean(desafioDoisFatores.value))

watch(
  () => route.query.email,
  (value) => {
    if (typeof value === 'string') email.value = value
  },
  { immediate: true },
)

definePageMeta({
  layout: false,
})

async function entrar(): Promise<void> {
  erro.value = ''
  aEntrar.value = true

  try {
    if (aguardaDoisFatores.value) {
      const user = metodoDoisFatores.value === 'email'
        ? await auth.verificarLoginPorEmail(
            desafioDoisFatores.value,
            codigoDoisFatores.value.trim(),
          )
        : await auth.verificarLoginDoisFatores(
            desafioDoisFatores.value,
            codigoDoisFatores.value.trim(),
          )
      await navegarAposLogin(user.role)
    } else {
      const resultado = await auth.login(email.value, password.value)
      if (!('role' in resultado)) {
        desafioDoisFatores.value = resultado.challenge_token
        metodosDoisFatores.value = resultado.methods
        metodoDoisFatores.value = 'authenticator'
        codigoDoisFatores.value = ''
      } else {
        await navegarAposLogin(resultado.role)
      }
    }
  } catch (error) {
    // Prefere o detalhe útil da API, mas não expõe erros internos quando não há 401.
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

    erro.value = detalhe || (
      aguardaDoisFatores.value
        ? 'Código inválido ou expirado. Tente novamente.'
        : statusCode === 401 || !detalhe
          ? 'Não foi possível iniciar sessão. Verifique o email e a palavra-passe.'
          : 'Não foi possível iniciar sessão. Tente novamente.'
    )
  } finally {
    aEntrar.value = false
  }
}

async function pedirCodigoPorEmail(): Promise<void> {
  erro.value = ''
  aEntrar.value = true

  try {
    await auth.pedirCodigoDoisFatoresPorEmail(desafioDoisFatores.value)
    metodoDoisFatores.value = 'email'
    codigoEmailEnviado.value = true
    codigoDoisFatores.value = ''
  } catch (error) {
    console.error('Erro ao pedir código de autenticação por email:', error)
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
    erro.value = detalhe || 'Não foi possível enviar o código. Tente novamente.'
  } finally {
    aEntrar.value = false
  }
}

async function navegarAposLogin(role: AuthUser['role']): Promise<void> {
  // Só aceita destinos internos da mesma origem; evita redirecionamentos externos.
  const redirect = typeof route.query.redirect === 'string'
    ? route.query.redirect
    : ''
  const urlRedirecionamento = redirect.startsWith('/')
    ? new URL(redirect, window.location.origin)
    : null
  const destino = urlRedirecionamento?.origin === window.location.origin
    ? `${urlRedirecionamento.pathname}${urlRedirecionamento.search}${urlRedirecionamento.hash}`
    : homeForRole(role)

  await navigateTo(destino)
}

function voltarAoLogin(): void {
  desafioDoisFatores.value = ''
  codigoDoisFatores.value = ''
  metodosDoisFatores.value = []
  metodoDoisFatores.value = 'authenticator'
  codigoEmailEnviado.value = false
  erro.value = ''
}
</script>

<template>
  <main class="login-page">
    <div class="login-shell">
      <section class="welcome-panel" aria-label="Sobre o TaskFlow">
        <div class="welcome-orb orb-one"></div>
        <div class="welcome-orb orb-two"></div>

        <NuxtLink class="login-brand" to="/login" aria-label="TaskFlow — início de sessão">
          <span class="brand-mark" aria-hidden="true">
            <svg viewBox="0 0 32 32" fill="none">
              <path d="M8 9.5h16M8 16h10M8 22.5h7" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" />
              <path d="m20.5 20.5 2 2 4-4" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </span>
          <span class="brand-copy">
            <strong>TaskFlow</strong>
            <small>PROJETOS EM MOVIMENTO</small>
          </span>
        </NuxtLink>

        <div class="welcome-copy">
          <span class="welcome-kicker"><span></span> O SEU TRABALHO, EM EQUIPA</span>
          <h2>Ideias que avançam.<br /><span>Projetos que acontecem.</span></h2>
          <p>
            Reúna a equipa, acompanhe cada etapa e transforme planos em
            resultados — tudo num só lugar.
          </p>
        </div>

        <div class="preview-board" aria-hidden="true">
          <div class="preview-board-heading">
            <div>
              <span class="preview-eyebrow">VISÃO DO PROJETO</span>
              <strong>Website da equipa</strong>
            </div>
            <span class="preview-menu">•••</span>
          </div>
          <div class="preview-progress">
            <span><i></i></span>
            <small>Progresso <b>68%</b></small>
          </div>
          <div class="preview-columns">
            <div class="preview-column">
              <span class="column-label"><i class="dot-todo"></i> A FAZER <b>2</b></span>
              <div class="preview-task"><i class="task-icon icon-violet"></i><span>Definir objetivos</span></div>
              <div class="preview-task"><i class="task-icon icon-amber"></i><span>Rever conteúdos</span></div>
            </div>
            <div class="preview-column">
              <span class="column-label"><i class="dot-progress"></i> EM CURSO <b>3</b></span>
              <div class="preview-task"><i class="task-icon icon-blue"></i><span>Preparar protótipo</span></div>
              <div class="preview-task"><i class="task-icon icon-green"></i><span>Alinhar a equipa</span></div>
            </div>
          </div>
          <div class="preview-team">
            <div class="team-avatars">
              <span>A</span><span>M</span><span>R</span><span>+2</span>
            </div>
            <span>Equipa a trabalhar em conjunto</span>
            <svg viewBox="0 0 20 20" fill="none"><path d="M4 10h11m0 0-4-4m4 4-4 4" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" /></svg>
          </div>
        </div>

        <div class="welcome-footer">
          <span class="footer-lock" aria-hidden="true">
            <svg viewBox="0 0 20 20" fill="none"><rect x="4" y="8.5" width="12" height="9" rx="2" stroke="currentColor" stroke-width="1.5" /><path d="M6.5 8.5V6a3.5 3.5 0 0 1 7 0v2.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" /></svg>
          </span>
          Um espaço seguro para a sua equipa
        </div>
      </section>

      <section class="form-panel" aria-labelledby="login-title">
        <div class="form-panel-top">
          <span class="mobile-brand-mark" aria-hidden="true">T</span>
          <span class="secure-label">
            <svg viewBox="0 0 20 20" fill="none" aria-hidden="true"><rect x="4" y="8.5" width="12" height="9" rx="2" stroke="currentColor" stroke-width="1.5" /><path d="M6.5 8.5V6a3.5 3.5 0 0 1 7 0v2.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" /></svg>
            ACESSO SEGURO
          </span>
        </div>

        <div class="form-intro">
          <span class="login-kicker">{{ aguardaDoisFatores ? 'SEGUNDO FATOR' : aAdicionarConta ? 'ADICIONAR CONTA' : 'BEM-VINDO/A DE VOLTA' }}</span>
          <h1 id="login-title">{{ aguardaDoisFatores ? 'Confirme a sua identidade' : aAdicionarConta ? 'Entre noutra conta' : 'Entre na sua conta' }}</h1>
          <p>{{ aguardaDoisFatores ? metodoDoisFatores === 'email' ? 'Introduza o código de seis dígitos enviado para o email associado à conta.' : 'Introduza o código da sua app autenticadora ou um código de recuperação.' : aAdicionarConta ? 'A conta atual mantém-se disponível para alternar mais tarde.' : 'Continue de onde a sua equipa precisa de si.' }}</p>
        </div>

        <form class="login-form" @submit.prevent="entrar">
          <template v-if="!aguardaDoisFatores">
            <label for="email">Endereço de email</label>
            <div class="input-wrap">
              <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
                <rect x="2.75" y="4.25" width="14.5" height="11.5" rx="2.5" stroke="currentColor" stroke-width="1.5" />
                <path d="m4 6 6 4.5L16 6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
              <input
                id="email"
                v-model="email"
                type="email"
                autocomplete="username"
                placeholder="nome@empresa.com"
                required
                :disabled="aEntrar"
              />
            </div>

            <div class="password-label-row">
              <label for="password">Palavra-passe</label>
            </div>
            <div class="input-wrap">
              <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
                <rect x="3.25" y="8" width="13.5" height="9" rx="2.25" stroke="currentColor" stroke-width="1.5" />
                <path d="M6.25 8V5.75a3.75 3.75 0 0 1 7.5 0V8M10 11.5v2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
              </svg>
              <input
                id="password"
                v-model="password"
                :type="mostrarPalavraPasse ? 'text' : 'password'"
                autocomplete="current-password"
                placeholder="Introduza a sua palavra-passe"
                required
                :disabled="aEntrar"
              />
              <button
                class="password-toggle"
                type="button"
                :aria-label="mostrarPalavraPasse ? 'Ocultar palavra-passe' : 'Mostrar palavra-passe'"
                :aria-pressed="mostrarPalavraPasse"
                @click="mostrarPalavraPasse = !mostrarPalavraPasse"
              >
                <svg v-if="mostrarPalavraPasse" viewBox="0 0 20 20" fill="none" aria-hidden="true">
                  <path d="M2.5 10s2.7-5 7.5-5 7.5 5 7.5 5-2.7 5-7.5 5-7.5-5-7.5-5Z" stroke="currentColor" stroke-width="1.5" />
                  <circle cx="10" cy="10" r="2.1" stroke="currentColor" stroke-width="1.5" />
                </svg>
                <svg v-else viewBox="0 0 20 20" fill="none" aria-hidden="true">
                  <path d="m3 3 14 14M8.6 5.2A7.6 7.6 0 0 1 10 5c4.8 0 7.5 5 7.5 5a12 12 0 0 1-2.2 2.8M5.2 5.8C3.4 7.1 2.5 10 2.5 10s2.7 5 7.5 5c.8 0 1.6-.2 2.3-.4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
              </button>
            </div>
          </template>
          <template v-else>
            <label for="two-factor-code">{{ metodoDoisFatores === 'email' ? 'Código enviado por email' : 'Código da app ou de recuperação' }}</label>
            <div class="input-wrap">
              <input
                id="two-factor-code"
                v-model="codigoDoisFatores"
                type="text"
                :inputmode="metodoDoisFatores === 'email' ? 'numeric' : undefined"
                autocomplete="one-time-code"
                :placeholder="metodoDoisFatores === 'email' ? 'Introduza o código enviado por email' : 'Código de seis dígitos ou de recuperação'"
                required
                :disabled="aEntrar"
              />
            </div>
            <p v-if="codigoEmailEnviado" class="login-info" role="status">
              Enviámos um código para o email associado à sua conta. O código expira em 5 minutos.
            </p>
            <button
              v-if="metodosDoisFatores.includes('email') && metodoDoisFatores === 'authenticator'"
              class="factor-method-button"
              type="button"
              :disabled="aEntrar"
              @click="pedirCodigoPorEmail"
            >
              {{ aEntrar ? 'A enviar...' : 'Enviar código por email' }}
            </button>
            <button
              v-else-if="metodosDoisFatores.includes('email') && metodoDoisFatores === 'email'"
              class="factor-method-button"
              type="button"
              :disabled="aEntrar"
              @click="metodoDoisFatores = 'authenticator'; codigoEmailEnviado = false; codigoDoisFatores = ''; erro = ''"
            >
              Usar app autenticadora ou código de recuperação
            </button>
            <p v-else class="login-info" role="status">
              O código por email não está disponível neste servidor. A autenticação continua disponível pela app ou por um código de recuperação.
            </p>
          </template>

          <p v-if="erro" class="login-error" role="alert">
            <svg viewBox="0 0 20 20" fill="none" aria-hidden="true"><circle cx="10" cy="10" r="7.5" stroke="currentColor" stroke-width="1.5" /><path d="M10 6v4.5m0 3h.01" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" /></svg>
            {{ erro }}
          </p>

          <button class="submit-button" type="submit" :disabled="aEntrar">
            <span>{{ aEntrar ? 'A validar os seus dados...' : aguardaDoisFatores ? 'Verificar código' : 'Iniciar sessão' }}</span>
            <svg v-if="!aEntrar" viewBox="0 0 20 20" fill="none" aria-hidden="true"><path d="M4 10h11m0 0-4-4m4 4-4 4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" /></svg>
            <span v-else class="button-spinner" aria-hidden="true"></span>
          </button>
          <button
            v-if="aguardaDoisFatores"
            class="secondary-login-button"
            type="button"
            :disabled="aEntrar"
            @click="voltarAoLogin"
          >
            Voltar
          </button>
        </form>

        <NuxtLink v-if="!aguardaDoisFatores" class="recovery-link" to="/password-reset">
          Esqueceu-se da palavra-passe?
        </NuxtLink>

        <div class="login-divider"><span></span><i>INFORMAÇÃO</i><span></span></div>
        <div class="account-note">
          <span class="note-icon" aria-hidden="true">
            <svg viewBox="0 0 20 20" fill="none"><circle cx="10" cy="6.25" r="2.5" stroke="currentColor" stroke-width="1.5" /><path d="M4.5 16v-1.25a5.5 5.5 0 0 1 11 0V16h-11Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round" /></svg>
          </span>
          <p>
            Ainda não tem uma conta?
            <span>Peça ao administrador da plataforma para criar o seu acesso.</span>
          </p>
        </div>

        <footer class="form-footer">
          <span>© {{ new Date().getFullYear() }} TaskFlow</span>
          <span><i></i> Plataforma de trabalho colaborativo</span>
        </footer>
      </section>
    </div>
  </main>
</template>

<style scoped>
.login-page {
  display: grid;
  min-height: 100vh;
  min-height: 100svh;
  padding: clamp(16px, 4vw, 52px);
  place-items: center;
  overflow: hidden;
  background:
    radial-gradient(ellipse at 8% 8%, rgb(199 210 254 / 45%), transparent 32%),
    radial-gradient(ellipse at 94% 95%, rgb(224 231 255 / 65%), transparent 30%),
    #f5f7fc;
  color: #172b4d;
  font-family: var(--tf-font, 'Segoe UI', sans-serif);
}

.recovery-link {
  display: block;
  width: fit-content;
  margin: 16px auto 0;
  color: #4e57d1;
  font-size: 12px;
  font-weight: 650;
  text-decoration: none;
}

.recovery-link:hover {
  color: #3730a3;
  text-decoration: underline;
}

.login-shell {
  display: grid;
  width: min(1060px, 100%);
  min-height: 650px;
  grid-template-columns: 1.04fr .96fr;
  overflow: hidden;
  background: #fff;
  border: 1px solid rgb(226 232 240 / 85%);
  border-radius: 26px;
  box-shadow: 0 32px 90px rgb(32 47 85 / 14%), 0 5px 16px rgb(32 47 85 / 5%);
}

.welcome-panel {
  position: relative;
  display: flex;
  min-width: 0;
  flex-direction: column;
  padding: 39px 42px 25px;
  overflow: hidden;
  color: #fff;
  background:
    radial-gradient(ellipse at 84% 7%, rgb(122 135 255 / 26%), transparent 34%),
    linear-gradient(150deg, #17264a 0%, #202e5d 54%, #2f3c79 100%);
}

.welcome-panel::before,
.welcome-panel::after {
  position: absolute;
  width: 340px;
  height: 340px;
  border: 1px solid rgb(255 255 255 / 7%);
  border-radius: 50%;
  content: '';
  pointer-events: none;
}

.welcome-panel::before {
  right: -210px;
  top: 170px;
  box-shadow: 0 0 0 30px rgb(255 255 255 / 2.5%), 0 0 0 62px rgb(255 255 255 / 2%);
}

.welcome-panel::after {
  left: -255px;
  bottom: -240px;
  width: 390px;
  height: 390px;
}

.welcome-orb {
  position: absolute;
  border-radius: 50%;
  pointer-events: none;
}

.orb-one {
  top: 285px;
  right: 12%;
  width: 7px;
  height: 7px;
  background: #72e0c3;
  box-shadow: 0 0 20px 5px rgb(114 224 195 / 35%);
}

.orb-two {
  top: 148px;
  right: 16%;
  width: 4px;
  height: 4px;
  background: #c4bfff;
  box-shadow: 0 0 15px 4px rgb(196 191 255 / 30%);
}

.login-brand {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  align-self: flex-start;
  gap: 12px;
  color: #fff;
  text-decoration: none;
}

.brand-mark {
  display: grid;
  width: 45px;
  height: 45px;
  place-items: center;
  color: #fff;
  background: linear-gradient(145deg, #818cf8, #6366f1);
  border: 1px solid rgb(255 255 255 / 18%);
  border-radius: 14px;
  box-shadow: 0 7px 18px rgb(11 19 47 / 24%);
}

.brand-mark svg { width: 27px; height: 27px; }

.brand-copy {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.brand-copy strong { color: #fff; font-size: 17px; font-weight: 750; letter-spacing: -.035em; }
.brand-copy small { color: #aeb9db; font-size: 8px; font-weight: 700; letter-spacing: .15em; }

.welcome-copy {
  position: relative;
  z-index: 1;
  margin: 53px 0 28px;
}

.welcome-kicker {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #b7c5ed;
  font-size: 9px;
  font-weight: 750;
  letter-spacing: .13em;
}

.welcome-kicker > span {
  width: 6px;
  height: 6px;
  background: #6ee7c2;
  border-radius: 50%;
  box-shadow: 0 0 12px rgb(110 231 194 / 55%);
}

.welcome-copy h2 {
  margin: 15px 0 12px;
  font-size: clamp(27px, 3.2vw, 36px);
  font-weight: 650;
  letter-spacing: -.055em;
  line-height: 1.17;
}

.welcome-copy h2 span { color: #a9b5ff; }

.welcome-copy p {
  max-width: 365px;
  margin: 0;
  color: #c3cee9;
  font-size: 12px;
  line-height: 1.75;
}

.preview-board {
  position: relative;
  z-index: 1;
  margin-top: auto;
  padding: 18px 18px 13px;
  color: #33415e;
  background: rgb(255 255 255 / 97%);
  border: 1px solid rgb(255 255 255 / 55%);
  border-radius: 15px;
  box-shadow: 0 14px 34px rgb(7 14 41 / 24%);
  transform: rotate(-1deg);
}

.preview-board-heading,
.preview-team,
.preview-progress {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.preview-board-heading > div { display: flex; flex-direction: column; gap: 4px; }
.preview-eyebrow { color: #8a96ad; font-size: 7px; font-weight: 800; letter-spacing: .13em; }
.preview-board-heading strong { color: #253452; font-size: 12px; font-weight: 750; }
.preview-menu { color: #8e9ab0; font-size: 13px; letter-spacing: 2px; }

.preview-progress { gap: 12px; margin: 13px 0 14px; }
.preview-progress > span { height: 5px; flex: 1; overflow: hidden; background: #edf0f7; border-radius: 10px; }
.preview-progress > span i { display: block; width: 68%; height: 100%; background: linear-gradient(90deg, #818cf8, #5b65df); border-radius: inherit; }
.preview-progress small { color: #8390a7; font-size: 8px; white-space: nowrap; }
.preview-progress b { margin-left: 4px; color: #4f46e5; font-size: 9px; }

.preview-columns { display: grid; grid-template-columns: 1fr 1fr; gap: 11px; }
.preview-column { display: flex; flex-direction: column; gap: 6px; }
.column-label { display: flex; align-items: center; gap: 5px; margin-bottom: 2px; color: #78859e; font-size: 7px; font-weight: 800; letter-spacing: .05em; }
.column-label b { display: grid; width: 14px; height: 14px; margin-left: auto; place-items: center; color: #748099; background: #f0f2f7; border-radius: 5px; font-size: 7px; }
.column-label > i { width: 5px; height: 5px; border-radius: 50%; }
.dot-todo { background: #a5b0c2; }
.dot-progress { background: #7181ed; }

.preview-task { display: flex; min-height: 30px; align-items: center; gap: 7px; padding: 0 8px; background: #f8f9fc; border: 1px solid #eef0f5; border-radius: 6px; color: #54627d; font-size: 8px; font-weight: 600; }
.task-icon { width: 5px; height: 14px; flex: 0 0 5px; border-radius: 4px; }
.icon-violet { background: #9287ed; }
.icon-amber { background: #edbd67; }
.icon-blue { background: #6d8bed; }
.icon-green { background: #55c5a0; }

.preview-team { justify-content: flex-start; gap: 8px; padding-top: 12px; margin-top: 11px; border-top: 1px solid #edf0f5; color: #8490a6; font-size: 8px; }
.team-avatars { display: flex; padding-left: 2px; }
.team-avatars span { display: grid; width: 19px; height: 19px; margin-left: -3px; place-items: center; color: #fff; background: #7b85df; border: 2px solid #fff; border-radius: 50%; font-size: 6px; font-weight: 800; }
.team-avatars span:nth-child(2) { background: #4eb89b; }
.team-avatars span:nth-child(3) { background: #e29b63; }
.team-avatars span:nth-child(4) { color: #5b64c7; background: #e8eaff; }
.preview-team > svg { width: 14px; height: 14px; margin-left: auto; color: #6573dc; }

.welcome-footer { position: relative; z-index: 1; display: flex; align-items: center; gap: 7px; margin-top: 22px; color: #aeb9d5; font-size: 9px; }
.footer-lock { display: grid; width: 20px; height: 20px; place-items: center; color: #aeb9d5; background: rgb(255 255 255 / 7%); border: 1px solid rgb(255 255 255 / 10%); border-radius: 6px; }
.footer-lock svg { width: 13px; height: 13px; }

.form-panel {
  display: flex;
  min-width: 0;
  flex-direction: column;
  padding: 41px clamp(30px, 5vw, 59px) 25px;
  background: #fff;
}

.form-panel-top { display: flex; min-height: 42px; align-items: center; justify-content: flex-end; }
.secure-label { display: inline-flex; align-items: center; gap: 6px; color: #8793a8; font-size: 8px; font-weight: 750; letter-spacing: .1em; }
.secure-label svg { width: 15px; height: 15px; color: #7583a0; }
.mobile-brand-mark { display: none; }

.form-intro { margin: 65px 0 29px; }
.login-kicker { color: #5e61dc; font-size: 9px; font-weight: 800; letter-spacing: .14em; }
.form-intro h1 { margin: 11px 0 8px; color: #202c46; font-size: clamp(25px, 3vw, 31px); font-weight: 700; letter-spacing: -.05em; line-height: 1.2; }
.form-intro p { margin: 0; color: #8792a6; font-size: 13px; line-height: 1.6; }

.login-form { display: flex; flex-direction: column; gap: 9px; }
.login-form label { color: #394761; font-size: 13px; font-weight: 650; }
.password-label-row { display: flex; align-items: center; justify-content: space-between; margin-top: 9px; }

.input-wrap {
  display: flex;
  min-height: 48px;
  align-items: center;
  gap: 10px;
  padding: 0 13px;
  color: #9aa5b8;
  background: #fbfcfe;
  border: 1px solid #e1e6ef;
  border-radius: 10px;
  transition: border-color .18s ease, box-shadow .18s ease, background .18s ease;
}

.input-wrap:focus-within { background: #fff; border-color: #7778e8; box-shadow: 0 0 0 3px rgb(99 102 241 / 10%); }
.input-wrap > svg { width: 17px; height: 17px; flex: 0 0 17px; }
.input-wrap input { width: 100%; min-width: 0; height: 46px; padding: 0; color: #293650; background: transparent; border: 0; outline: 0; font-size: 14px; }
.input-wrap input::placeholder { color: #aab3c2; }
.input-wrap input:disabled { opacity: .7; }

.password-toggle { display: grid; width: 30px; height: 30px; flex: 0 0 30px; place-items: center; color: #8e9aaf; background: transparent; border-radius: 7px; cursor: pointer; }
.password-toggle:hover { color: #4f46e5; background: #f0f1ff; }
.password-toggle:focus-visible { outline: 3px solid #c7d2fe; outline-offset: 1px; }
.password-toggle svg { width: 17px; height: 17px; }

.login-error { display: flex; align-items: flex-start; gap: 8px; margin: 4px 0 0; padding: 10px 11px; color: #a53636; background: #fff4f3; border: 1px solid #f6d5d2; border-radius: 8px; font-size: 10px; line-height: 1.5; }
.login-error svg { width: 15px; height: 15px; flex: 0 0 15px; margin-top: 1px; }
.login-info { margin: 0; color: #5363a5; font-size: 11px; line-height: 1.5; }
.factor-method-button { justify-self: start; padding: 2px 0; color: #5146c8; background: transparent; border: 0; font-size: 11px; font-weight: 650; text-align: left; cursor: pointer; }
.factor-method-button:hover:not(:disabled) { color: #3730a3; text-decoration: underline; }
.factor-method-button:focus-visible { outline: 3px solid #c7d2fe; outline-offset: 3px; border-radius: 3px; }
.factor-method-button:disabled { opacity: .6; cursor: wait; }

.submit-button { display: flex; min-height: 48px; align-items: center; justify-content: center; gap: 9px; margin-top: 13px; color: #fff; background: linear-gradient(105deg, var(--tf-primary), var(--tf-primary-hover)); border: 1px solid var(--tf-primary-hover); border-radius: 10px; box-shadow: 0 7px 18px rgb(79 70 229 / 26%); font-size: 14px; font-weight: 700; cursor: pointer; transition: transform .18s ease, box-shadow .18s ease, background .18s ease; }
.submit-button:hover:not(:disabled) { transform: translateY(-1px); background: linear-gradient(105deg, var(--tf-primary-hover), #3730a3); box-shadow: 0 10px 22px rgb(79 70 229 / 32%); }
.submit-button:focus-visible { outline: 3px solid #c7d2fe; outline-offset: 3px; }
.submit-button:disabled { opacity: .75; cursor: wait; }
.submit-button > svg { width: 17px; height: 17px; }
.secondary-login-button { min-height: 40px; margin-top: 5px; color: #64708a; background: transparent; border: 0; border-radius: 8px; font-size: 12px; font-weight: 650; cursor: pointer; }
.secondary-login-button:hover:not(:disabled) { color: #4338ca; background: #f4f5ff; }
.secondary-login-button:focus-visible { outline: 3px solid #c7d2fe; outline-offset: 2px; }
.secondary-login-button:disabled { opacity: .6; cursor: wait; }
.button-spinner { width: 14px; height: 14px; border: 2px solid rgb(255 255 255 / 35%); border-top-color: #fff; border-radius: 50%; animation: spin .75s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.login-divider { display: flex; align-items: center; gap: 10px; margin: 26px 0 17px; }
.login-divider span { height: 1px; flex: 1; background: #edf0f5; }
.login-divider i { color: #a1aabc; font-size: 7px; font-style: normal; font-weight: 750; letter-spacing: .14em; }

.account-note { display: flex; align-items: flex-start; gap: 10px; padding: 13px; background: #f7f8ff; border: 1px solid #eceeff; border-radius: 10px; }
.note-icon { display: grid; width: 26px; height: 26px; flex: 0 0 26px; place-items: center; color: #5d63d6; background: #eceeff; border-radius: 8px; }
.note-icon svg { width: 16px; height: 16px; }
.account-note p { display: flex; flex-direction: column; gap: 4px; margin: 1px 0 0; color: #45516a; font-size: 9px; font-weight: 700; line-height: 1.45; }
.account-note p span { color: #8993a6; font-size: 8px; font-weight: 450; }

.form-footer { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-top: auto; padding-top: 25px; color: #9aa4b6; font-size: 8px; }
.form-footer > span:last-child { display: inline-flex; align-items: center; gap: 5px; }
.form-footer i { width: 5px; height: 5px; background: #67caa9; border-radius: 50%; }

@media (max-width: 760px) {
  .login-page { padding: 16px; }
  .login-shell { width: min(500px, 100%); min-height: 0; grid-template-columns: 1fr; border-radius: 22px; }
  .welcome-panel { display: none; }
  .form-panel { min-height: min(700px, calc(100svh - 32px)); padding: 27px clamp(24px, 7vw, 42px) 21px; }
  .form-panel-top { justify-content: space-between; }
  .mobile-brand-mark { display: grid; width: 38px; height: 38px; place-items: center; color: #fff; background: linear-gradient(145deg, #6485ff, #4164dc); border-radius: 12px; font-size: 18px; font-weight: 800; }
  .form-intro { margin: clamp(42px, 12vh, 85px) 0 28px; }
}

@media (max-width: 380px) {
  .login-page { padding: 10px; }
  .login-shell { border-radius: 17px; }
  .form-panel { min-height: calc(100svh - 20px); padding: 19px 19px 17px; }
  .form-intro h1 { font-size: 25px; }
  .form-footer { font-size: 7px; }
}

@media (prefers-reduced-motion: reduce) {
  .input-wrap,
  .submit-button { transition: none; }
  .button-spinner { animation-duration: 1.5s; }
}
</style>
