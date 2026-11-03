<script setup lang="ts">
import { onBeforeUnmount, onMounted } from 'vue'

// Área pessoal: mostra tarefas atribuídas e acompanha os registos de trabalho por tarefa.
definePageMeta({
  layout: 'member',
})

type EstadoTarefaAPI = 'to_do' | 'in_progress' | 'completed' | 'blocked'
type PrioridadeAPI = 'low' | 'medium' | 'high'
type EstadoProjetoAPI = 'active' | 'completed' | 'archived'

interface ProjetoAPI {
  id: number
  name: string
  status: EstadoProjetoAPI
}

interface TarefaAPI {
  id: number
  project_id: number
  title: string
  description: string | null
  category: string
  priority: PrioridadeAPI
  status: EstadoTarefaAPI
  progress: number
  assigned_to: number | null
  due_date: string | null
  completed_at: string | null
}

interface AnexoRegistoAPI {
  id: number
  original_name: string
  content_type: string
  size: number
}

interface RegistoTrabalhoAPI {
  id: number
  task_id: number
  author_id: number
  author_name: string
  note: string
  progress: number
  created_at: string
  attachments: AnexoRegistoAPI[]
}

interface Tarefa {
  id: number
  projectId: number
  projectName: string
  projectStatus: EstadoProjetoAPI
  title: string
  description: string
  category: string
  priority: PrioridadeAPI
  status: EstadoTarefaAPI
  progress: number
  dueDate: string | null
  completedAt: string | null
  saving: boolean
  updates: RegistoTrabalhoAPI[]
  updatesLoaded: boolean
  loadingUpdates: boolean
  workPanelOpen: boolean
  savingUpdate: boolean
  updateNote: string
  updateProgress: number
  selectedFiles: File[]
}

const api = useNuxtApp().$api
const auth = useAuth()

const projetos = ref<ProjetoAPI[]>([])
const tarefas = ref<Tarefa[]>([])
const pesquisa = ref('')
const filtroEstado = ref('')
const filtroProjeto = ref('')
const carregando = ref(true)
const erro = ref('')
const sucesso = ref('')
let pedidoTarefas = 0
let atualizacaoEmCurso = false
let refreshTimer: ReturnType<typeof setInterval> | undefined

const estados: EstadoTarefaAPI[] = [
  'to_do',
  'in_progress',
  'blocked',
  'completed',
]

const nomesEstados: Record<EstadoTarefaAPI, string> = {
  to_do: 'Por fazer',
  in_progress: 'Em curso',
  blocked: 'Bloqueada',
  completed: 'Concluída',
}

const nomesPrioridades: Record<PrioridadeAPI, string> = {
  low: 'Baixa',
  medium: 'Média',
  high: 'Alta',
}

const nomesCategorias: Record<string, string> = {
  planning: 'Planeamento',
  research: 'Investigação',
  design: 'Design',
  development: 'Desenvolvimento',
  validation: 'Validação',
  documentation: 'Documentação',
}

const tarefasVisiveis = computed(() => {
  const termo = pesquisa.value.trim().toLocaleLowerCase('pt-PT')

  // Mantém a lista focada no utilizador autenticado e ordenada pelos prazos próximos.
  return tarefas.value
    .filter((tarefa) => {
      const correspondeTexto =
        !termo ||
        `${tarefa.title} ${tarefa.description} ${tarefa.projectName}`
          .toLocaleLowerCase('pt-PT')
          .includes(termo)
      const correspondeEstado =
        !filtroEstado.value || tarefa.status === filtroEstado.value
      const correspondeProjeto =
        !filtroProjeto.value ||
        tarefa.projectId === Number(filtroProjeto.value)

      return correspondeTexto && correspondeEstado && correspondeProjeto
    })
    .sort((a, b) =>
      (a.dueDate ?? '9999-12-31').localeCompare(
        b.dueDate ?? '9999-12-31',
      ),
    )
})

const utilizadorSelecionado = computed(() =>
  auth.user.value,
)

const tarefasConcluidas = computed(
  () => tarefas.value.filter((tarefa) => tarefa.status === 'completed').length,
)

const tarefasAbertas = computed(
  () => tarefas.value.length - tarefasConcluidas.value,
)

const tarefasAtrasadas = computed(
  () =>
    tarefas.value.filter(
      (tarefa) =>
        tarefa.status !== 'completed' &&
        tarefa.dueDate !== null &&
        tarefa.dueDate.slice(0, 10) < hojeISO(),
    ).length,
)

const progresso = computed(() =>
  tarefas.value.length
    ? Math.round(
        tarefas.value.reduce((total, tarefa) => total + tarefa.progress, 0) /
          tarefas.value.length,
      )
    : 0,
)

function hojeISO(): string {
  const hoje = new Date()
  const ano = hoje.getFullYear()
  const mes = String(hoje.getMonth() + 1).padStart(2, '0')
  const dia = String(hoje.getDate()).padStart(2, '0')

  return `${ano}-${mes}-${dia}`
}

function formatarData(data: string | null): string {
  if (!data) return 'Sem prazo'

  const dataValida = new Date(`${data.slice(0, 10)}T12:00:00`)

  if (Number.isNaN(dataValida.getTime())) return 'Data indisponível'

  return new Intl.DateTimeFormat('pt-PT', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  }).format(dataValida)
}

