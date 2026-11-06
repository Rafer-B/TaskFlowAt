<script setup lang="ts">
import { ref } from 'vue'
import { scrollToPanel } from '~/composables/usePanelScroll'

// Agrega prazos de tarefas e eventos numa grelha que suporta mês, semana e dia.
definePageMeta({
  layout: 'admin',
})

type EstadoTarefa = 'to_do' | 'in_progress' | 'completed' | 'blocked'
type PrioridadeTarefa = 'low' | 'medium' | 'high'
type CorEvento = 'blue' | 'purple' | 'green' | 'red'
type ModoCalendario = 'month' | 'week' | 'day'

interface ProjetoAPI {
  id: number
  name: string
  current_user_role: 'admin' | 'owner' | 'contributor' | 'viewer'
}

interface TarefaAPI {
  id: number
  project_id: number
  title: string
  status: EstadoTarefa
  priority: PrioridadeTarefa
  progress: number
  due_date: string | null
  assigned_to: number | null
}

interface EventoAPI {
  id: number
  project_id: number | null
  title: string
  description: string | null
  start_at: string
  end_at: string
  color: CorEvento
  created_by: number
}

interface ItemCalendario {
  id: string
  tipo: 'task' | 'event'
  titulo: string
  projeto: string
  projectId: number | null
  data: string
  hora: string | null
  cor: string
  estado?: EstadoTarefa
  prioridade?: PrioridadeTarefa
  progresso?: number
  eventoId?: number
  criadorId?: number
  descricao?: string
}

interface DiaCalendario {
  iso: string
  numero: number
  noMesAtual: boolean
  hoje: boolean
  itens: ItemCalendario[]
}

interface CabecalhoDia {
  key: string
  nome: string
  numero: number | null
  hoje: boolean
}

interface FormularioEvento {
  id: number | null
  projectId: string
  title: string
  description: string
  startAt: string
  endAt: string
  color: CorEvento
}

const api = useNuxtApp().$api
const auth = useAuth()
const projetos = ref<ProjetoAPI[]>([])
const tarefas = ref<TarefaAPI[]>([])
const eventos = ref<EventoAPI[]>([])
const carregando = ref(true)
const erro = ref('')
const sucesso = ref('')
const guardandoEvento = ref(false)
const formularioEventoVisivel = ref(false)
const formularioEventoRef = ref<HTMLElement | null>(null)
const confirmarEliminacaoEvento = ref(false)
const mostrarEventosAnteriores = ref(false)
const modo = ref<ModoCalendario>('month')
const agora = new Date()
const hojeISO = toIsoDate(agora)
const mesVisivel = ref(new Date(agora.getFullYear(), agora.getMonth(), 1))
const diaSelecionado = ref(hojeISO)
const projetoSelecionado = ref('all')
const filtros = ref({
  tarefas: true,
  projetos: true,
  eventos: true,
  bloqueadas: true,
})
const formulario = ref<FormularioEvento>(novoFormularioEvento())

const nomesDiasSemana = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
const titulosDiasSemana = [
  'Segunda-feira', 'Terça-feira', 'Quarta-feira',
  'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo',
]
const coresEvento: { value: CorEvento; label: string; color: string }[] = [
  { value: 'blue', label: 'Azul', color: '#3478f6' },
  { value: 'purple', label: 'Roxo', color: '#a125f4' },
  { value: 'green', label: 'Verde', color: '#31ad5b' },
  { value: 'red', label: 'Vermelho', color: '#ef4e5e' },
]

const projetosEditaveis = computed(() =>
  projetos.value.filter(projeto =>
    auth.user.value?.role === 'admin' ||
    projeto.current_user_role === 'owner' ||
    projeto.current_user_role === 'contributor',
  ),
)

// Converte os dois tipos de registo para um formato único usado pela grelha e pela lista.
const todosItens = computed<ItemCalendario[]>(() => {
  const nomesProjetos = new Map(projetos.value.map(projeto => [projeto.id, projeto.name]))
  const tarefasCalendario = tarefas.value
    .filter(tarefa => tarefa.due_date)
    .map<ItemCalendario>(tarefa => ({
      id: `task-${tarefa.id}`,
      tipo: 'task',
      titulo: tarefa.title,
      projeto: nomesProjetos.get(tarefa.project_id) ?? 'Projeto desconhecido',
      projectId: tarefa.project_id,
      data: tarefa.due_date!.slice(0, 10),
      hora: null,
      cor: tarefa.status === 'blocked'
        ? 'red'
        : tarefa.priority === 'high'
          ? 'blue'
          : tarefa.priority === 'medium'
            ? 'purple'
            : 'green',
      estado: tarefa.status,
      prioridade: tarefa.priority,
      progresso: tarefa.progress,
    }))
  const eventosCalendario = eventos.value.map<ItemCalendario>(evento => ({
    id: `event-${evento.id}`,
    tipo: 'event',
    titulo: evento.title,
    projeto: evento.project_id
      ? nomesProjetos.get(evento.project_id) ?? 'Projeto desconhecido'
      : 'Evento pessoal',
    projectId: evento.project_id,
    data: dataLocal(evento.start_at),
    hora: horaLocal(evento.start_at),
    cor: evento.color,
    eventoId: evento.id,
    criadorId: evento.created_by,
    descricao: evento.description ?? '',
  }))

  return [...tarefasCalendario, ...eventosCalendario]
})

const itensVisiveis = computed(() =>
  todosItens.value.filter(item => {
    if (projetoSelecionado.value !== 'all' && item.projectId !== Number(projetoSelecionado.value)) {
      return false
    }

    if (item.tipo === 'task') {
      if (item.estado === 'blocked') return filtros.value.bloqueadas
      return filtros.value.tarefas
    }

    if (item.projectId !== null) return filtros.value.projetos
    return filtros.value.eventos
  }),
)

