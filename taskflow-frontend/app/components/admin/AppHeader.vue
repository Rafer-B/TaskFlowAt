
<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import type { AuthUser } from '~/composables/useAuth'
import { useDashboardData } from '~/composables/useDashboardData'
import { diffInDays, parseISODay, toISODay } from '~/utils/dates'

// Junta pesquisa, alertas, navegação e fotografia do utilizador autenticado.
const route = useRoute()
const router = useRouter()
const auth = useAuth()
const dashboard = useDashboardData(new Date())
const dashboardCarregando = dashboard.carregando
const dashboardErro = dashboard.erro
const config = useRuntimeConfig()
const apiBase = String(config.public.apiBase)
const api = useNuxtApp().$api
const avatarUrl = computed(() =>
  obterUrlAvatar(auth.user.value?.avatar_url, apiBase),
)
const avatarFalhou = ref(false)
const fotografiaAEnviar = ref(false)
const mensagemFotografia = ref('')
const erroFotografia = ref(false)

watch(avatarUrl, () => {
  avatarFalhou.value = false
})

defineProps<{
  title: string
}>()

const emit = defineEmits<{
  toggleSidebar: []
}>()

const searchQuery = ref('')
const searchInput = ref<HTMLInputElement | null>(null)
const headerRef = ref<HTMLElement | null>(null)
const mostrarPesquisa = ref(false)
const mostrarNotificacoes = ref(false)
const idsNotificacoesLidas = ref<Set<string>>(new Set())
const estadoLeituraCarregado = ref(false)
const hojeISO = computed(() => toISODay(new Date()))

interface ResultadoPesquisa {
  id: string
  title: string
  subtitle: string
  kind: string
  to: string
}

interface Notificacao {
  id: string
  title: string
  description: string
  kind: 'Bloqueio' | 'Atraso' | 'Inatividade' | 'Tarefa'
  to: string
  persisted?: boolean
  read_at?: string | null
}

const notificacoesPersistentes = ref<Notificacao[]>([])
const notificacoesPersistentesNaoLidas = ref(0)

const resultadosPesquisa = computed<ResultadoPesquisa[]>(() => {
  // A pesquisa localiza entidades já carregadas e limita a lista para manter o painel compacto.
  const termo = searchQuery.value.trim().toLocaleLowerCase('pt-PT')
  if (!termo) return []

  const resultados: ResultadoPesquisa[] = []
  for (const task of dashboard.tasks) {
    const texto = `${task.title} ${task.project} ${task.responsible}`.toLocaleLowerCase('pt-PT')
    if (texto.includes(termo)) {
      resultados.push({
        id: `task-${task.id}`,
        title: task.title,
        subtitle: `${task.project} · ${task.responsible}`,
        kind: 'Tarefa',
        to: `/tasks?taskId=${task.id}`,
      })
    }
  }
  for (const project of dashboard.projects) {
    if (project.name.toLocaleLowerCase('pt-PT').includes(termo)) {
      resultados.push({
        id: `project-${project.id}`,
        title: project.name,
        subtitle: `Projeto · ${project.status}`,
        kind: 'Projeto',
        to: `/projects?search=${encodeURIComponent(searchQuery.value.trim())}`,
      })
    }
  }
  for (const user of dashboard.users) {
    if (
      user.name.toLocaleLowerCase('pt-PT').includes(termo) ||
      user.email.toLocaleLowerCase('pt-PT').includes(termo)
    ) {
      resultados.push({
        id: `user-${user.id}`,
        title: user.name,
        subtitle: user.email,
        kind: 'Utilizador',
        to: `/users?userId=${user.id}`,
      })
    }
  }

  return resultados.slice(0, 8)
})