function classePrazo(tarefa: Tarefa): string {
  if (!tarefa.dueDate || tarefa.status === 'completed') return 'prazo-normal'

  if (tarefa.dueDate.slice(0, 10) < hojeISO()) return 'prazo-atrasado'
  if (tarefa.dueDate.slice(0, 10) === hojeISO()) return 'prazo-hoje'

  return 'prazo-normal'
}

function mensagemErro(error: unknown): string {
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

  return 'Não foi possível comunicar com a API. Tente novamente.'
}

function converterTarefa(
  tarefa: TarefaAPI,
  projetosPorId: Map<number, ProjetoAPI>,
): Tarefa {
  // Mantém a resposta da API num formato próprio da página e junta o nome do projeto.
  const projeto = projetosPorId.get(tarefa.project_id)

  return {
    id: tarefa.id,
    projectId: tarefa.project_id,
    projectName: projeto?.name ?? 'Projeto desconhecido',
    projectStatus: projeto?.status ?? 'archived',
    title: tarefa.title,
    description: tarefa.description ?? '',
    category: nomesCategorias[tarefa.category] ?? 'Outra categoria',
    priority: tarefa.priority,
    status: tarefa.status,
    progress: tarefa.progress,
    dueDate: tarefa.due_date,
    completedAt: tarefa.completed_at,
    saving: false,
    updates: [],
    updatesLoaded: false,
    loadingUpdates: false,
    workPanelOpen: false,
    savingUpdate: false,
    updateNote: '',
    updateProgress: tarefa.progress,
    selectedFiles: [],
  }
}

async function carregarTarefas(silenciosa = false): Promise<void> {
  const pedidoAtual = ++pedidoTarefas
  const id = auth.user.value?.id

  if (id === undefined) {
    tarefas.value = []
    carregando.value = false
    return
  }

  if (!silenciosa) carregando.value = true
  erro.value = ''
  if (!silenciosa) sucesso.value = ''

  try {
    // O contador descarta respostas antigas se uma nova carga começar antes desta terminar.
    const tarefasAPI = await api<TarefaAPI[]>(
      `/tasks/?assigned_to=${encodeURIComponent(id)}`,
    )
    if (pedidoAtual !== pedidoTarefas) return

    const projetosPorId = new Map(
      projetos.value.map((projeto) => [projeto.id, projeto]),
    )

    tarefas.value = tarefasAPI.map((tarefa) =>
      converterTarefa(tarefa, projetosPorId),
    )
  } catch (error) {
    if (pedidoAtual !== pedidoTarefas) return

    console.error('Erro ao carregar tarefas atribuídas:', error)
    erro.value = mensagemErro(error)
  } finally {
    if (pedidoAtual === pedidoTarefas) {
      carregando.value = false
    }
  }
}

async function carregarArea(silenciosa = false): Promise<void> {
  if (atualizacaoEmCurso) return
  atualizacaoEmCurso = true

  if (!silenciosa) carregando.value = true
  erro.value = ''

  try {
    const projetosAPI = await api<ProjetoAPI[]>('/projects/')
    projetos.value = projetosAPI

    await carregarTarefas(silenciosa)
  } catch (error) {
    console.error('Erro ao carregar a área de trabalho:', error)
    erro.value = mensagemErro(error)
    carregando.value = false
  } finally {
    atualizacaoEmCurso = false
  }
}

async function alterarEstado(
  tarefa: Tarefa,
  evento: Event,
): Promise<void> {
  const elemento = evento.target as HTMLSelectElement
  const novoEstado = elemento.value as EstadoTarefaAPI

  if (!estados.includes(novoEstado) || novoEstado === tarefa.status) return

  if (tarefa.projectStatus === 'archived') {
    elemento.value = tarefa.status
    erro.value = 'Não é possível alterar tarefas de projetos arquivados.'
    return
  }

  tarefa.saving = true
  erro.value = ''
  sucesso.value = ''

  try {
    // Só confirma o novo estado no ecrã depois de a API o guardar com sucesso.
    const atualizada = await api<TarefaAPI>(
      `/tasks/${tarefa.id}`,
      {
        method: 'PATCH',
        body: { status: novoEstado },
      },
    )

    tarefa.status = atualizada.status
    tarefa.progress = atualizada.progress
    tarefa.completedAt = atualizada.completed_at
    sucesso.value = 'Estado da tarefa atualizado.'
  } catch (error) {
    console.error('Erro ao atualizar o estado da tarefa:', error)
    elemento.value = tarefa.status
    erro.value = mensagemErro(error)
  } finally {
    tarefa.saving = false
  }
}

async function abrirRegisto(tarefa: Tarefa): Promise<void> {
  tarefa.workPanelOpen = !tarefa.workPanelOpen
  if (!tarefa.workPanelOpen) return

  tarefa.updateProgress = tarefa.progress
  erro.value = ''

  if (!tarefa.updatesLoaded) {
    await carregarRegistos(tarefa)
  }
}

async function carregarRegistos(tarefa: Tarefa): Promise<void> {
  tarefa.loadingUpdates = true
  erro.value = ''

  try {
    // O histórico só é carregado ao abrir o painel e fica em cache na tarefa.
    tarefa.updates = await api<RegistoTrabalhoAPI[]>(
      `/tasks/${tarefa.id}/work-logs`,
    )
    tarefa.updatesLoaded = true
  } catch (error) {
    console.error('Erro ao carregar o histórico de trabalho:', error)
    erro.value = mensagemErro(error)
  } finally {
    tarefa.loadingUpdates = false
  }
}