// Calcula a janela visível com semanas iniciadas à segunda-feira, incluindo dias adjacentes.
const diasCalendario = computed<DiaCalendario[]>(() => {
  let inicio: Date
  let quantidade: number

  if (modo.value === 'day') {
    inicio = fromIsoDate(diaSelecionado.value)
    quantidade = 1
  } else if (modo.value === 'week') {
    const selecionado = fromIsoDate(diaSelecionado.value)
    const deslocamento = (selecionado.getDay() + 6) % 7
    inicio = new Date(selecionado.getFullYear(), selecionado.getMonth(), selecionado.getDate() - deslocamento)
    quantidade = 7
  } else {
    const primeiroDia = new Date(mesVisivel.value.getFullYear(), mesVisivel.value.getMonth(), 1)
    const deslocamento = (primeiroDia.getDay() + 6) % 7
    const totalDias = new Date(mesVisivel.value.getFullYear(), mesVisivel.value.getMonth() + 1, 0).getDate()
    quantidade = Math.ceil((deslocamento + totalDias) / 7) * 7
    inicio = new Date(primeiroDia.getFullYear(), primeiroDia.getMonth(), 1 - deslocamento)
  }

  return Array.from({ length: quantidade }, (_, indice) => {
    const data = new Date(inicio.getFullYear(), inicio.getMonth(), inicio.getDate() + indice)
    const iso = toIsoDate(data)
    return {
      iso,
      numero: data.getDate(),
      noMesAtual: data.getMonth() === mesVisivel.value.getMonth(),
      hoje: iso === hojeISO,
      itens: itensVisiveis.value
        .filter(item => item.data === iso)
        .sort((a, b) => (a.hora ?? '').localeCompare(b.hora ?? '')),
    }
  })
})

const cabecalhosDia = computed<CabecalhoDia[]>(() => {
  if (modo.value === 'month') {
    return nomesDiasSemana.map((nome, indice) => ({
      key: nome,
      nome,
      numero: null,
      hoje: false,
    }))
  }

  return diasCalendario.value.map(dia => ({
    key: dia.iso,
    nome: nomesDiasSemana[(fromIsoDate(dia.iso).getDay() + 6) % 7],
    numero: dia.numero,
    hoje: dia.hoje,
  }))
})

const tarefasDoMes = computed(() => tarefas.value.filter(tarefa =>
  tarefa.due_date?.slice(0, 7) === toIsoDate(mesVisivel.value).slice(0, 7),
))
const tarefasConcluidas = computed(() =>
  tarefasDoMes.value.filter(tarefa => tarefa.status === 'completed').length,
)
const progressoMes = computed(() => tarefasDoMes.value.length
  ? Math.round(tarefasConcluidas.value / tarefasDoMes.value.length * 100)
  : 0)

// Limita a agenda aos próximos três itens, salvo quando o utilizador pede para a expandir.
const eventosProximos = computed(() =>
  itensVisiveis.value
    .filter(item => item.data >= hojeISO)
    .sort((a, b) => a.data.localeCompare(b.data) || (a.hora ?? '').localeCompare(b.hora ?? ''))
    .slice(0, mostrarEventosAnteriores.value ? undefined : 3),
)

const tituloPeriodo = computed(() => {
  if (modo.value === 'month') {
    return new Intl.DateTimeFormat('pt-PT', { month: 'long', year: 'numeric' }).format(mesVisivel.value)
  }
  if (modo.value === 'day') {
    return formatarDataLonga(diaSelecionado.value)
  }

  const inicio = diasCalendario.value[0]?.iso
  const fim = diasCalendario.value[diasCalendario.value.length - 1]?.iso
  if (!inicio || !fim) return ''

  const dataInicio = fromIsoDate(inicio)
  const dataFim = fromIsoDate(fim)
  const formatDiaMes = new Intl.DateTimeFormat('pt-PT', { day: 'numeric', month: 'short' })
  return `${formatDiaMes.format(dataInicio)} – ${formatarDataLonga(toIsoDate(dataFim))}`
})

const tituloDiaSelecionado = computed(() => {
  const data = fromIsoDate(diaSelecionado.value)
  return new Intl.DateTimeFormat('pt-PT', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  }).format(data)
})

function novoFormularioEvento(): FormularioEvento {
  const inicio = new Date()
  inicio.setMinutes(0, 0, 0)
  inicio.setHours(inicio.getHours() + 1)
  const fim = new Date(inicio)
  fim.setHours(fim.getHours() + 1)

  return {
    id: null,
    projectId: '',
    title: '',
    description: '',
    startAt: toDateTimeLocal(inicio),
    endAt: toDateTimeLocal(fim),
    color: 'purple',
  }
}

function toDateTimeLocal(data: Date): string {
  const deslocamento = data.getTimezoneOffset() * 60_000
  return new Date(data.getTime() - deslocamento).toISOString().slice(0, 16)
}

function dataLocal(iso: string): string {
  return toIsoDate(new Date(iso))
}

function horaLocal(iso: string): string {
  return new Intl.DateTimeFormat('pt-PT', { hour: '2-digit', minute: '2-digit' }).format(new Date(iso))
}