const notificacoesLocais = computed<Notificacao[]>(() => {
  // Os alertas cobrem apenas projetos ativos e priorizam bloqueios sobre atrasos e inatividade.
  const projectIds = new Set(
    dashboard.projects
      .filter((project) => project.status === 'Ativo')
      .map((project) => project.id),
  )
  const items: Notificacao[] = []

  for (const task of dashboard.tasks) {
    if (!projectIds.has(task.projectId) || task.status === 'Concluída') continue
    const overdueDays = task.dueDate
      ? diffInDays(parseISODay(task.dueDate), parseISODay(hojeISO.value))
      : 0

    if (task.status === 'Bloqueada') {
      items.push({
        id: `blocked-${task.id}`,
        title: task.title,
        description: `Tarefa bloqueada · ${task.project}`,
        kind: 'Bloqueio',
        to: `/tasks?taskId=${task.id}`,
      })
    } else if (overdueDays > 0) {
      items.push({
        id: `overdue-${task.id}`,
        title: task.title,
        description: `Prazo ultrapassado há ${overdueDays} ${overdueDays === 1 ? 'dia' : 'dias'} · ${task.project}`,
        kind: 'Atraso',
        to: `/tasks?taskId=${task.id}`,
      })
    }
  }

  for (const project of dashboard.projects) {
    if (project.status !== 'Ativo') continue
    const activityDates = [
      project.createdAt,
      project.updatedAt,
      ...dashboard.tasks
        .filter((task) => task.projectId === project.id)
        .flatMap((task) => [task.createdAt, task.updatedAt]),
    ]
      .filter((date): date is string => Boolean(date))
      .map((date) => date.slice(0, 10))
      .sort()
    const lastActivity = activityDates.at(-1)
    if (!lastActivity) continue

    const inactiveDays = diffInDays(
      parseISODay(lastActivity),
      parseISODay(hojeISO.value),
    )
    if (inactiveDays < 7) continue

    items.push({
      id: `inactive-${project.id}`,
      title: project.name,
      description: `Sem atividade há ${inactiveDays} dias`,
      kind: 'Inatividade',
      to: `/projects?search=${encodeURIComponent(project.name)}`,
    })
  }

  return items.sort((a, b) => {
    const priority: Record<Notificacao['kind'], number> = {
      Bloqueio: 0,
      Atraso: 1,
      Inatividade: 2,
      Tarefa: 3,
    }
    return priority[a.kind] - priority[b.kind]
  })
})

const notificacoes = computed(() => [
  ...notificacoesPersistentes.value,
  ...notificacoesLocais.value,
])

const notificacoesNaoLidas = computed(() =>
  notificacoesPersistentesNaoLidas.value +
  notificacoesLocais.value.filter(
    (item) => !idsNotificacoesLidas.value.has(item.id),
  ).length,
)

const totalNaoLidas = computed(() =>
  estadoLeituraCarregado.value ? notificacoesNaoLidas.value : 0,
)

function chaveLeituraNotificacoes(userId: string): string {
  return `taskflow-notificacoes-lidas:${userId}`
}

watch(
  () => auth.user.value?.id,
  (userId) => {
    if (!import.meta.client) return

    if (userId == null) {
      idsNotificacoesLidas.value = new Set()
      notificacoesPersistentes.value = []
      notificacoesPersistentesNaoLidas.value = 0
      estadoLeituraCarregado.value = true
      return
    }

    estadoLeituraCarregado.value = false
    try {
      const guardado = localStorage.getItem(chaveLeituraNotificacoes(userId))
      const parsed: unknown = guardado ? JSON.parse(guardado) : []
      idsNotificacoesLidas.value = new Set(
        Array.isArray(parsed)
          ? parsed.filter((id): id is string => typeof id === 'string')
          : [],
      )
    } catch (error) {
      console.error('Não foi possível carregar o estado das notificações:', error)
      idsNotificacoesLidas.value = new Set()
    } finally {
      estadoLeituraCarregado.value = true
    }

    void Promise.all([
      api<{
        id: string
        title: string
        message: string
        target: string
        read_at: string | null
      }[]>('/notifications/?limit=30'),
      api<{ count: number }>('/notifications/unread-count'),
    ])
      .then(([items, unread]) => {
        notificacoesPersistentes.value = items.map((item) => ({
          id: item.id,
          title: item.title,
          description: item.message,
          kind: 'Tarefa',
          to: item.target,
          persisted: true,
          read_at: item.read_at,
        }))
        notificacoesPersistentesNaoLidas.value = unread.count
      })
      .catch((error: unknown) => {
        console.error('Não foi possível carregar as notificações persistentes:', error)
      })
  },
  { immediate: true },
)

function fecharPainel(): void {
  mostrarPesquisa.value = false
  mostrarNotificacoes.value = false
}

function notificacaoLida(item: Notificacao): boolean {
  return item.persisted
    ? item.read_at != null
    : idsNotificacoesLidas.value.has(item.id)
}