function selecionarFicheiros(tarefa: Tarefa, evento: Event): void {
  const input = evento.target as HTMLInputElement
  const selecionados = Array.from(input.files ?? [])
  input.value = ''

  if (selecionados.length + tarefa.selectedFiles.length > 5) {
    erro.value = 'Podes anexar no máximo 5 ficheiros por registo.'
    return
  }

  const tamanhoTotal = [...tarefa.selectedFiles, ...selecionados]
    .reduce((total, ficheiro) => total + ficheiro.size, 0)

  // Impõe limites por ficheiro e cumulativos antes de guardar os anexos em memória.
  if (selecionados.some((ficheiro) => ficheiro.size > 10 * 1024 * 1024)) {
    erro.value = 'Cada ficheiro pode ter no máximo 10 MB.'
    return
  }

  if (tamanhoTotal > 25 * 1024 * 1024) {
    erro.value = 'O conjunto de anexos não pode ultrapassar 25 MB.'
    return
  }

  tarefa.selectedFiles.push(...selecionados)
  erro.value = ''
}

function removerFicheiro(tarefa: Tarefa, indice: number): void {
  tarefa.selectedFiles.splice(indice, 1)
}

function formatarTamanho(tamanho: number): string {
  if (tamanho < 1024) return `${tamanho} B`
  if (tamanho < 1024 * 1024) return `${Math.ceil(tamanho / 1024)} KB`

  return `${(tamanho / (1024 * 1024)).toFixed(1)} MB`
}