function toIsoDate(data: Date): string {
  const year = data.getFullYear()
  const month = String(data.getMonth() + 1).padStart(2, '0')
  const day = String(data.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function fromIsoDate(iso: string): Date {
  const [year, month, day] = iso.split('-').map(Number)
  return new Date(year, month - 1, day)
}

function formatarDataLonga(iso: string): string {
  return new Intl.DateTimeFormat('pt-PT', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  }).format(fromIsoDate(iso))
}

function classeItem(item: ItemCalendario): string {
  if (item.tipo === 'task' && item.estado === 'completed') return 'item-completed'
  if (item.tipo === 'task' && item.estado === 'blocked') return 'item-red'
  if (item.tipo === 'task') return `item-${item.cor}`
  return `item-${item.cor}`
}

function alterarPeriodo(offset: number): void {
  if (modo.value === 'month') {
    mesVisivel.value = new Date(mesVisivel.value.getFullYear(), mesVisivel.value.getMonth() + offset, 1)
    diaSelecionado.value = toIsoDate(mesVisivel.value)
    return
  }

  const dias = modo.value === 'week' ? 7 : 1
  const atual = fromIsoDate(diaSelecionado.value)
  const novoDia = new Date(atual.getFullYear(), atual.getMonth(), atual.getDate() + offset * dias)
  diaSelecionado.value = toIsoDate(novoDia)
  mesVisivel.value = new Date(novoDia.getFullYear(), novoDia.getMonth(), 1)
}

function irParaHoje(): void {
  mesVisivel.value = new Date(agora.getFullYear(), agora.getMonth(), 1)
  diaSelecionado.value = hojeISO
}

function selecionarDia(dia: DiaCalendario): void {
  diaSelecionado.value = dia.iso
  mesVisivel.value = new Date(fromIsoDate(dia.iso).getFullYear(), fromIsoDate(dia.iso).getMonth(), 1)
}

function mudarModo(novoModo: ModoCalendario): void {
  modo.value = novoModo
  if (novoModo === 'month') {
    mesVisivel.value = new Date(fromIsoDate(diaSelecionado.value).getFullYear(), fromIsoDate(diaSelecionado.value).getMonth(), 1)
  }
}

async function abrirNovoEvento(): Promise<void> {
  formulario.value = novoFormularioEvento()
  const horaInicio = formulario.value.startAt.slice(11)
  formulario.value.startAt = `${diaSelecionado.value}T${horaInicio}`
  const dataFim = new Date(`${formulario.value.startAt}:00`)
  dataFim.setHours(dataFim.getHours() + 1)
  formulario.value.endAt = toDateTimeLocal(dataFim)
  if (projetoSelecionado.value !== 'all') {
    formulario.value.projectId = projetoSelecionado.value
  }
  erro.value = ''
  formularioEventoVisivel.value = true
  confirmarEliminacaoEvento.value = false
  await scrollToPanel(formularioEventoRef)
}

async function editarEvento(item: ItemCalendario): Promise<void> {
  const evento = eventos.value.find(candidato => candidato.id === item.eventoId)
  if (!evento) return

  formulario.value = {
    id: evento.id,
    projectId: evento.project_id === null ? '' : String(evento.project_id),
    title: evento.title,
    description: evento.description ?? '',
    startAt: toDateTimeLocal(new Date(evento.start_at)),
    endAt: toDateTimeLocal(new Date(evento.end_at)),
    color: evento.color,
  }
  erro.value = ''
  formularioEventoVisivel.value = true
  confirmarEliminacaoEvento.value = false
  await scrollToPanel(formularioEventoRef)
}

function podeGerirEvento(item: ItemCalendario): boolean {
  // Administradores, criadores e responsáveis do projeto podem gerir os eventos correspondentes.
  if (item.tipo !== 'event') return false
  if (auth.user.value?.role === 'admin' || item.criadorId === auth.user.value?.id) return true
  return projetos.value.some(projeto =>
    projeto.id === item.projectId && projeto.current_user_role === 'owner',
  )
}

function abrirItemCalendario(item: ItemCalendario): void {
  diaSelecionado.value = item.data
  if (item.tipo === 'event' && podeGerirEvento(item)) {
    editarEvento(item)
  }
}

async function guardarEvento(): Promise<void> {
  const dados = formulario.value
  if (new Date(dados.endAt) <= new Date(dados.startAt)) {
    erro.value = 'A data de fim tem de ser posterior à data de início.'
    return
  }

  guardandoEvento.value = true
  erro.value = ''
  sucesso.value = ''

  const payload = {
    project_id: dados.projectId ? Number(dados.projectId) : null,
    title: dados.title.trim(),
    description: dados.description.trim() || null,
    start_at: new Date(dados.startAt).toISOString(),
    end_at: new Date(dados.endAt).toISOString(),
    color: dados.color,
  }

  try {
    // O mesmo formulário cria ou atualiza, conforme exista um identificador selecionado.
    const evento = dados.id
      ? await api<EventoAPI>(`/calendar/events/${dados.id}`, { method: 'PATCH', body: payload })
      : await api<EventoAPI>('/calendar/events/', { method: 'POST', body: payload })

    const indice = eventos.value.findIndex(candidato => candidato.id === evento.id)
    if (indice === -1) eventos.value.push(evento)
    else eventos.value[indice] = evento

    diaSelecionado.value = dataLocal(evento.start_at)
    mesVisivel.value = new Date(fromIsoDate(diaSelecionado.value).getFullYear(), fromIsoDate(diaSelecionado.value).getMonth(), 1)
    formularioEventoVisivel.value = false
    confirmarEliminacaoEvento.value = false
    sucesso.value = dados.id ? 'Evento atualizado com sucesso.' : 'Evento criado com sucesso.'
  } catch (error) {
    console.error('Erro ao guardar evento:', error)
    erro.value = mensagemErro(error)
  } finally {
    guardandoEvento.value = false
  }
}

async function eliminarEvento(): Promise<void> {
  const eventId = formulario.value.id
  if (!eventId) return
  if (!confirmarEliminacaoEvento.value) {
    confirmarEliminacaoEvento.value = true
    return
  }

  guardandoEvento.value = true
  erro.value = ''
  try {
    await api(`/calendar/events/${eventId}`, { method: 'DELETE' })
    eventos.value = eventos.value.filter(evento => evento.id !== eventId)
    formularioEventoVisivel.value = false
    confirmarEliminacaoEvento.value = false
    sucesso.value = 'Evento eliminado.'
  } catch (error) {
    console.error('Erro ao eliminar evento:', error)
    erro.value = mensagemErro(error)
  } finally {
    guardandoEvento.value = false
  }
}

function mensagemErro(error: unknown): string {
  if (typeof error === 'object' && error !== null && 'data' in error) {
    const data = error.data
    if (typeof data === 'object' && data !== null && 'detail' in data && typeof data.detail === 'string') {
      return data.detail
    }
  }
  return 'Não foi possível guardar a alteração. Tente novamente.'
}

async function carregarCalendario(): Promise<void> {
  carregando.value = true
  erro.value = ''

  try {
    // Carrega em paralelo projetos, tarefas e eventos para compor o calendário inicial.
    const [projetosAPI, tarefasAPI, eventosAPI] = await Promise.all([
      api<ProjetoAPI[]>('/projects/'),
      api<TarefaAPI[]>('/tasks/'),
      api<EventoAPI[]>('/calendar/events/'),
    ])
    projetos.value = projetosAPI
    tarefas.value = tarefasAPI
    eventos.value = eventosAPI
  } catch (error) {
    console.error('Erro ao carregar o calendário:', error)
    erro.value = mensagemErro(error)
  } finally {
    carregando.value = false
  }
}

onMounted(carregarCalendario)
</script>

<template>
  <section class="calendar-page">
    <header class="calendar-heading">
      <div class="calendar-icon" aria-hidden="true">
        <svg viewBox="0 0 64 64" fill="none">
          <rect x="10" y="13" width="44" height="43" rx="8" fill="#fff" stroke="#2864e8" stroke-width="3" />
          <path d="M21 8v12M43 8v12M11 25h42" stroke="#174fc5" stroke-width="5" stroke-linecap="round" />
          <path d="M19 33h8v7h-8zm18 0h8v7h-8zm-18 13h8v6h-8zm18 0h8v6h-8z" fill="#548aff" />
        </svg>
      </div>
      <div class="heading-copy">
        <h1>Calendário</h1>
        <p>Visualize os seus eventos e tarefas</p>
      </div>
      <div class="calendar-heading-actions">
        <div class="period-control" aria-label="Navegar no calendário">
          <button type="button" aria-label="Período anterior" @click="alterarPeriodo(-1)">‹</button>
          <strong>{{ tituloPeriodo }}</strong>
          <button type="button" aria-label="Período seguinte" @click="alterarPeriodo(1)">›</button>
        </div>
        <div class="view-switch" aria-label="Modo de visualização">
          <button
            v-for="opcao in [{ value: 'month', label: 'Mês' }, { value: 'week', label: 'Semana' }, { value: 'day', label: 'Dia' }]"
            :key="opcao.value"
            type="button"
            :class="{ 'view-active': modo === opcao.value }"
            :aria-pressed="modo === opcao.value"
            @click="mudarModo(opcao.value as ModoCalendario)"
          >
            {{ opcao.label }}
          </button>
        </div>
        <button class="today-button" type="button" @click="irParaHoje">Hoje</button>
        <button class="create-event-button" type="button" @click="abrirNovoEvento">
          <span aria-hidden="true">＋</span> Novo evento
        </button>
      </div>
    </header>

    <div v-if="erro" class="notice notice-error" role="alert">
      <span>{{ erro }}</span>
      <button type="button" @click="carregarCalendario">Tentar novamente</button>
    </div>
    <div v-if="sucesso" class="notice notice-success" role="status">
      <span>{{ sucesso }}</span>
      <button type="button" aria-label="Fechar mensagem" @click="sucesso = ''">×</button>
    </div>

    <div class="calendar-main">
      <aside class="calendar-sidebar">
        <section class="filters-card" aria-label="Filtros do calendário">
          <h2><span aria-hidden="true">▽</span> Filtros</h2>
          <label class="filter-option">
            <input v-model="filtros.tarefas" type="checkbox">
            <span class="filter-check filter-blue"></span>
            Tarefas
          </label>
          <label class="filter-option">
            <input v-model="filtros.projetos" type="checkbox">
            <span class="filter-check filter-purple"></span>
            Projetos
          </label>
          <label class="filter-option">
            <input v-model="filtros.eventos" type="checkbox">
            <span class="filter-check filter-green"></span>
            Eventos
          </label>
          <label class="filter-option">
            <input v-model="filtros.bloqueadas" type="checkbox">
            <span class="filter-check filter-red"></span>
            Bloqueadas
          </label>
          <label class="project-filter">
            <span>Projeto</span>
            <select v-model="projetoSelecionado" aria-label="Filtrar por projeto">
              <option value="all">Todos</option>
              <option v-for="projeto in projetos" :key="projeto.id" :value="String(projeto.id)">
                {{ projeto.name }}
              </option>
            </select>
          </label>
        </section>

        <section class="month-summary" aria-label="Resumo do mês">
          <h2>Resumo do mês</h2>
          <div class="completion-donut" :style="{ '--completion': `${progressoMes}%` }">
            <div>
              <strong>{{ progressoMes }}%</strong>
              <span>Concluídas</span>
            </div>
          </div>
          <div class="summary-numbers">
            <div><strong>{{ tarefasDoMes.length }}</strong><span>Tarefas totais</span></div>
            <div><strong>{{ tarefasConcluidas }}</strong><span>Concluídas</span></div>
          </div>
        </section>
      </aside>

      <section class="calendar-content">
        <div v-if="carregando" class="calendar-loading" role="status">A carregar calendário…</div>
        <div v-else-if="!erro" class="calendar-grid-wrap">
          <div
            class="calendar-grid"
            :class="`calendar-${modo}`"
            role="grid"
            :aria-label="`Calendário ${modo}: ${tituloPeriodo}`"
          >
            <div
              v-for="dia in cabecalhosDia"
              :key="`header-${dia.key}`"
              class="weekday-heading"
              :class="{ 'weekday-selected': dia.key === diaSelecionado }"
              role="columnheader"
              :aria-label="dia.numero === null ? titulosDiasSemana[nomesDiasSemana.indexOf(dia.nome)] : `${dia.nome} ${dia.numero}`"
            >
              <span>{{ dia.nome }}</span>
              <strong v-if="dia.numero !== null" :class="{ 'today-number': dia.hoje }">{{ dia.numero }}</strong>
            </div>
            <button
              v-for="dia in diasCalendario"
              :key="dia.iso"
              class="calendar-day"
              :class="{
                'day-outside': !dia.noMesAtual && modo === 'month',
                'day-today': dia.hoje,
                'day-selected': dia.iso === diaSelecionado,
              }"
              type="button"
              role="gridcell"
              :aria-label="`${formatarDataLonga(dia.iso)}, ${dia.itens.length} elemento(s)`"
              :aria-pressed="dia.iso === diaSelecionado"
              @click="selecionarDia(dia)"
            >
              <span v-if="modo === 'month'" class="day-number" :class="{ 'today-number': dia.hoje }">
                {{ dia.numero }}
              </span>
              <span
                v-for="item in dia.itens.slice(0, modo === 'month' ? 3 : 20)"
                :key="item.id"
                class="calendar-item-chip"
                :class="[classeItem(item), { 'item-editable': item.tipo === 'event' && podeGerirEvento(item) }]"
                :title="item.tipo === 'event' && podeGerirEvento(item) ? 'Clique para editar' : `${item.titulo} · ${item.projeto}`"
                @click.stop="abrirItemCalendario(item)"
              >
                <i></i>
                <span v-if="item.hora" class="item-time">{{ item.hora }}</span>
                {{ item.titulo }}
              </span>
              <span v-if="modo === 'month' && dia.itens.length > 3" class="more-items">
                +{{ dia.itens.length - 3 }} mais
              </span>
              <span v-if="modo !== 'month' && !dia.itens.length" class="empty-day">
                Sem eventos
              </span>
            </button>
          </div>
          <div class="calendar-legend">
            <span><i class="legend-dot legend-blue"></i>Tarefas</span>
            <span><i class="legend-dot legend-purple"></i>Projetos</span>
            <span><i class="legend-dot legend-green"></i>Eventos</span>
            <span><i class="legend-dot legend-red"></i>Bloqueadas</span>
          </div>
        </div>
      </section>
    </div>

    <section class="upcoming-banner">
      <div class="upcoming-intro">
        <span class="bulb-icon" aria-hidden="true">♧</span>
        <div>
          <strong>Próximos eventos</strong>
          <span>Veja o que se segue nos próximos dias.</span>
        </div>
      </div>
      <ul class="upcoming-list">
        <li v-for="item in eventosProximos" :key="item.id">
          <button class="upcoming-item" type="button" @click="abrirItemCalendario(item)">
            <i class="legend-dot" :class="`legend-${item.tipo === 'task' && item.estado === 'blocked' ? 'red' : item.cor}`"></i>
            <strong>{{ fromIsoDate(item.data).getDate() }} {{ new Intl.DateTimeFormat('pt-PT', { month: 'short' }).format(fromIsoDate(item.data)) }}</strong>
            <span>{{ item.titulo }}</span>
          </button>
        </li>
        <li v-if="!eventosProximos.length" class="upcoming-empty">Não existem eventos ou prazos próximos.</li>
      </ul>
      <button
        v-if="itensVisiveis.filter(item => item.data >= hojeISO).length > 3"
        class="all-events-button"
        type="button"
        @click="mostrarEventosAnteriores = !mostrarEventosAnteriores"
      >
        {{ mostrarEventosAnteriores ? 'Mostrar menos' : 'Ver todos os eventos' }}
        <span aria-hidden="true">→</span>
      </button>
    </section>

    <!-- O mesmo formulário suporta criação e edição; a capacidade é verificada no script. -->
    <section v-if="formularioEventoVisivel" ref="formularioEventoRef" class="event-inline-panel">
        <header class="form-panel-heading">
          <div>
            <span class="form-panel-eyebrow">CALENDÁRIO</span>
            <h2 id="event-form-title">{{ formulario.id ? 'Editar evento' : 'Criar evento' }}</h2>
          </div>
          <button type="button" aria-label="Fechar" :disabled="guardandoEvento" @click="formularioEventoVisivel = false; confirmarEliminacaoEvento = false">×</button>
        </header>
        <form class="event-form" @submit.prevent="guardarEvento">
          <label>
            Título
            <input v-model="formulario.title" type="text" maxlength="255" required placeholder="Ex.: Reunião de equipa">
          </label>
          <label>
            Projeto
            <select v-model="formulario.projectId">
              <option value="">Evento pessoal</option>
              <option v-for="projeto in projetosEditaveis" :key="projeto.id" :value="String(projeto.id)">
                {{ projeto.name }}
              </option>
            </select>
          </label>
          <div class="datetime-fields">
            <label>
              Início
              <input v-model="formulario.startAt" type="datetime-local" required>
            </label>
            <label>
              Fim
              <input v-model="formulario.endAt" type="datetime-local" required>
            </label>
          </div>
          <label>
            Descrição
            <textarea v-model="formulario.description" rows="3" maxlength="5000" placeholder="Detalhes do evento (opcional)"></textarea>
          </label>
          <fieldset class="color-picker">
            <legend>Cor do evento</legend>
            <label v-for="cor in coresEvento" :key="cor.value" :title="cor.label">
              <input v-model="formulario.color" type="radio" name="event-color" :value="cor.value">
              <span :style="{ '--event-color': cor.color }"></span>
              <small>{{ cor.label }}</small>
            </label>
          </fieldset>
          <p v-if="erro" class="form-error" role="alert">{{ erro }}</p>
          <div v-if="confirmarEliminacaoEvento" class="inline-confirm" role="group" aria-label="Confirmar eliminação do evento">
            <span>Eliminar o evento “{{ formulario.title }}”?</span>
            <button class="delete-button" type="button" :disabled="guardandoEvento" @click="eliminarEvento">Confirmar eliminação</button>
            <button class="cancel-button" type="button" :disabled="guardandoEvento" @click="confirmarEliminacaoEvento = false">Cancelar</button>
          </div>
          <footer class="form-panel-actions">
            <button
              v-if="formulario.id && !confirmarEliminacaoEvento"
              class="delete-button"
              type="button"
              :disabled="guardandoEvento"
              @click="eliminarEvento"
            >
              Eliminar
            </button>
            <button class="cancel-button" type="button" :disabled="guardandoEvento" @click="formularioEventoVisivel = false; confirmarEliminacaoEvento = false">Cancelar</button>
            <button class="save-button" type="submit" :disabled="guardandoEvento">
              {{ guardandoEvento ? 'A guardar…' : formulario.id ? 'Guardar alterações' : 'Criar evento' }}
            </button>
          </footer>
        </form>
    </section>
  </section>