async function marcarNotificacaoComoLida(item: Notificacao): Promise<void> {
  if (item.persisted) {
    try {
      const atualizada = await api<{ read_at: string | null }>(
        `/notifications/${item.id}/read`,
        { method: 'POST' },
      )
      if (item.read_at == null) {
        notificacoesPersistentesNaoLidas.value = Math.max(
          0,
          notificacoesPersistentesNaoLidas.value - 1,
        )
      }
      item.read_at = atualizada.read_at
    } catch (error) {
      console.error('Não foi possível marcar a notificação como lida:', error)
    }
    return
  }

  idsNotificacoesLidas.value = new Set(idsNotificacoesLidas.value).add(item.id)
  const userId = auth.user.value?.id
  if (userId == null) return

  try {
    localStorage.setItem(
      chaveLeituraNotificacoes(userId),
      JSON.stringify([...idsNotificacoesLidas.value]),
    )
  } catch (error) {
    console.error('Não foi possível guardar o estado das notificações:', error)
  }
}

async function abrirDestino(destino: string): Promise<void> {
  const destinoResolvido = router.resolve(destino)
  fecharPainel()
  await router.push({
    path: destinoResolvido.path,
    query: {
      ...destinoResolvido.query,
      abrir: String(Date.now()),
    },
  })
}

async function abrirNotificacao(item: Notificacao): Promise<void> {
  await marcarNotificacaoComoLida(item)
  await abrirDestino(item.to)
}

function abrirPrimeiroResultado(): void {
  const primeiroResultado = resultadosPesquisa.value[0]
  if (primeiroResultado) void abrirDestino(primeiroResultado.to)
}

function tratarAtalhos(event: KeyboardEvent): void {
  // Ctrl/Cmd+K foca a pesquisa; Escape fecha os painéis sem navegar.
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
    event.preventDefault()
    mostrarPesquisa.value = true
    mostrarNotificacoes.value = false
    searchInput.value?.focus()
  } else if (event.key === 'Escape') {
    fecharPainel()
    searchInput.value?.blur()
  }
}

function tratarCliqueFora(event: MouseEvent): void {
  if (
    event.target instanceof Node &&
    !headerRef.value?.contains(event.target)
  ) {
    fecharPainel()
  }
}

onMounted(() => {
  // Os listeners globais são removidos ao desmontar o cabeçalho para evitar acumulação.
  window.addEventListener('keydown', tratarAtalhos)
  document.addEventListener('click', tratarCliqueFora)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', tratarAtalhos)
  document.removeEventListener('click', tratarCliqueFora)
})

function obterMensagemErro(error: unknown): string {
  if (typeof error === 'object' && error !== null && 'data' in error) {
    const data = error.data
    if (
      typeof data === 'object' &&
      data !== null &&
      'detail' in data &&
      typeof data.detail === 'string'
    ) {
      return data.detail
    }
  }

  if (error instanceof Error) return error.message
  return 'Ocorreu um erro ao comunicar com a API.'
}

async function carregarFotografia(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  mensagemFotografia.value = ''

  if (!file || !auth.user.value) return

  // Valida o formato e o limite de 5 MB antes do envio multipart.
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
    erroFotografia.value = true
    mensagemFotografia.value = 'Escolha uma imagem JPG, PNG ou WEBP.'
    input.value = ''
    return
  }

  if (file.size > 5 * 1024 * 1024) {
    erroFotografia.value = true
    mensagemFotografia.value = 'A fotografia não pode ultrapassar 5 MB.'
    input.value = ''
    return
  }

  const form = new FormData()
  form.append('file', file)
  fotografiaAEnviar.value = true

  try {
    const updatedUser = await api<AuthUser>(
      `/users/${auth.user.value.id}/avatar`,
      { method: 'POST', body: form },
    )
    auth.user.value = updatedUser
    erroFotografia.value = false
    mensagemFotografia.value = 'Fotografia atualizada.'
  } catch (error) {
    console.error('Erro ao atualizar fotografia de perfil:', error)
    erroFotografia.value = true
    mensagemFotografia.value = obterMensagemErro(error)
  } finally {
    fotografiaAEnviar.value = false
    input.value = ''
  }
}
</script>