function formatarDataHora(data: string): string {
  const dataValida = new Date(data)
  if (Number.isNaN(dataValida.getTime())) return 'Data indisponível'

  return new Intl.DateTimeFormat('pt-PT', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(dataValida)
}

async function guardarRegisto(tarefa: Tarefa): Promise<void> {
  const nota = tarefa.updateNote.trim()
  if (!nota) {
    erro.value = 'Descreve o trabalho realizado antes de guardar.'
    return
  }

  tarefa.savingUpdate = true
  erro.value = ''
  sucesso.value = ''

  const dados = new FormData()
  // Nota, progresso e anexos são enviados juntos como multipart/form-data.
  dados.set('note', nota)
  dados.set('progress', String(tarefa.updateProgress))
  for (const ficheiro of tarefa.selectedFiles) {
    dados.append('files', ficheiro)
  }

  try {
    const registo = await api<RegistoTrabalhoAPI>(
      `/tasks/${tarefa.id}/work-logs`,
      {
        method: 'POST',
        body: dados,
      },
    )

    tarefa.progress = registo.progress
    tarefa.updates.unshift(registo)
    tarefa.updatesLoaded = true
    tarefa.updateNote = ''
    tarefa.selectedFiles = []
    sucesso.value = 'Atualização do trabalho registada.'
  } catch (error) {
    console.error('Erro ao registar trabalho:', error)
    erro.value = mensagemErro(error)
  } finally {
    tarefa.savingUpdate = false
  }
}

async function descarregarAnexo(
  tarefa: Tarefa,
  registo: RegistoTrabalhoAPI,
  anexo: AnexoRegistoAPI,
): Promise<void> {
  try {
    const ficheiro = await api<Blob>(
      `/tasks/${tarefa.id}/work-logs/${registo.id}/attachments/${anexo.id}`,
      { responseType: 'blob' },
    )
    const url = URL.createObjectURL(ficheiro)
    const link = document.createElement('a')
    link.href = url
    link.download = anexo.original_name
    document.body.append(link)
    link.click()
    link.remove()
    window.setTimeout(() => URL.revokeObjectURL(url), 1000)
  } catch (error) {
    console.error('Erro ao descarregar o anexo:', error)
    erro.value = mensagemErro(error)
  }
}

function atualizarAreaVisivel(): void {
  if (document.visibilityState === 'visible') {
    void carregarArea(true)
  }
}

onMounted(() => {
  void carregarArea()
  refreshTimer = setInterval(atualizarAreaVisivel, 60_000)
  document.addEventListener('visibilitychange', atualizarAreaVisivel)
})

onBeforeUnmount(() => {
  if (refreshTimer) clearInterval(refreshTimer)
  document.removeEventListener('visibilitychange', atualizarAreaVisivel)
})
</script>

<template>
  <section class="member-area">
    <header class="member-hero">
      <div class="hero-copy">
        <span class="hero-label"><span></span> FRONT-OFFICE · ÁREA DE TRABALHO</span>
        <h2>Olá, {{ utilizadorSelecionado?.name ?? 'bem-vindo/a' }}</h2>
        <p>Organize o seu trabalho, acompanhe os prazos e avance tarefa a tarefa.</p>
      </div>

    </header>

    <div v-if="erro" class="notice notice-error" role="alert">
      <span>{{ erro }}</span>
      <button type="button" aria-label="Fechar mensagem" @click="erro = ''">×</button>
    </div>
    <div v-if="sucesso" class="notice notice-success" role="status">
      <span>{{ sucesso }}</span>
      <button type="button" aria-label="Fechar mensagem" @click="sucesso = ''">×</button>
    </div>

    <section class="summary-grid" aria-label="Resumo das tarefas">
      <article class="summary-card">
        <span class="summary-icon icon-indigo">✓</span>
        <div><span>Tarefas atribuídas</span><strong>{{ tarefas.length }}</strong></div>
        <small>{{ tarefasAbertas }} por concluir</small>
      </article>
      <article class="summary-card">
        <span class="summary-icon icon-green">↗</span>
        <div><span>Concluídas</span><strong>{{ tarefasConcluidas }}</strong></div>
        <small>{{ progresso }}% do trabalho</small>
      </article>
      <article class="summary-card">
        <span class="summary-icon icon-red">!</span>
        <div><span>Fora do prazo</span><strong>{{ tarefasAtrasadas }}</strong></div>
        <small>{{ tarefasAtrasadas ? 'Requerem atenção' : 'Tudo em dia' }}</small>
      </article>
      <article class="progress-card">
        <div class="progress-heading">
          <div><span>Progresso geral</span><strong>{{ progresso }}%</strong></div>
          <span>média das tarefas atribuídas</span>
        </div>
        <div
          class="progress-track"
          role="progressbar"
          :aria-valuenow="progresso"
          aria-valuemin="0"
          aria-valuemax="100"
          aria-label="Progresso das tarefas"
        >
          <span :style="{ width: `${progresso}%` }"></span>
        </div>
        <small>Um passo de cada vez. Está a fazer um ótimo trabalho.</small>
      </article>
    </section>

    <section class="tasks-panel">
      <div class="panel-heading">
        <div>
          <span class="section-eyebrow">O SEU DIA</span>
          <h3>As minhas tarefas</h3>
          <p>As tarefas atribuídas a si nos seus projetos.</p>
        </div>
        <span class="task-count">{{ tarefasVisiveis.length }} tarefas</span>
      </div>

      <div class="task-filters">
        <label class="search-field">
          <span aria-hidden="true">⌕</span>
          <input v-model="pesquisa" type="search" placeholder="Pesquisar tarefas..." />
        </label>
        <select v-model="filtroProjeto" aria-label="Filtrar por projeto">
          <option value="">Todos os projetos</option>
          <option v-for="projeto in projetos" :key="projeto.id" :value="projeto.id">
            {{ projeto.name }}
          </option>
        </select>
        <select v-model="filtroEstado" aria-label="Filtrar por estado">
          <option value="">Todos os estados</option>
          <option v-for="estado in estados" :key="estado" :value="estado">
            {{ nomesEstados[estado] }}
          </option>
        </select>
      </div>

      <div v-if="carregando" class="empty-state">
        <span class="loading-spinner" aria-hidden="true"></span>
        <strong>A carregar a sua área de trabalho…</strong>
        <span>Estamos a procurar as tarefas atribuídas.</span>
      </div>

      <div v-else-if="!tarefas.length" class="empty-state">
        <span class="empty-icon" aria-hidden="true">✦</span>
        <strong>O seu espaço está livre</strong>
        <span>Ainda não tem tarefas atribuídas. Quando lhe atribuírem uma tarefa, ela aparecerá aqui.</span>
      </div>

      <div v-else-if="!tarefasVisiveis.length" class="empty-state compact-empty">
        <strong>Não encontrámos tarefas</strong>
        <span>Experimente alterar a pesquisa ou os filtros.</span>
      </div>

      <div v-else class="task-list">
        <div v-for="tarefa in tarefasVisiveis" :key="tarefa.id" class="task-entry">
          <article class="task-row">
            <span
              class="task-status-mark"
              :class="`status-mark-${tarefa.status}`"
              aria-hidden="true"
            ></span>

            <div class="task-main">
              <div class="task-title-line">
                <h4>{{ tarefa.title }}</h4>
                <span class="priority-pill" :class="`priority-${tarefa.priority}`">
                  {{ nomesPrioridades[tarefa.priority] }} prioridade
                </span>
              </div>
              <p v-if="tarefa.description">{{ tarefa.description }}</p>
              <div class="task-meta">
                <span class="project-name"><span aria-hidden="true">▤</span>{{ tarefa.projectName }}</span>
                <span>{{ tarefa.category }}</span>
                <span
                  class="due-date"
                  :class="classePrazo(tarefa)"
                  :title="tarefa.dueDate ? `Prazo: ${formatarData(tarefa.dueDate)}` : undefined"
                >
                  <span aria-hidden="true">◷</span>{{ formatarData(tarefa.dueDate) }}
                </span>
                <span v-if="tarefa.projectStatus === 'archived'" class="archived-label">
                  Projeto arquivado
                </span>
              </div>
              <div class="task-progress">
                <div
                  class="task-progress-track"
                  role="progressbar"
                  :aria-valuenow="tarefa.progress"
                  aria-valuemin="0"
                  aria-valuemax="100"
                  :aria-label="`Progresso de ${tarefa.title}`"
                >
                  <span :style="{ width: `${tarefa.progress}%` }"></span>
                </div>
                <span>{{ tarefa.progress }}% concluído</span>
              </div>
            </div>

            <div class="task-actions">
              <label class="status-control">
                <span class="sr-only">Estado de {{ tarefa.title }}</span>
                <select
                  :value="tarefa.status"
                  :disabled="tarefa.saving || tarefa.projectStatus === 'archived'"
                  @change="alterarEstado(tarefa, $event)"
                >
                  <option v-for="estado in estados" :key="estado" :value="estado">
                    {{ nomesEstados[estado] }}
                  </option>
                </select>
              </label>

              <button
                type="button"
                class="work-toggle"
                :aria-expanded="tarefa.workPanelOpen"
                @click="abrirRegisto(tarefa)"
              >
                {{ tarefa.workPanelOpen ? 'Fechar registo' : 'Registar trabalho' }}
              </button>
            </div>
          </article>

          <!-- O painel de registo carrega o histórico ao abrir e permite anexar provas do progresso. -->
          <section
            v-if="tarefa.workPanelOpen"
            class="worklog-panel"
            :aria-label="`Registar trabalho em ${tarefa.title}`"
          >
            <div class="worklog-columns">
              <div class="worklog-composer">
                <div class="worklog-heading">
                  <div>
                    <span class="section-eyebrow">ATUALIZAÇÃO DA TAREFA</span>
                    <h5>O que avançou?</h5>
                  </div>
                  <span class="work-progress-value">{{ tarefa.updateProgress }}%</span>
                </div>

                <form @submit.prevent="guardarRegisto(tarefa)">
                  <label class="work-field">
                    <span>Trabalho realizado, notas ou próximos passos</span>
                    <textarea
                      v-model="tarefa.updateNote"
                      rows="4"
                      maxlength="5000"
                      placeholder="Descreva o que concluiu, decisões tomadas ou o que falta fazer..."
                      required
                      :disabled="tarefa.savingUpdate || tarefa.projectStatus === 'archived'"
                    ></textarea>
                  </label>

                  <label class="work-field progress-field">
                    <span>
                      Progresso da tarefa
                      <strong>{{ tarefa.updateProgress }}%</strong>
                    </span>
                    <input
                      v-model.number="tarefa.updateProgress"
                      type="range"
                      min="0"
                      max="100"
                      step="5"
                      :disabled="
                        tarefa.savingUpdate ||
                        tarefa.projectStatus === 'archived' ||
                        tarefa.status === 'completed'
                      "
                    />
                  </label>

                  <label class="work-field">
                    <span>Anexar documentos ou imagens (máximo 5 ficheiros, 10 MB cada)</span>
                    <input
                      type="file"
                      accept=".pdf,.png,.jpg,.jpeg,.webp,.txt,.md,.csv,.docx,.xlsx"
                      multiple
                      :disabled="tarefa.savingUpdate || tarefa.projectStatus === 'archived'"
                      @change="selecionarFicheiros(tarefa, $event)"
                    />
                  </label>

                  <ul v-if="tarefa.selectedFiles.length" class="selected-files">
                    <li v-for="(ficheiro, indice) in tarefa.selectedFiles" :key="`${ficheiro.name}-${ficheiro.lastModified}`">
                      <span>{{ ficheiro.name }} · {{ formatarTamanho(ficheiro.size) }}</span>
                      <button
                        type="button"
                        :aria-label="`Remover ${ficheiro.name}`"
                        :disabled="tarefa.savingUpdate"
                        @click="removerFicheiro(tarefa, indice)"
                      >
                        ×
                      </button>
                    </li>
                  </ul>

                  <button
                    class="submit-update"
                    type="submit"
                    :disabled="
                      tarefa.savingUpdate ||
                      tarefa.projectStatus === 'archived' ||
                      !tarefa.updateNote.trim()
                    "
                  >
                    {{ tarefa.savingUpdate ? 'A guardar atualização…' : 'Guardar atualização' }}
                  </button>
                  <small v-if="tarefa.projectStatus === 'archived'" class="archived-hint">
                    Projetos arquivados não aceitam novos registos.
                  </small>
                </form>
              </div>

              <div class="worklog-history">
                <div class="worklog-heading">
                  <div>
                    <span class="section-eyebrow">HISTÓRICO</span>
                    <h5>Trabalho registado</h5>
                  </div>
                  <button
                    class="history-refresh"
                    type="button"
                    :disabled="tarefa.loadingUpdates"
                    aria-label="Atualizar histórico de trabalho"
                    @click="carregarRegistos(tarefa)"
                  >
                    ↻
                  </button>
                </div>

                <div v-if="tarefa.loadingUpdates" class="history-empty">
                  A carregar o histórico…
                </div>
                <div v-else-if="!tarefa.updates.length" class="history-empty">
                  Ainda não existem atualizações nesta tarefa.
                </div>
                <ol v-else class="worklog-list">
                  <li v-for="registo in tarefa.updates" :key="registo.id" class="worklog-item">
                    <div class="worklog-item-heading">
                      <strong>{{ registo.author_name }}</strong>
                      <span>{{ formatarDataHora(registo.created_at) }}</span>
                    </div>
                    <p>{{ registo.note }}</p>
                    <div class="worklog-progress">
                      <span>Progresso registado</span>
                      <strong>{{ registo.progress }}%</strong>
                    </div>
                    <ul v-if="registo.attachments.length" class="worklog-attachments">
                      <li v-for="anexo in registo.attachments" :key="anexo.id">
                        <button
                          type="button"
                          @click="descarregarAnexo(tarefa, registo, anexo)"
                        >
                          <span aria-hidden="true">↧</span>
                          {{ anexo.original_name }}
                          <small>{{ formatarTamanho(anexo.size) }}</small>
                        </button>
                      </li>
                    </ul>
                  </li>
                </ol>
              </div>
            </div>
          </section>
        </div>
      </div>
    </section>
  </section>
</template>

<style scoped>
.member-area {
  width: min(1320px, 100%);
  margin: 0 auto;
  padding: 14px 10px 38px;
  color: #172b4d;
}

.member-hero {
  position: relative;
  display: flex;
  align-items: center;
  gap: 24px;
  min-height: 190px;
  margin-bottom: 22px;
  padding: 30px 34px;
  overflow: hidden;
  color: white;
  background:
    radial-gradient(ellipse at 75% 20%, rgb(101 117 255 / 35%), transparent 36%),
    linear-gradient(120deg, #182a4b 0%, #253d70 58%, #3159a0 100%);
  border-radius: 22px;
  box-shadow: 0 16px 36px rgb(34 57 103 / 18%);
}

.member-hero::after {
  position: absolute;
  right: -80px;
  bottom: -180px;
  width: 380px;
  height: 380px;
  border: 1px solid rgb(255 255 255 / 10%);
  border-radius: 50%;
  box-shadow: 0 0 0 38px rgb(255 255 255 / 4%), 0 0 0 80px rgb(255 255 255 / 3%);
  content: '';
  pointer-events: none;
}

.hero-copy {
  position: relative;
  z-index: 1;
  flex: 1;
}

.hero-label,
.section-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #b7c8f4;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.13em;
}

.hero-label > span {
  width: 7px;
  height: 7px;
  background: #64e1c0;
  border-radius: 50%;
  box-shadow: 0 0 12px rgb(100 225 192 / 75%);
}

.hero-copy h2 {
  margin: 13px 0 8px;
  font-size: clamp(26px, 3vw, 36px);
  letter-spacing: -0.045em;
}

.hero-copy p {
  max-width: 500px;
  margin: 0;
  color: #d3def5;
  font-size: 14px;
  line-height: 1.6;
}

.notice {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin: 0 0 16px;
  padding: 12px 15px;
  border-radius: 10px;
  font-size: 13px;
}

.notice button {
  color: inherit;
  font-size: 20px;
}

.notice-error {
  color: #991b1b;
  background: #fef2f2;
  border: 1px solid #fecaca;
}

.notice-success {
  color: #166534;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr)) minmax(230px, 1.3fr);
  gap: 14px;
  margin-bottom: 20px;
}

.summary-card,
.progress-card,
.tasks-panel {
  background: #fff;
  border: 1px solid #e6ebf3;
  border-radius: 15px;
  box-shadow: 0 3px 12px rgb(34 57 103 / 4%);
}

.summary-card {
  display: grid;
  grid-template-columns: 39px 1fr;
  align-items: center;
  column-gap: 11px;
  padding: 18px;
}

.summary-icon {
  display: grid;
  grid-row: span 2;
  width: 38px;
  height: 38px;
  place-items: center;
  border-radius: 11px;
  font-size: 17px;
  font-weight: 800;
}

.icon-indigo { color: #4f46e5; background: #eef2ff; }
.icon-green { color: #15803d; background: #ecfdf5; }
.icon-red { color: #dc2626; background: #fef2f2; }

.summary-card > div {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.summary-card > div span,
.progress-heading > div span {
  color: #7b8aa2;
  font-size: 11px;
  font-weight: 600;
}

.summary-card > div strong {
  color: #192a49;
  font-size: 24px;
  letter-spacing: -0.04em;
}

.summary-card > small {
  grid-column: 2;
  margin-top: 5px;
  color: #9aa7ba;
  font-size: 10px;
}

.progress-card {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 13px;
  padding: 18px 20px;
}

.progress-heading,
.progress-heading > div {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.progress-heading > div {
  align-items: baseline;
}

.progress-heading strong {
  color: #4f46e5;
  font-size: 22px;
}

.progress-heading > span,
.progress-card > small {
  color: #94a3b8;
  font-size: 10px;
}

.progress-track {
  height: 8px;
  overflow: hidden;
  background: #eef2f8;
  border-radius: 999px;
}

.progress-track > span {
  display: block;
  height: 100%;
  background: linear-gradient(90deg, #6366f1, #38bdf8);
  border-radius: inherit;
  transition: width 0.35s ease;
}

.progress-card > small {
  line-height: 1.4;
}

.tasks-panel {
  overflow: hidden;
}

.panel-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 23px 25px 19px;
}

.section-eyebrow {
  color: #818cf8;
  font-size: 9px;
}

.panel-heading h3 {
  margin: 6px 0 4px;
  color: #192a49;
  font-size: 20px;
  letter-spacing: -0.035em;
}

.panel-heading p {
  margin: 0;
  color: #8492a8;
  font-size: 12px;
}

.task-count {
  padding: 7px 10px;
  color: #5b61d6;
  background: #f0f1ff;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  white-space: nowrap;
}

.task-filters {
  display: flex;
  gap: 10px;
  padding: 0 25px 17px;
}

.search-field {
  display: flex;
  flex: 1;
  align-items: center;
  gap: 8px;
  min-width: 160px;
  height: 38px;
  padding: 0 11px;
  color: #8b9ab1;
  background: #f8fafc;
  border: 1px solid #e5eaf2;
  border-radius: 8px;
}

.search-field > span {
  font-size: 18px;
}

.search-field input {
  width: 100%;
  min-width: 0;
  color: #334155;
  background: transparent;
  border: 0;
  outline: 0;
  font-size: 12px;
}

.task-filters select,
.status-control select {
  min-height: 38px;
  padding: 0 11px;
  color: #475569;
  background: #fff;
  border: 1px solid #e5eaf2;
  border-radius: 8px;
  font-size: 11px;
}

.task-list {
  border-top: 1px solid #edf0f5;
}

.task-entry {
  border-bottom: 1px solid #edf0f5;
}

.task-entry:last-child {
  border-bottom: 0;
}

.task-row {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 17px 25px;
  transition: background 0.18s ease;
}

.task-row:hover {
  background: #fafbff;
}

.task-status-mark {
  flex: 0 0 9px;
  width: 9px;
  height: 9px;
  align-self: flex-start;
  margin-top: 6px;
  border-radius: 50%;
}

.status-mark-to_do { background: #94a3b8; }
.status-mark-in_progress { background: #3b82f6; }
.status-mark-blocked { background: #ef4444; }
.status-mark-completed { background: #22c55e; }

.task-main {
  flex: 1;
  min-width: 0;
}

.task-title-line {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.task-title-line h4 {
  margin: 0;
  color: #263957;
  font-size: 13px;
  font-weight: 700;
}

.priority-pill {
  padding: 3px 7px;
  border-radius: 999px;
  font-size: 9px;
  font-weight: 700;
}

.priority-low { color: #64748b; background: #f1f5f9; }
.priority-medium { color: #b45309; background: #fffbeb; }
.priority-high { color: #b91c1c; background: #fef2f2; }

.task-main > p {
  margin: 6px 0 0;
  color: #75839a;
  font-size: 11px;
  line-height: 1.5;
}

.task-progress {
  display: flex;
  align-items: center;
  gap: 9px;
  max-width: 380px;
  margin-top: 11px;
}

.task-progress-track {
  flex: 1;
  height: 6px;
  overflow: hidden;
  background: #edf0f7;
  border-radius: 999px;
}

.task-progress-track > span {
  display: block;
  height: 100%;
  background: linear-gradient(90deg, #6366f1, #38bdf8);
  border-radius: inherit;
  transition: width .25s ease;
}

.task-progress > span {
  min-width: 84px;
  color: #74829a;
  font-size: 10px;
  font-weight: 650;
  text-align: right;
}

.task-actions {
  display: flex;
  flex: 0 0 auto;
  flex-direction: column;
  align-items: stretch;
  gap: 8px;
}

.task-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 7px 14px;
  margin-top: 9px;
  color: #94a3b8;
  font-size: 10px;
}

.project-name,
.due-date {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.project-name { color: #64748b; font-weight: 650; }
.prazo-atrasado { color: #dc2626; font-weight: 700; }
.prazo-hoje { color: #d97706; font-weight: 700; }
.archived-label { color: #b45309; }

.status-control {
  flex: 0 0 auto;
}

.status-control select {
  min-width: 122px;
  font-weight: 650;
}

.status-control select:disabled {
  color: #94a3b8;
  background: #f8fafc;
  cursor: not-allowed;
}

.work-toggle,
.submit-update {
  display: inline-flex;
  min-height: 37px;
  align-items: center;
  justify-content: center;
  padding: 0 12px;
  color: #fff;
  background: linear-gradient(135deg, #5b5ce2, #4338ca);
  border: 1px solid #4f46e5;
  border-radius: 8px;
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
  transition: transform .16s ease, box-shadow .16s ease, background .16s ease;
}

.work-toggle:hover,
.submit-update:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 5px 12px rgb(67 56 202 / 18%);
}

.work-toggle:focus-visible,
.submit-update:focus-visible,
.history-refresh:focus-visible,
.worklog-attachments button:focus-visible {
  outline: 3px solid #c7d2fe;
  outline-offset: 2px;
}

.worklog-panel {
  padding: 22px 25px 24px 48px;
  background: linear-gradient(180deg, #f8faff, #fff);
  border-top: 1px solid #edf0f7;
}

.worklog-columns {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 26px;
}

.worklog-composer {
  min-width: 0;
  padding: 18px;
  background: #fff;
  border: 1px solid #e5eaf3;
  border-radius: 13px;
  box-shadow: 0 4px 14px rgb(34 57 103 / 4%);
}

.worklog-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.worklog-heading h5 {
  margin: 5px 0 0;
  color: #243452;
  font-size: 15px;
}

.work-progress-value {
  display: grid;
  min-width: 49px;
  min-height: 35px;
  padding: 0 8px;
  place-items: center;
  color: #4f46e5;
  background: #eef2ff;
  border-radius: 9px;
  font-size: 13px;
  font-weight: 800;
}

.work-field {
  display: flex;
  flex-direction: column;
  gap: 7px;
  margin-bottom: 15px;
}

.work-field > span {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  color: #475569;
  font-size: 11px;
  font-weight: 700;
}

.work-field > span strong {
  color: #4f46e5;
}

.work-field textarea {
  box-sizing: border-box;
  width: 100%;
  min-height: 98px;
  resize: vertical;
  padding: 11px 12px;
  color: #334155;
  background: #fff;
  border: 1px solid #dfe5ef;
  border-radius: 8px;
  font: inherit;
  font-size: 12px;
  line-height: 1.5;
}

.work-field textarea:focus,
.work-field input[type='file']:focus-visible {
  outline: 3px solid #c7d2fe;
  outline-offset: 1px;
  border-color: #818cf8;
}

.work-field textarea:disabled,
.work-field input:disabled {
  background: #f8fafc;
  cursor: not-allowed;
}

.progress-field input {
  width: 100%;
  accent-color: #4f46e5;
}

.work-field input[type='file'] {
  box-sizing: border-box;
  width: 100%;
  padding: 9px;
  color: #64748b;
  background: #f8fafc;
  border: 1px dashed #cbd5e1;
  border-radius: 8px;
  font-size: 10px;
}

.selected-files,
.worklog-attachments {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 0;
  margin: 0 0 13px;
  list-style: none;
}

.selected-files li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 7px 9px;
  color: #526078;
  background: #f4f6fb;
  border-radius: 7px;
  font-size: 10px;
}

.selected-files li span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.selected-files button {
  flex: 0 0 auto;
  color: #b91c1c;
  background: transparent;
  border: 0;
  font-size: 18px;
  cursor: pointer;
}

.submit-update {
  width: 100%;
  min-height: 41px;
  font-size: 12px;
}

.submit-update:disabled {
  opacity: .55;
  cursor: not-allowed;
}

.archived-hint {
  display: block;
  margin-top: 9px;
  color: #b45309;
  font-size: 10px;
}

.worklog-history {
  min-width: 0;
}

.history-refresh {
  display: grid;
  width: 32px;
  height: 32px;
  place-items: center;
  color: #5363bd;
  background: #eef2ff;
  border: 1px solid #e0e5ff;
  border-radius: 8px;
  font-size: 18px;
  cursor: pointer;
}

.history-refresh:disabled {
  opacity: .5;
  cursor: wait;
}

.history-empty {
  padding: 18px;
  color: #8995a8;
  background: #fff;
  border: 1px dashed #dce3ee;
  border-radius: 10px;
  font-size: 11px;
  text-align: center;
}

.worklog-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 480px;
  overflow-y: auto;
  padding: 0 4px 0 0;
  margin: 0;
  list-style: none;
}

.worklog-item {
  padding: 13px 14px;
  background: #fff;
  border: 1px solid #e6ebf3;
  border-radius: 10px;
}

.worklog-item-heading {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  justify-content: space-between;
  gap: 5px 12px;
}

.worklog-item-heading strong {
  color: #344158;
  font-size: 11px;
}

.worklog-item-heading > span {
  color: #94a3b8;
  font-size: 9px;
}

.worklog-item > p {
  margin: 9px 0;
  color: #53627a;
  font-size: 11px;
  line-height: 1.55;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.worklog-progress {
  display: flex;
  justify-content: space-between;
  padding-top: 8px;
  color: #7c879b;
  border-top: 1px solid #f0f2f6;
  font-size: 9px;
}

.worklog-progress strong {
  color: #4f46e5;
}

.worklog-attachments {
  margin: 10px 0 0;
}

.worklog-attachments button {
  display: flex;
  width: 100%;
  align-items: center;
  gap: 7px;
  padding: 7px 8px;
  overflow: hidden;
  color: #4858ad;
  background: #f5f6ff;
  border: 1px solid #e5e8ff;
  border-radius: 7px;
  font-size: 10px;
  text-align: left;
  cursor: pointer;
}

.worklog-attachments button > span {
  flex: 0 0 auto;
  font-size: 15px;
}

.worklog-attachments button small {
  flex: 0 0 auto;
  margin-left: auto;
  color: #8995a8;
  font-size: 9px;
}

.empty-state {
  display: flex;
  min-height: 220px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 24px;
  color: #8b9ab1;
  text-align: center;
}

.empty-state strong {
  color: #334155;
  font-size: 14px;
}

.empty-state > span:last-child {
  max-width: 430px;
  font-size: 12px;
  line-height: 1.5;
}

.compact-empty { min-height: 150px; }

.empty-icon {
  display: grid;
  width: 43px;
  height: 43px;
  margin-bottom: 4px;
  place-items: center;
  color: #6366f1;
  background: #eef2ff;
  border-radius: 13px;
  font-size: 20px;
}

.loading-spinner {
  width: 26px;
  height: 26px;
  border: 3px solid #e0e7ff;
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 1100px) {
  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .member-area { padding: 2px 0 24px; }
  .member-hero {
    align-items: stretch;
    flex-direction: column;
    gap: 17px;
    padding: 24px 20px;
    border-radius: 16px;
  }
  .summary-grid { gap: 9px; }
  .summary-card { padding: 13px; }
  .progress-card { grid-column: span 2; }
  .panel-heading { padding: 19px 16px 15px; }
  .task-filters { flex-wrap: wrap; padding: 0 16px 14px; }
  .search-field { flex-basis: 100%; }
  .task-filters select { flex: 1; }
  .task-row { align-items: flex-start; flex-wrap: wrap; padding: 15px 16px; }
  .task-main { flex-basis: calc(100% - 25px); }
  .task-actions { width: calc(100% - 23px); flex-direction: row; margin-left: 23px; }
  .task-actions > * { flex: 1; }
  .status-control { margin: 0; }
  .work-toggle { min-height: 38px; }
  .worklog-panel { padding: 16px; }
  .worklog-columns { grid-template-columns: 1fr; gap: 20px; }
}

@media (max-width: 420px) {
  .summary-grid { grid-template-columns: 1fr 1fr; }
  .summary-card { grid-template-columns: 32px 1fr; column-gap: 8px; padding: 11px; }
  .summary-icon { width: 32px; height: 32px; }
  .summary-card > div span { font-size: 10px; }
  .summary-card > div strong { font-size: 21px; }
  .summary-card > small { font-size: 9px; }
  .progress-heading { align-items: flex-start; flex-direction: column; }
  .panel-heading h3 { font-size: 18px; }
  .task-filters select { min-width: 0; }
  .task-actions { flex-direction: column; }
  .worklog-panel { padding: 12px; }
  .worklog-composer { padding: 14px; }
}

@media (prefers-reduced-motion: reduce) {
  .loading-spinner { animation-duration: 2s; }
  .task-row, .progress-track > span, .task-progress-track > span,
  .work-toggle, .submit-update { transition: none; }
}
</style>