</template>

<style scoped>
.calendar-page { display: grid; gap: 14px; color: #17264a; }
.calendar-heading { display: flex; min-height: 72px; align-items: center; gap: 14px; }
.calendar-icon { display: grid; width: 76px; height: 74px; flex: 0 0 76px; place-items: center; background: radial-gradient(circle at 30% 35%, #cbdcff 0 24%, transparent 25%), radial-gradient(circle at 82% 10%, #d8e3ff 0 20%, transparent 21%); }
.calendar-icon svg { width: 64px; height: 64px; filter: drop-shadow(0 5px 5px rgb(42 89 198 / 16%)); }
.heading-copy { min-width: 190px; }
.heading-copy h1 { margin: 0 0 3px; color: #111d42; font-size: clamp(24px, 3vw, 31px); font-weight: 750; letter-spacing: -.05em; }
.heading-copy p { margin: 0; color: #68789d; font-size: 12px; }
.calendar-heading-actions { display: flex; align-items: center; gap: 8px; margin-left: auto; }
.period-control { display: flex; height: 37px; align-items: center; gap: 12px; padding: 0 9px; background: #fff; border: 1px solid #e8ecf7; border-radius: 20px; }
.period-control button { display: grid; width: 24px; height: 28px; place-items: center; color: #4b5c82; background: transparent; border: 0; font-size: 23px; cursor: pointer; }
.period-control strong { min-width: 91px; color: #25365e; font-size: 11px; font-weight: 700; text-align: center; text-transform: capitalize; white-space: nowrap; }
.view-switch { display: flex; gap: 2px; padding: 3px; background: #eef1fa; border-radius: 12px; }
.view-switch button { min-height: 29px; padding: 0 11px; color: #526284; background: transparent; border: 0; border-radius: 9px; font-size: 10px; font-weight: 600; cursor: pointer; }
.view-switch button.view-active { color: #fff; background: #2f6df6; box-shadow: 0 3px 8px rgb(47 109 246 / 22%); }
.today-button { min-height: 34px; padding: 0 11px; color: #475b86; background: #fff; border: 1px solid #e3e8f4; border-radius: 9px; font-size: 10px; font-weight: 650; cursor: pointer; }
.create-event-button, .all-events-button { display: inline-flex; min-height: 36px; align-items: center; justify-content: center; gap: 6px; padding: 0 12px; color: #fff; background: linear-gradient(110deg, #3479ff, #2c61ed); border: 0; border-radius: 18px; box-shadow: 0 5px 12px rgb(48 105 239 / 20%); font-size: 10px; font-weight: 700; cursor: pointer; white-space: nowrap; }
.create-event-button:hover, .all-events-button:hover { background: #2459df; }
.notice { display: flex; align-items: center; justify-content: space-between; gap: 10px; padding: 10px 13px; border-radius: 8px; font-size: 11px; }
.notice-error { color: #a53d47; background: #fff3f3; border: 1px solid #f7d8db; }
.notice-success { color: #247650; background: #edfaf3; border: 1px solid #d5f1e2; }
.notice button { padding: 6px 9px; color: inherit; background: #fff; border: 1px solid currentColor; border-radius: 6px; cursor: pointer; }
.calendar-main { display: grid; grid-template-columns: 160px minmax(0, 1fr); gap: 10px; }
.calendar-sidebar { display: flex; flex-direction: column; padding: 13px 11px; background: #fff; border: 1px solid #e4e9f4; border-radius: 13px; }
.filters-card { display: grid; gap: 9px; padding-bottom: 15px; border-bottom: 1px solid #edf0f7; }
.filters-card h2 { display: flex; align-items: center; gap: 8px; margin: 0 0 3px; color: #24365d; font-size: 12px; font-weight: 750; }
.filters-card h2 span { color: #455b8d; font-size: 15px; }
.filter-option { display: flex; align-items: center; gap: 9px; color: #34466d; font-size: 11px; cursor: pointer; }
.filter-option input { position: absolute; width: 1px; height: 1px; opacity: 0; }
.filter-check { display: grid; width: 15px; height: 15px; place-items: center; color: #fff; border-radius: 4px; }
.filter-check::after { content: ''; width: 6px; height: 3px; transform: rotate(-45deg); border-bottom: 2px solid currentColor; border-left: 2px solid currentColor; }
.filter-option input:not(:checked) + .filter-check { background: #fff; border: 1px solid #cbd4e4; }
.filter-blue { background: #3478f6; }
.filter-purple { background: #a724f2; }
.filter-green { background: #35b35d; }
.filter-red { background: #f04e5d; }
.filter-option input:focus-visible + .filter-check { outline: 3px solid #b8caff; outline-offset: 2px; }
.project-filter { display: grid; gap: 5px; margin-top: 6px; color: #7683a0; font-size: 9px; }
.project-filter select { width: 100%; height: 30px; padding: 0 7px; color: #405176; background: #fff; border: 1px solid #e3e8f2; border-radius: 7px; font-size: 10px; }
.month-summary { padding: 15px 0 0; }
.month-summary h2 { margin: 0 0 11px; color: #26375e; font-size: 11px; font-weight: 750; }
.completion-donut { display: grid; width: 92px; height: 92px; place-items: center; margin: 0 auto 10px; background: conic-gradient(#31ac5a var(--completion), #d9e3ff var(--completion)); border-radius: 50%; transform: rotate(-90deg); }
.completion-donut::before { position: absolute; width: 76px; height: 76px; background: #fff; border-radius: 50%; content: ''; }
.completion-donut > div { z-index: 1; display: grid; gap: 3px; transform: rotate(90deg); text-align: center; }
.completion-donut strong { color: #17264a; font-size: 18px; font-weight: 800; }
.completion-donut span { color: #415477; font-size: 8px; }
.summary-numbers { display: grid; grid-template-columns: 1fr 1fr; }
.summary-numbers > div { display: grid; gap: 2px; justify-items: center; }
.summary-numbers > div + div { border-left: 1px solid #e8edf7; }
.summary-numbers strong { color: #1d2e53; font-size: 17px; font-weight: 750; }
.summary-numbers span { color: #7785a3; font-size: 8px; text-align: center; }
.calendar-content { min-width: 0; }
.calendar-grid-wrap { padding: 0; overflow: hidden; background: #fff; border: 1px solid #e0e7f4; border-radius: 12px; }
.calendar-grid { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); }
.weekday-heading { display: flex; min-height: 33px; align-items: center; justify-content: center; gap: 5px; color: #53658b; background: #f5f7fc; border-right: 1px solid #e7ebf4; border-bottom: 1px solid #e3e9f5; font-size: 10px; font-weight: 650; }
.weekday-heading:nth-child(7n) { border-right: 0; }
.weekday-heading strong { color: #33466f; font-size: 10px; }
.weekday-selected { background: #edf2ff; }
.today-number { display: grid; width: 22px; height: 22px; place-items: center; color: #fff !important; background: #3476f6; border-radius: 50%; }
.calendar-day { display: flex; min-width: 0; min-height: 72px; flex-direction: column; align-items: stretch; gap: 3px; padding: 5px 5px 4px; overflow: hidden; color: #263653; background: #fff; border: 0; border-right: 1px solid #e8edf5; border-bottom: 1px solid #e8edf5; text-align: left; cursor: pointer; transition: background .15s ease; }
.calendar-day:nth-child(7n) { border-right: 0; }
.calendar-day:hover { background: #f8faff; }
.calendar-day.day-outside { background: #fafbfd; }
.calendar-day.day-outside .day-number { color: #8896b4; }
.calendar-day.day-selected { background: #f0f3ff; box-shadow: inset 0 0 0 1px #b8caff; }
.day-number { display: grid; width: 20px; height: 20px; flex: 0 0 20px; place-items: center; color: #263653; border-radius: 50%; font-size: 10px; }
.day-today:not(.day-selected) { background: #fbfcff; }
.calendar-week .calendar-day { min-height: 352px; }
.calendar-day-view { grid-template-columns: 1fr; }
.calendar-day-view .weekday-heading { min-height: 37px; }
.calendar-day-view .calendar-day { min-height: 320px; }
.calendar-item-chip { display: flex; min-width: 0; min-height: 17px; align-items: center; gap: 4px; padding: 2px 4px; overflow: hidden; border-radius: 5px; font-size: 8px; font-weight: 600; line-height: 1.25; text-overflow: ellipsis; white-space: nowrap; }
.calendar-item-chip.item-editable { cursor: pointer; }
.calendar-item-chip > i { width: 7px; height: 7px; flex: 0 0 7px; background: currentColor; border-radius: 50%; }
.calendar-item-chip > span:last-child { overflow: hidden; text-overflow: ellipsis; }
.item-time { flex: 0 0 auto; font-size: 7px; font-variant-numeric: tabular-nums; }
.item-blue { color: #1c56c7; background: #e8efff; }
.item-purple { color: #8114c3; background: #f5eaff; }
.item-green { color: #187b3c; background: #e9f7ec; }
.item-red { color: #b92b3b; background: #ffeaed; }
.item-completed { color: #27854e; background: #e9f7ec; }
.more-items { padding-left: 4px; color: #71809f; font-size: 8px; font-weight: 700; }
.empty-day { display: grid; flex: 1; place-items: center; color: #bac3d2; font-size: 10px; }
.calendar-legend { display: flex; flex-wrap: wrap; gap: 13px; padding: 9px 12px; color: #73819d; background: #fff; border-top: 1px solid #edf0f6; font-size: 8px; }
.calendar-legend > span { display: inline-flex; align-items: center; gap: 5px; }
.legend-dot { display: inline-block; width: 8px; height: 8px; flex: 0 0 8px; border-radius: 50%; }
.legend-blue { background: #3478f6; }
.legend-purple { background: #a724f2; }
.legend-green { background: #35b35d; }
.legend-red { background: #f04e5d; }
.upcoming-banner { display: grid; min-height: 74px; grid-template-columns: minmax(200px, .9fr) minmax(260px, 1fr) auto; align-items: center; gap: 15px; padding: 11px 15px; background: linear-gradient(100deg, #eaf0ff, #f8faff); border: 1px solid #d7e2ff; border-radius: 13px; }
.upcoming-intro { display: flex; align-items: center; gap: 10px; }
.bulb-icon { display: grid; width: 43px; height: 43px; flex: 0 0 43px; place-items: center; color: #3269db; background: #dce7ff; border-radius: 50%; font-size: 22px; }
.upcoming-intro > div { display: grid; gap: 4px; }
.upcoming-intro strong { color: #19336c; font-size: 12px; font-weight: 750; }
.upcoming-intro span:last-child { color: #425f9f; font-size: 9px; }
.upcoming-list { display: grid; gap: 5px; margin: 0; padding: 0; list-style: none; }
.upcoming-list li { min-width: 0; }
.upcoming-item { display: flex; width: 100%; min-width: 0; align-items: center; gap: 7px; padding: 0; color: #283a62; background: transparent; border: 0; font: inherit; text-align: left; cursor: pointer; }
.upcoming-item:hover > span { color: #2459df; text-decoration: underline; }
.upcoming-item:focus-visible { outline: 2px solid #3478f6; outline-offset: 2px; }
.upcoming-item > strong { flex: 0 0 auto; font-size: 9px; font-weight: 700; }
.upcoming-item > span { overflow: hidden; font-size: 9px; text-overflow: ellipsis; white-space: nowrap; }
.upcoming-list strong { flex: 0 0 auto; font-weight: 700; }
.upcoming-list li > span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.upcoming-empty { color: #73819d !important; }
.all-events-button { min-height: 35px; padding: 0 13px; border-radius: 20px; font-size: 9px; }
.calendar-loading { display: grid; min-height: 280px; place-items: center; color: #73819d; background: #fff; border: 1px solid #e0e7f4; border-radius: 12px; font-size: 12px; }
.event-inline-panel { width: min(760px, 100%); padding: 18px; background: #fff; border: 1px solid #e4e9f3; border-radius: 12px; box-shadow: 0 3px 12px rgb(15 23 42 / 5%); scroll-margin-top: 96px; }
.inline-confirm { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; padding: 10px; color: #825b22; background: #fff8eb; border: 1px solid #f3dfb8; border-radius: 8px; font-size: 11px; }
.form-panel-heading { display: flex; align-items: center; justify-content: space-between; padding: 0 0 14px; border-bottom: 1px solid #edf0f6; }
.form-panel-eyebrow { color: #7987a2; font-size: 8px; font-weight: 800; letter-spacing: .13em; }
.form-panel-heading h2 { margin: 4px 0 0; color: #1f2e4d; font-size: 18px; }
.form-panel-heading > button { width: 31px; height: 31px; color: #70809a; background: #f5f7fb; border: 0; border-radius: 8px; font-size: 21px; cursor: pointer; }
.event-form { display: grid; gap: 13px; padding: 17px 21px 20px; }
.event-form > label, .datetime-fields label { display: grid; gap: 6px; color: #4b5a75; font-size: 10px; font-weight: 700; }
.event-form input[type="text"], .event-form input[type="datetime-local"], .event-form select, .event-form textarea { width: 100%; min-height: 38px; padding: 8px 10px; color: #293954; background: #fff; border: 1px solid #dfe5ef; border-radius: 8px; font: inherit; font-size: 11px; }
.event-form textarea { resize: vertical; }
.event-form :is(input, select, textarea):focus { border-color: #6879e6; outline: 3px solid rgb(104 121 230 / 14%); }
.datetime-fields { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.color-picker { display: flex; gap: 12px; padding: 0; margin: 0; border: 0; }
.color-picker legend { padding: 0; margin-bottom: 8px; color: #4b5a75; font-size: 10px; font-weight: 700; }
.color-picker label { display: grid; justify-items: center; gap: 4px; color: #72809a; font-size: 8px; cursor: pointer; }
.color-picker input { position: absolute; opacity: 0; }
.color-picker label > span { width: 18px; height: 18px; background: var(--event-color); border: 3px solid #fff; border-radius: 50%; box-shadow: 0 0 0 1px #d5dce8; }
.color-picker input:checked + span { box-shadow: 0 0 0 2px var(--event-color); }
.color-picker input:focus-visible + span { outline: 3px solid #b8caff; outline-offset: 3px; }
.form-error { padding: 8px 10px; margin: 0; color: #a33b45; background: #fff2f2; border: 1px solid #f5d6d8; border-radius: 7px; font-size: 10px; }
.form-panel-actions { display: flex; justify-content: flex-end; gap: 8px; padding-top: 13px; border-top: 1px solid #edf0f6; }
.form-panel-actions .delete-button { margin-right: auto; color: #b43e4b; background: #fff3f4; border: 1px solid #f1cdd1; }
.form-panel-actions .delete-button:hover { background: #ffe6e8; }
.form-panel-actions button { min-height: 36px; padding: 0 13px; border-radius: 8px; font-size: 10px; font-weight: 700; cursor: pointer; }
.cancel-button { color: #61708a; background: #fff; border: 1px solid #dfe5ef; }
.save-button { color: #fff; background: #326cf1; border: 1px solid #326cf1; }
.form-panel-actions button:disabled { opacity: .6; cursor: wait; }

@media (max-width: 1100px) {
  .calendar-heading { flex-wrap: wrap; }
  .calendar-heading-actions { flex-wrap: wrap; }
  .calendar-day { min-height: 66px; }
  .calendar-week .calendar-day { min-height: 290px; }
  .upcoming-banner { grid-template-columns: minmax(190px, .8fr) minmax(220px, 1fr); }
  .all-events-button { grid-column: 2; justify-self: end; }
}
@media (max-width: 760px) {
  .calendar-heading { align-items: flex-start; gap: 8px; }
  .calendar-icon { width: 52px; height: 52px; flex-basis: 52px; }
  .calendar-icon svg { width: 48px; height: 48px; }
  .heading-copy { padding-top: 5px; }
  .heading-copy h1 { font-size: 23px; }
  .heading-copy p { font-size: 10px; }
  .calendar-heading-actions { width: 100%; justify-content: space-between; margin-left: 0; }
  .period-control { gap: 5px; padding: 0 5px; }
  .period-control strong { min-width: 94px; font-size: 10px; }
  .view-switch button { padding: 0 8px; font-size: 9px; }
  .today-button { min-height: 31px; padding: 0 8px; }
  .create-event-button { min-height: 33px; padding: 0 9px; font-size: 9px; }
  .calendar-main { grid-template-columns: 1fr; }
  .calendar-sidebar { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
  .filters-card { grid-template-columns: 1fr 1fr; align-content: start; gap: 8px; padding: 0 10px 0 0; border-right: 1px solid #edf0f7; border-bottom: 0; }
  .filters-card h2, .project-filter { grid-column: 1 / -1; }
  .month-summary { padding: 0 0 0 8px; }
  .month-summary h2 { margin-bottom: 7px; }
  .completion-donut { width: 72px; height: 72px; margin-bottom: 7px; }
  .completion-donut::before { width: 59px; height: 59px; }
  .completion-donut strong { font-size: 15px; }
  .completion-donut span { font-size: 7px; }
  .summary-numbers strong { font-size: 14px; }
  .summary-numbers span { font-size: 7px; }
  .calendar-day { min-height: 59px; padding: 3px 2px; gap: 2px; }
  .calendar-week .calendar-day { min-height: 240px; }
  .calendar-day-view .calendar-day { min-height: 280px; }
  .calendar-item-chip { min-height: 14px; gap: 2px; padding: 2px; font-size: 7px; }
  .calendar-item-chip > i { width: 5px; height: 5px; flex-basis: 5px; }
  .calendar-item-chip > span:last-child { display: none; }
  .calendar-legend { gap: 8px; padding: 8px; }
  .upcoming-banner { grid-template-columns: 1fr; gap: 10px; }
  .upcoming-list { padding-left: 53px; }
  .all-events-button { grid-column: 1; justify-self: end; }
}
@media (max-width: 380px) {
  .calendar-heading-actions { gap: 4px; }
  .period-control { gap: 2px; }
  .period-control strong { min-width: 84px; font-size: 9px; }
  .view-switch button { padding: 0 6px; }
  .create-event-button { gap: 3px; padding: 0 7px; }
  .weekday-heading { font-size: 8px; }
  .calendar-item-chip { min-height: 12px; }
}
</style>