<template>
  <header ref="headerRef" class="app-header">
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
          TASKFLOW /
          {{ auth.user.value?.role === 'admin' ? 'BACK-OFFICE' : 'FRONT-OFFICE' }}
        </span>

        <h1>{{ title }}</h1>
      </div>
    </div>

    <div class="header-actions">
      <div class="search-container">
        <label class="header-search">
          <SidebarIcon name="search" />
          <input
            ref="searchInput"
            v-model="searchQuery"
            type="search"
            placeholder="Pesquisar..."
            aria-label="Pesquisar tarefas, projetos e utilizadores"
            aria-controls="global-search-results"
            :aria-expanded="mostrarPesquisa && Boolean(searchQuery.trim())"
            @focus="mostrarPesquisa = true; mostrarNotificacoes = false"
            @input="mostrarPesquisa = true"
            @keydown.enter.prevent="abrirPrimeiroResultado"
          />
          <kbd>Ctrl K</kbd>
        </label>

        <div
          v-if="mostrarPesquisa && searchQuery.trim()"
          id="global-search-results"
          class="header-popover search-popover"
          role="listbox"
          aria-label="Resultados da pesquisa"
        >
          <p v-if="dashboardCarregando" class="popover-state">
            A pesquisar...
          </p>
          <p v-else-if="dashboardErro" class="popover-state popover-error" role="alert">
            {{ dashboardErro }}
          </p>
          <template v-else-if="resultadosPesquisa.length">
            <NuxtLink
              v-for="result in resultadosPesquisa"
              :key="result.id"
              :to="result.to"
              class="search-result"
              role="option"
              @click.prevent="abrirDestino(result.to)"
            >
              <span class="search-result-icon">
                <SidebarIcon :name="result.kind === 'Projeto' ? 'projects' : result.kind === 'Utilizador' ? 'users' : 'tasks'" />
              </span>
              <span class="search-result-copy">
                <strong>{{ result.title }}</strong>
                <small>{{ result.subtitle }}</small>
              </span>
              <span class="search-result-kind">{{ result.kind }}</span>
            </NuxtLink>
          </template>
          <p v-else class="popover-state">
            Não foram encontrados resultados para “{{ searchQuery }}”.
          </p>
        </div>
      </div>

      <div class="notification-container">
        <button
          class="header-icon-button"
          :class="{ 'has-notifications': totalNaoLidas > 0 }"
          type="button"
          :aria-label="`Notificações${totalNaoLidas ? `, ${totalNaoLidas} não lidas` : ''}`"
          aria-controls="header-notifications"
          :aria-expanded="mostrarNotificacoes"
          title="Ver notificações"
          @click="mostrarNotificacoes = !mostrarNotificacoes; mostrarPesquisa = false"
        >
          <SidebarIcon name="notifications" />
          <span v-if="totalNaoLidas" class="notification-count">
            {{ totalNaoLidas > 9 ? '9+' : totalNaoLidas }}
          </span>
        </button>

        <section
          v-if="mostrarNotificacoes"
          id="header-notifications"
          class="header-popover notification-popover"
          aria-label="Notificações de tarefas e projetos"
        >
          <div class="popover-heading">
            <div>
              <strong>Notificações</strong>
              <span>
                {{ notificacoes.length }} alertas ativos ·
                {{ totalNaoLidas }} {{ totalNaoLidas === 1 ? 'não lida' : 'não lidas' }}
              </span>
            </div>
            <button type="button" aria-label="Fechar notificações" @click="mostrarNotificacoes = false">
              ×
            </button>
          </div>
          <p v-if="dashboardCarregando" class="popover-state">
            A verificar tarefas e projetos...
          </p>
          <p v-else-if="dashboardErro" class="popover-state popover-error" role="alert">
            {{ dashboardErro }}
          </p>
          <ul v-else-if="notificacoes.length" class="notification-list">
            <li v-for="item in notificacoes" :key="item.id">
              <button
                type="button"
                class="notification-item"
                :class="{ 'is-read': notificacaoLida(item) }"
                :aria-label="`Abrir notificação${notificacaoLida(item) ? ' lida' : ' não lida'}: ${item.title}`"
                @click="abrirNotificacao(item)"
              >
                <span
                  class="notification-marker"
                  :class="[
                    `marker-${item.kind.toLowerCase()}`,
                    { 'marker-read': notificacaoLida(item) },
                  ]"
                ></span>
                <span class="notification-copy">
                  <strong>{{ item.title }}</strong>
                  <small>{{ item.description }}</small>
                </span>
                <span
                  class="notification-kind"
                  :class="{ 'notification-read': notificacaoLida(item) }"
                >
                  {{ notificacaoLida(item) ? 'Lida' : item.kind }}
                </span>
              </button>
            </li>
          </ul>
          <p v-else class="popover-state">
            Não há alertas ou notificações.
          </p>
        </section>
      </div>

      <div class="header-divider"></div>

      <div class="header-profile">
        <label
          class="profile-avatar-change"
          :class="{ 'is-uploading': fotografiaAEnviar }"
          :title="fotografiaAEnviar ? 'A carregar fotografia...' : 'Alterar fotografia'"
        >
          <div class="profile-avatar">
            <img
              v-if="avatarUrl && !avatarFalhou"
              :src="avatarUrl"
              :alt="`Fotografia de ${auth.user.value?.name ?? 'administrador'}`"
              @error="avatarFalhou = true"
            />
            <span v-else>
              {{ auth.user.value?.name.slice(0, 1).toUpperCase() ?? 'A' }}
            </span>
          </div>
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp"
            aria-label="Alterar fotografia de perfil"
            :disabled="fotografiaAEnviar || !auth.user.value"
            @change="carregarFotografia"
          />
        </label>

        <NuxtLink
          to="/settings"
          class="header-profile-link"
          aria-label="Ver perfil"
          title="Ver perfil"
        >
          <div class="profile-copy">
            <strong>{{ auth.user.value?.name ?? 'Utilizador' }}</strong>
            <span>{{ auth.user.value?.role === 'admin' ? 'Administrador' : 'Utilizador' }}</span>
          </div>
        </NuxtLink>
        <span
          v-if="mensagemFotografia"
          class="profile-upload-message"
          :class="{ 'is-error': erroFotografia }"
          :role="erroFotografia ? 'alert' : 'status'"
        >
          {{ mensagemFotografia }}
        </span>

        <button
          class="logout-button"
          type="button"
          title="Terminar sessão"
          aria-label="Terminar sessão"
          @click="auth.logout"
        >
          <SidebarIcon name="logout" />
        </button>
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
  background: var(--tf-surface);
  border-bottom: 1px solid var(--tf-border);
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

.search-container,
.notification-container {
  position: relative;
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

.header-search > :deep(svg) {
  flex: 0 0 18px;
  color: #8492a8;
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
  display: grid;
  width: 36px;
  height: 36px;
  place-items: center;
  color: #64748b;
  background: transparent;
  border: 0;
  border-radius: 9px;
  cursor: pointer;
  transition: color 0.15s ease, background 0.15s ease;
}

.header-icon-button:hover,
.header-icon-button[aria-expanded='true'] {
  color: #345b9e;
  background: #edf3ff;
}

.header-icon-button:focus-visible {
  outline: 2px solid #6485ff;
  outline-offset: 2px;
}

.header-icon-button :deep(svg) {
  width: 21px;
  height: 21px;
}

.header-icon-button.has-notifications {
  color: #345b9e;
}

.notification-count {
  position: absolute;
  top: 0;
  right: -2px;
  display: grid;
  min-width: 17px;
  height: 17px;
  padding: 0 4px;
  place-items: center;
  color: #fff;
  background: #e5484d;
  border: 2px solid #fff;
  border-radius: 999px;
  font-size: 9px;
  font-weight: 750;
  line-height: 1;
}

.header-popover {
  position: absolute;
  z-index: 60;
  top: calc(100% + 13px);
  overflow: hidden;
  width: min(390px, calc(100vw - 28px));
  background: #fff;
  border: 1px solid #e2e9f5;
  border-radius: 13px;
  box-shadow: 0 16px 40px rgb(23 43 77 / 16%);
}

.search-popover {
  left: 0;
}

.notification-popover {
  right: 0;
  width: min(420px, calc(100vw - 28px));
}

.popover-state {
  margin: 0;
  padding: 20px 16px;
  color: #74839b;
  font-size: 12px;
  line-height: 1.5;
}

.popover-error {
  color: #b42318;
}

.search-result {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 11px 13px;
  color: inherit;
  text-decoration: none;
}

.search-result + .search-result,
.notification-list li + li {
  border-top: 1px solid #f0f3f8;
}

.search-result:hover,
.search-result:focus-visible,
.notification-item:hover,
.notification-item:focus-visible {
  background: #f7f9fd;
  outline: none;
}

.search-result-icon {
  display: grid;
  flex: 0 0 31px;
  width: 31px;
  height: 31px;
  place-items: center;
  color: #4567a7;
  background: #edf3ff;
  border-radius: 9px;
}

.search-result-icon :deep(svg) {
  width: 17px;
  height: 17px;
}

.search-result-copy,
.notification-copy {
  display: grid;
  min-width: 0;
  flex: 1;
  gap: 4px;
}

.search-result-copy strong,
.notification-copy strong {
  overflow: hidden;
  color: #263957;
  font-size: 12px;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.search-result-copy small,
.notification-copy small {
  overflow: hidden;
  color: #8492a8;
  font-size: 10px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.search-result-kind,
.notification-kind {
  flex: 0 0 auto;
  color: #8b9ab1;
  font-size: 9px;
  font-weight: 700;
}

.popover-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid #edf1f7;
}

.popover-heading > div {
  display: grid;
  gap: 4px;
}

.popover-heading strong {
  color: #263957;
  font-size: 13px;
}

.popover-heading span {
  color: #8492a8;
  font-size: 10px;
}

.popover-heading button {
  display: grid;
  width: 28px;
  height: 28px;
  place-items: center;
  color: #73829a;
  background: transparent;
  border: 0;
  border-radius: 7px;
  font-size: 20px;
  cursor: pointer;
}

.popover-heading button:hover {
  color: #263957;
  background: #f1f4f9;
}

.notification-list {
  max-height: min(390px, 60vh);
  overflow-y: auto;
  margin: 0;
  padding: 0;
  list-style: none;
}

.notification-item {
  display: flex;
  width: 100%;
  align-items: center;
  gap: 10px;
  padding: 12px 15px;
  border: 0;
  background: transparent;
  color: inherit;
  text-align: left;
  cursor: pointer;
  font: inherit;
}

.notification-item:focus-visible {
  outline: 2px solid #6485ff;
  outline-offset: -2px;
}

.notification-item.is-read .notification-copy strong,
.notification-item.is-read .notification-copy small {
  color: #8b97aa;
}

.notification-item.is-read .notification-marker {
  opacity: 0.4;
}

.notification-marker {
  flex: 0 0 8px;
  width: 8px;
  height: 8px;
  background: #e5484d;
  border-radius: 50%;
}

.marker-atraso {
  background: #ee9b26;
}

.marker-inatividade {
  background: #6485ff;
}

.marker-tarefa {
  background: #22a06b;
}

.marker-read {
  background: #aab4c3;
}

.notification-read {
  color: #718096;
  background: #f0f2f5;
}

.header-divider {
  width: 1px;
  height: 35px;
  background: #e5eaf2;
}

.header-profile {
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
}

.profile-avatar-change {
  position: relative;
  display: block;
  flex: 0 0 38px;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  cursor: pointer;
}

.profile-avatar-change input {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
}

.profile-avatar-change input:focus-visible {
  outline: 2px solid #6485ff;
  outline-offset: 3px;
  border-radius: 50%;
}

.profile-avatar-change.is-uploading {
  cursor: wait;
  opacity: 0.65;
}

.header-profile-link {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px;
  color: inherit;
  border-radius: 10px;
  text-decoration: none;
}

.header-profile-link:hover,
.header-profile-link:focus-visible {
  background: #f5f7fb;
}

.header-profile-link:focus-visible {
  outline: 2px solid #6485ff;
  outline-offset: 2px;
}

.profile-upload-message {
  position: absolute;
  z-index: 2;
  top: calc(100% + 10px);
  right: 42px;
  width: max-content;
  max-width: min(300px, calc(100vw - 40px));
  padding: 9px 12px;
  color: #166534;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 8px;
  box-shadow: 0 5px 16px rgb(23 43 77 / 12%);
  font-size: 11px;
}

.profile-upload-message.is-error {
  color: #b42318;
  background: #fff5f4;
  border-color: #fecdca;
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

.profile-avatar img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
}

.profile-avatar span {
  line-height: 1;
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

.logout-button {
  display: grid;
  width: 34px;
  height: 34px;
  place-items: center;
  color: #64748b;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 9px;
  cursor: pointer;
}

.logout-button:hover {
  color: #4338ca;
  background: #eef2ff;
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
    gap: 7px;
  }

  .header-divider,
  .profile-copy,
  .profile-chevron {
    display: none;
  }

  .header-search {
    width: clamp(110px, 34vw, 190px);
  }

  .header-search kbd {
    display: none;
  }

  .header-heading h1 {
    font-size: 18px;
  }
}
</style>
