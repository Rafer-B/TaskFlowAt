
<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'

// Gere tarefas em Kanban, sincronizando filtros, projetos, papéis e operações com a API.
definePageMeta({
  layout: 'admin',
})

// --------------------------------------------------
// TIPOS
// --------------------------------------------------

type EstadoTarefa = 'Por fazer' | 'Em curso' | 'Concluída' | 'Bloqueada'
type Prioridade = 'Baixa' | 'Média' | 'Alta'

type Categoria =
  | 'Planeamento'
  | 'Investigação'
  | 'Design'
  | 'Desenvolvimento'
  | 'Validação'
  | 'Documentação'

type EstadoAPI = 'to_do' | 'in_progress' | 'completed' | 'blocked'
type PrioridadeAPI = 'low' | 'medium' | 'high'
type ChaveOrdenacaoTabela = 'id' | 'title' | 'project' | 'responsible' | 'status' | 'priority' | 'dueDate'

const colunasTabela: Array<{ chave: ChaveOrdenacaoTabela; rotulo: string }> = [
  { chave: 'id', rotulo: 'ID' },
  { chave: 'title', rotulo: 'Tarefa' },
  { chave: 'project', rotulo: 'Projeto' },
  { chave: 'responsible', rotulo: 'Responsável' },
  { chave: 'status', rotulo: 'Estado' },
  { chave: 'priority', rotulo: 'Prioridade' },
  { chave: 'dueDate', rotulo: 'Prazo' },
]

type CategoriaAPI =
  | 'planning'
  | 'research'
  | 'design'
  | 'development'
  | 'validation'
  | 'documentation'

type ModoFormulario = 'criar' | 'editar'

interface ProjetoAPI {
  id: number
  name: string
  description: string | null
  status: 'active' | 'completed' | 'archived'
  created_by: number
  created_at: string
  updated_at: string
  archived_at: string | null
  current_user_role: 'admin' | 'owner' | 'contributor' | 'viewer'
}

interface UtilizadorAPI {
  id: number
  name: string
  email: string
  is_active: boolean
  created_at: string
}

interface MembroAPI {
  project_id: number
  user_id: number
  name: string
  email: string
  is_active: boolean
  role: 'owner' | 'contributor' | 'viewer'
  avatar_url?: string | null
}

interface TarefaAPI {
  id: number
  project_id: number
  title: string
  description: string | null
  category: CategoriaAPI
  priority: PrioridadeAPI
  status: EstadoAPI
  assigned_to: number | null
  created_by: number
  due_date: string | null
  created_at: string
  updated_at: string
  completed_at: string | null
}

interface Tarefa {
  id: number
  projectId: number
  title: string
  description: string
  project: string
  projectStatus: ProjetoAPI['status']
  responsible: string
  assignedTo: number | null
  dueDate: string
  priority: Prioridade
  status: EstadoTarefa
  category: Categoria
  createdBy: number
  createdAt: string
  updatedAt: string
  completedAt: string | null
}

interface ProjetoOpcao {
  id: number
  name: string
  status: ProjetoAPI['status']
  created_by: number
  current_user_role: ProjetoAPI['current_user_role']
}

interface FormularioTarefa {
  title: string
  description: string
  projectId: string
  assignedTo: string
  dueDate: string
  priority: Prioridade
  status: EstadoTarefa
  category: Categoria
}

// --------------------------------------------------
// CONFIGURAÇÃO
// --------------------------------------------------

const api = useNuxtApp().$api
const auth = useAuth()
const route = useRoute()

// --------------------------------------------------
// DADOS
// --------------------------------------------------

const tarefas = ref<Tarefa[]>([])
const projetosDisponiveis = ref<ProjetoOpcao[]>([])
const utilizadores = ref<UtilizadorAPI[]>([])
const membrosProjeto = ref<MembroAPI[]>([])

const pesquisa = ref('')
const filtroEstado = ref('')
const filtroPrioridade = ref('')
const filtroProjeto = ref('')
const filtroCategoria = ref('')
const pesquisaTabela = ref('')
const paginaTabela = ref(1)
const tamanhoPaginaTabela = ref(10)
const ordenacaoTabela = ref<{
  chave: ChaveOrdenacaoTabela
  ascendente: boolean
}>({
  chave: 'id',
  ascendente: false,
})

watch(
  () => route.query.search,
  (value) => {
    pesquisa.value = Array.isArray(value) ? value[0] ?? '' : value ?? ''
  },
  { immediate: true },
)

const mostrarFormulario = ref(false)
const modoFormulario = ref<ModoFormulario>('criar')
const tarefaEmEdicao = ref<number | null>(null)

const mostrarDetalhes = ref(false)
const tarefaSelecionada = ref<Tarefa | null>(null)

const formularioRef = ref<HTMLElement | null>(null)

const erro = ref('')
const erroMembros = ref('')
const sucesso = ref('')
const carregando = ref(false)
const aGuardar = ref(false)
const tarefaEmEliminacao = ref<number | null>(null)
const carregandoMembros = ref(false)
const tarefaEmArrasto = ref<number | null>(null)
const colunaEmDestaque = ref<EstadoTarefa | null>(null)

let pedidoMembros = 0

// --------------------------------------------------
// OPÇÕES
// --------------------------------------------------

const estados: EstadoTarefa[] = [
  'Por fazer',
  'Em curso',
  'Concluída',
  'Bloqueada',
]

watch(
  [() => route.query.projectId, () => route.query.status],
  ([projectId, status]) => {
    const projectValue = Array.isArray(projectId) ? projectId[0] : projectId
    const statusValue = Array.isArray(status) ? status[0] : status
    filtroProjeto.value = projectValue && /^\d+$/.test(projectValue)
      ? projectValue
      : ''
    filtroEstado.value = estados.includes(statusValue as EstadoTarefa)
      ? statusValue as EstadoTarefa
      : ''
  },
  { immediate: true },
)

const prioridades: Prioridade[] = [
  'Baixa',
  'Média',
  'Alta',
]

const categorias: Categoria[] = [
  'Planeamento',
  'Investigação',
  'Design',
  'Desenvolvimento',
  'Validação',
  'Documentação',
]

// --------------------------------------------------
// CONVERSÃO API / FRONTEND
// --------------------------------------------------

const estadoParaAPI: Record<EstadoTarefa, EstadoAPI> = {
  'Por fazer': 'to_do',
  'Em curso': 'in_progress',
  'Concluída': 'completed',
  'Bloqueada': 'blocked',
}

const estadoDaAPI: Record<EstadoAPI, EstadoTarefa> = {
  to_do: 'Por fazer',
  in_progress: 'Em curso',
  completed: 'Concluída',
  blocked: 'Bloqueada',
}

const prioridadeParaAPI: Record<Prioridade, PrioridadeAPI> = {
  Baixa: 'low',
  Média: 'medium',
  Alta: 'high',
}

const prioridadeDaAPI: Record<PrioridadeAPI, Prioridade> = {
  low: 'Baixa',
  medium: 'Média',
  high: 'Alta',
}

const categoriaParaAPI: Record<Categoria, CategoriaAPI> = {
  Planeamento: 'planning',
  Investigação: 'research',
  Design: 'design',
  Desenvolvimento: 'development',
  Validação: 'validation',
  Documentação: 'documentation',
}

const categoriaDaAPI: Record<CategoriaAPI, Categoria> = {
  planning: 'Planeamento',
  research: 'Investigação',
  design: 'Design',
  development: 'Desenvolvimento',
  validation: 'Validação',
  documentation: 'Documentação',
}

// --------------------------------------------------
// FORMULÁRIO
// --------------------------------------------------

const novaTarefa = ref<FormularioTarefa>({
  title: '',
  description: '',
  projectId: '',
  assignedTo: '',
  dueDate: '',
  priority: 'Média',
  status: 'Por fazer',
  category: 'Desenvolvimento',
})

const projetosAtivos = computed(() =>
  projetosDisponiveis.value.filter(
    (projeto) =>
      projeto.status === 'active' &&
      podeEditarTarefasDoProjeto(projeto.id),
  ),
)

const podeCriarTarefa = computed(() => projetosAtivos.value.length > 0)

function papelNoProjeto(projectId: number): ProjetoAPI['current_user_role'] | null {
  return projetosDisponiveis.value.find(
    (project) => project.id === projectId,
  )?.current_user_role ?? null
}

function podeEditarTarefasDoProjeto(projectId: number): boolean {
  // Observadores podem consultar, mas só admins, responsáveis e colaboradores alteram tarefas.
  return auth.user.value?.role === 'admin' ||
    ['owner', 'contributor'].includes(papelNoProjeto(projectId) ?? '')
}

function podeEliminarTarefa(tarefa: Tarefa): boolean {
  // Eliminar é mais restrito do que editar: apenas admin ou responsável do projeto.
  return auth.user.value?.role === 'admin' ||
    papelNoProjeto(tarefa.projectId) === 'owner'
}

const membrosAtivos = computed(() =>
  membrosProjeto.value.filter(
    (membro) => membro.is_active && membro.role !== 'viewer',
  ),
)

function limparFormulario() {
  const primeiroProjeto = projetosAtivos.value[0]

  novaTarefa.value = {
    title: '',
    description: '',
    projectId: primeiroProjeto ? String(primeiroProjeto.id) : '',
    assignedTo: '',
    dueDate: '',
    priority: 'Média',
    status: 'Por fazer',
    category: 'Desenvolvimento',
  }

  tarefaEmEdicao.value = null
  modoFormulario.value = 'criar'
  membrosProjeto.value = []
}

async function deslocarAteFormulario() {
  await nextTick()

  formularioRef.value?.scrollIntoView({
    behavior: 'smooth',
    block: 'start',
  })
}

async function abrirFormularioCriar(estadoInicial: EstadoTarefa = 'Por fazer') {
  erro.value = ''
  sucesso.value = ''
  mostrarDetalhes.value = false

  limparFormulario()
  novaTarefa.value.status = estadoInicial

  const projectQuery = route.query.project
  const projectId = Array.isArray(projectQuery)
    ? projectQuery[0]
    : projectQuery

  if (
    projectId &&
    /^\d+$/.test(projectId) &&
    projetosAtivos.value.some(
      (projeto) => projeto.id === Number(projectId),
    )
  ) {
    novaTarefa.value.projectId = projectId
  }

  modoFormulario.value = 'criar'
  mostrarFormulario.value = true

  if (novaTarefa.value.projectId) {
    await carregarMembrosProjeto(Number(novaTarefa.value.projectId))
  }

  await deslocarAteFormulario()
}

function fecharFormulario() {
  if (aGuardar.value) return

  mostrarFormulario.value = false
  erro.value = ''
  limparFormulario()
}

// --------------------------------------------------
// CARREGAR MEMBROS DO PROJETO
// --------------------------------------------------

async function carregarMembrosProjeto(projectId: number) {
  const pedidoAtual = ++pedidoMembros

  membrosProjeto.value = []
  erroMembros.value = ''

  if (!projectId) {
    carregandoMembros.value = false
    return
  }

  carregandoMembros.value = true

  try {
    // Ignora respostas de seleções anteriores quando o projeto muda rapidamente no formulário.
    const membros = await api<MembroAPI[]>(
      `/projects/${projectId}/members/`,
    )

    if (pedidoAtual !== pedidoMembros) return

    membrosProjeto.value = membros

  } catch (error) {
    console.error('Erro ao carregar membros do projeto:', error)

    if (pedidoAtual === pedidoMembros) {
      membrosProjeto.value = []
      erroMembros.value =
        'Não foi possível carregar os membros. Confirma se a API está ativa e tenta novamente.'
    }

  } finally {
    if (pedidoAtual === pedidoMembros) {
      carregandoMembros.value = false
    }
  }
}

watch(
  () => novaTarefa.value.projectId,
  async (novoProjeto, projetoAnterior) => {
    if (!mostrarFormulario.value || modoFormulario.value !== 'criar') {
      return
    }

    if (!novoProjeto || novoProjeto === projetoAnterior) {
      return
    }

    novaTarefa.value.assignedTo = ''

    await carregarMembrosProjeto(Number(novoProjeto))
  },
)

// --------------------------------------------------
// PESQUISA E FILTROS
// --------------------------------------------------

const tarefasFiltradas = computed(() => {
  const termo = pesquisa.value.trim().toLowerCase()

  return tarefas.value.filter((tarefa) => {
    const correspondePesquisa =
      !termo ||
      [
        tarefa.title,
        tarefa.description,
        tarefa.project,
        tarefa.responsible,
      ].some((valor) =>
        valor.toLowerCase().includes(termo),
      )

    const correspondeEstado =
      !filtroEstado.value ||
      tarefa.status === filtroEstado.value

    const correspondePrioridade =
      !filtroPrioridade.value ||
      tarefa.priority === filtroPrioridade.value

    const correspondeProjeto =
      !filtroProjeto.value ||
      tarefa.projectId === Number(filtroProjeto.value)

    const correspondeCategoria =
      !filtroCategoria.value ||
      tarefa.category === filtroCategoria.value

    return (
      correspondePesquisa &&
      correspondeEstado &&
      correspondePrioridade &&
      correspondeProjeto &&
      correspondeCategoria
    )
  })
})

const tarefasTabelaFiltradas = computed(() => {
  const termo = pesquisaTabela.value.trim().toLocaleLowerCase('pt-PT')
  const correspondentes = tarefasFiltradas.value.filter((tarefa) =>
    !termo ||
    [
      tarefa.title,
      tarefa.project,
      tarefa.responsible,
      tarefa.description,
      tarefa.status,
      tarefa.priority,
      tarefa.category,
    ].some(valor => valor.toLocaleLowerCase('pt-PT').includes(termo)),
  )

  const { chave, ascendente } = ordenacaoTabela.value
  return correspondentes.sort((a, b) => {
    const valorA = a[chave]
    const valorB = b[chave]
    const comparacao = typeof valorA === 'number' && typeof valorB === 'number'
      ? valorA - valorB
      : String(valorA).localeCompare(String(valorB), 'pt-PT', {
          numeric: true,
          sensitivity: 'base',
        })
    return ascendente ? comparacao : -comparacao
  })
})

const totalPaginasTabela = computed(() =>
  Math.max(1, Math.ceil(tarefasTabelaFiltradas.value.length / tamanhoPaginaTabela.value)),
)

const tarefasDaPaginaTabela = computed(() => {
  const inicio = (paginaTabela.value - 1) * tamanhoPaginaTabela.value
  return tarefasTabelaFiltradas.value.slice(inicio, inicio + tamanhoPaginaTabela.value)
})

const inicioTabela = computed(() =>
  tarefasTabelaFiltradas.value.length
    ? (paginaTabela.value - 1) * tamanhoPaginaTabela.value + 1
    : 0,
)

const fimTabela = computed(() =>
  Math.min(paginaTabela.value * tamanhoPaginaTabela.value, tarefasTabelaFiltradas.value.length),
)

watch(
  [pesquisa, filtroEstado, filtroPrioridade, filtroProjeto, filtroCategoria, pesquisaTabela, tamanhoPaginaTabela],
  () => {
    paginaTabela.value = 1
  },
)

watch(totalPaginasTabela, (total) => {
  if (paginaTabela.value > total) paginaTabela.value = total
})

function ordenarTabela(chave: ChaveOrdenacaoTabela) {
  ordenacaoTabela.value = ordenacaoTabela.value.chave === chave
    ? { chave, ascendente: !ordenacaoTabela.value.ascendente }
    : { chave, ascendente: true }
  paginaTabela.value = 1
}

// Mantém uma coluna Kanban por estado; cada coluna respeita os filtros ativos.
const colunasKanban = computed(() =>
  estados.map((estado) => ({
    estado,
    tarefas: tarefasFiltradas.value.filter(
      (tarefa) => tarefa.status === estado,
    ),
  })),
)

// --------------------------------------------------
// RESUMO
// --------------------------------------------------

const resumo = computed(() => ({
  total: tarefas.value.length,

  porFazer: tarefas.value.filter(
    (tarefa) => tarefa.status === 'Por fazer',
  ).length,

  emCurso: tarefas.value.filter(
    (tarefa) => tarefa.status === 'Em curso',
  ).length,

  concluidas: tarefas.value.filter(
    (tarefa) => tarefa.status === 'Concluída',
  ).length,

  bloqueadas: tarefas.value.filter(
    (tarefa) => tarefa.status === 'Bloqueada',
  ).length,
}))

// --------------------------------------------------
// CONVERTER TAREFA DA API
// --------------------------------------------------

function converterTarefa(tarefa: TarefaAPI): Tarefa {
  const projeto = projetosDisponiveis.value.find(
    (item) => item.id === tarefa.project_id,
  )

  const responsavel = utilizadores.value.find(
    (item) => item.id === tarefa.assigned_to,
  )

  return {
    id: tarefa.id,
    projectId: tarefa.project_id,
    title: tarefa.title,
    description: tarefa.description ?? '',
    project: projeto?.name ?? `Projeto #${tarefa.project_id}`,
    projectStatus: projeto?.status ?? 'archived',
    responsible: responsavel?.name ?? 'Por atribuir',
    assignedTo: tarefa.assigned_to,
    dueDate: tarefa.due_date
      ? tarefa.due_date.slice(0, 10)
      : '',
    priority: prioridadeDaAPI[tarefa.priority],
    status: estadoDaAPI[tarefa.status],
    category: categoriaDaAPI[tarefa.category],
    createdBy: tarefa.created_by,
    createdAt: tarefa.created_at,
    updatedAt: tarefa.updated_at,
    completedAt: tarefa.completed_at,
  }
}

// --------------------------------------------------
// CARREGAR DADOS
// --------------------------------------------------

async function carregarDados() {
  erro.value = ''
  carregando.value = true

  try {
    const [listaProjetos, listaTarefas] = await Promise.all([
      api<ProjetoAPI[]>('/projects/'),
      api<TarefaAPI[]>('/tasks/'),
    ])

    projetosDisponiveis.value = listaProjetos.map((projeto) => ({
      id: projeto.id,
      name: projeto.name,
      status: projeto.status,
      created_by: projeto.created_by,
      current_user_role: projeto.current_user_role,
    }))

    const membrosDosProjetos = await Promise.all(
      listaProjetos.map((projeto) =>
        api<MembroAPI[]>(`/projects/${projeto.id}/members`),
      ),
    )
    const membrosUnicos = new Map<number, UtilizadorAPI>()
    for (const membros of membrosDosProjetos) {
      for (const membro of membros) {
        if (membro.is_active) {
          membrosUnicos.set(membro.user_id, {
            id: membro.user_id,
            name: membro.name,
            email: membro.email,
            is_active: membro.is_active,
            created_at: '',
          })
        }
      }
    }
    utilizadores.value = [...membrosUnicos.values()]

    tarefas.value = listaTarefas.map(converterTarefa)

  } catch (error) {
    console.error('Erro ao carregar dados:', error)

    erro.value =
      'Não foi possível carregar as tarefas, os projetos ou os utilizadores. Confirma se a API está ativa.'

  } finally {
    carregando.value = false
  }
}

// --------------------------------------------------
// CONSULTAR DETALHES
// --------------------------------------------------

function consultarTarefa(tarefa: Tarefa) {
  tarefaSelecionada.value = tarefa
  mostrarDetalhes.value = true
}

watch(
  [() => route.fullPath, tarefas],
  () => {
    const taskId = route.query.taskId
    const value = Array.isArray(taskId) ? taskId[0] : taskId
    if (!value || !/^\d+$/.test(value)) return

    const tarefa = tarefas.value.find((item) => item.id === Number(value))
    if (tarefa) consultarTarefa(tarefa)
  },
  { immediate: true },
)

function fecharDetalhes() {
  mostrarDetalhes.value = false
  tarefaSelecionada.value = null
}

async function editarTarefa(tarefa: Tarefa) {
  erro.value = ''
  sucesso.value = ''
  fecharDetalhes()

  if (tarefa.projectStatus === 'archived') {
    erro.value = 'Não é possível editar tarefas de projetos arquivados.'
    return
  }

  modoFormulario.value = 'editar'
  tarefaEmEdicao.value = tarefa.id

  novaTarefa.value = {
    title: tarefa.title,
    description: tarefa.description,
    projectId: String(tarefa.projectId),
    assignedTo: tarefa.assignedTo
      ? String(tarefa.assignedTo)
      : '',
    dueDate: tarefa.dueDate,
    priority: tarefa.priority,
    status: tarefa.status,
    category: tarefa.category,
  }

  mostrarFormulario.value = true

  await carregarMembrosProjeto(tarefa.projectId)
  await deslocarAteFormulario()
}

// --------------------------------------------------
// CRIAR / ATUALIZAR TAREFA
// --------------------------------------------------

async function guardarTarefa() {
  erro.value = ''
  sucesso.value = ''

  const titulo = novaTarefa.value.title.trim()
  const descricao = novaTarefa.value.description.trim()

  const projetoId = Number(novaTarefa.value.projectId)

  const responsavelId = novaTarefa.value.assignedTo
    ? Number(novaTarefa.value.assignedTo)
    : null

  if (!titulo) {
    erro.value = 'O título da tarefa é obrigatório.'
    return
  }

  if (titulo.length > 255) {
    erro.value = 'O título não pode ultrapassar 255 caracteres.'
    return
  }

  if (descricao.length > 5000) {
    erro.value = 'A descrição não pode ultrapassar 5000 caracteres.'
    return
  }

  const projeto = projetosDisponiveis.value.find(
    (item) => item.id === projetoId,
  )

  if (!projeto) {
    erro.value = 'Seleciona um projeto válido.'
    return
  }

  if (
    modoFormulario.value === 'criar' &&
    projeto.status !== 'active'
  ) {
    erro.value = 'Só é possível criar tarefas em projetos ativos.'
    return
  }

  if (projeto.status === 'archived') {
    erro.value = 'Não é possível alterar tarefas de projetos arquivados.'
    return
  }

  if (
    responsavelId !== null &&
    !membrosAtivos.value.some(
      (membro) => membro.user_id === responsavelId,
    )
  ) {
    erro.value = 'O responsável deve ser um membro ativo do projeto.'
    return
  }

  if (
    modoFormulario.value === 'editar' &&
    tarefaEmEdicao.value === null
  ) {
    erro.value = 'Não foi possível identificar a tarefa a editar.'
    return
  }

  if (
    modoFormulario.value === 'criar' &&
    !auth.user.value
  ) {
    erro.value = 'A sessão expirou. Inicia sessão novamente.'
    return
  }

  aGuardar.value = true

  try {
    // Converte rótulos da interface para enums da API e envia datas como início do dia.
    const corpo = {
      title: titulo,
      description: descricao || null,
      category: categoriaParaAPI[novaTarefa.value.category],
      priority: prioridadeParaAPI[novaTarefa.value.priority],
      status: estadoParaAPI[novaTarefa.value.status],
      assigned_to: responsavelId,
      due_date: novaTarefa.value.dueDate
        ? `${novaTarefa.value.dueDate}T00:00:00`
        : null,
    }

    let resultado: TarefaAPI

    if (modoFormulario.value === 'criar') {
      resultado = await api<TarefaAPI>(
        '/tasks/',
        {
          method: 'POST',
          body: {
            project_id: projetoId,
            ...corpo,
          },
        },
      )

      tarefas.value.unshift(converterTarefa(resultado))
      sucesso.value = 'Tarefa criada com sucesso.'

    } else {
      resultado = await api<TarefaAPI>(
        `/tasks/${tarefaEmEdicao.value}`,
        {
          method: 'PATCH',
          body: corpo,
        },
      )

      const indice = tarefas.value.findIndex(
        (item) => item.id === resultado.id,
      )

      if (indice !== -1) {
        tarefas.value[indice] = converterTarefa(resultado)
      }

      sucesso.value = 'Tarefa atualizada com sucesso.'
    }

    mostrarFormulario.value = false
    limparFormulario()

  } catch (error: any) {
    console.error('Erro ao guardar tarefa:', error)

    erro.value =
      error?.data?.detail ||
      'Não foi possível guardar a tarefa. Verifica os dados e tenta novamente.'

  } finally {
    aGuardar.value = false
  }
}

// --------------------------------------------------
// ALTERAR ESTADO
// --------------------------------------------------

async function alterarEstado(
  tarefa: Tarefa,
  novoEstado: EstadoTarefa,
  elemento?: HTMLSelectElement,
) {
  const estadoAnterior = tarefa.status

  if (!estados.includes(novoEstado)) return
  if (novoEstado === estadoAnterior) return

  if (!podeEditarTarefasDoProjeto(tarefa.projectId)) {
    erro.value = 'O teu papel neste projeto permite apenas consultar as tarefas.'
    if (elemento) elemento.value = estadoAnterior
    return
  }

  if (tarefa.projectStatus === 'archived') {
    erro.value = 'Não é possível alterar tarefas de projetos arquivados.'
    if (elemento) elemento.value = estadoAnterior
    return
  }

  erro.value = ''
  sucesso.value = ''

  // Atualização otimista: reverte o estado se o servidor rejeitar a alteração.
  tarefa.status = novoEstado

  try {
    const atualizada = await api<TarefaAPI>(
      `/tasks/${tarefa.id}`,
      {
        method: 'PATCH',
        body: {
          status: estadoParaAPI[novoEstado],
        },
      },
    )

    const indice = tarefas.value.findIndex(
      (item) => item.id === tarefa.id,
    )

    if (indice !== -1) {
      const tarefaAtualizada = converterTarefa(atualizada)
      tarefas.value[indice] = tarefaAtualizada

      if (tarefaSelecionada.value?.id === tarefa.id) {
        tarefaSelecionada.value = tarefaAtualizada
      }
    }

    sucesso.value = 'Estado da tarefa atualizado.'

  } catch (error: unknown) {
    console.error('Erro ao atualizar estado:', error)

    tarefa.status = estadoAnterior
    if (elemento) elemento.value = estadoAnterior

    erro.value = obterMensagemErro(error)
  }
}

function alterarEstadoPorEvento(tarefa: Tarefa, evento: Event): void {
  const elemento = evento.target as HTMLSelectElement
  const novoEstado = elemento.value as EstadoTarefa

  if (!estados.includes(novoEstado)) {
    elemento.value = tarefa.status
    return
  }

  void alterarEstado(tarefa, novoEstado, elemento)
}

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

  if (
    typeof error === 'object' &&
    error !== null &&
    'statusCode' in error &&
    error.statusCode === 0
  ) {
    return 'Não foi possível contactar a API. Confirma se o backend está ativo e tenta novamente.'
  }

  return 'Não foi possível atualizar o estado da tarefa.'
}

function iniciarArrasto(evento: DragEvent, tarefa: Tarefa): void {
  // Bloqueia o arrasto de projetos arquivados ou de utilizadores sem permissão de edição.
  if (
    tarefa.projectStatus === 'archived' ||
    !podeEditarTarefasDoProjeto(tarefa.projectId)
  ) {
    evento.preventDefault()
    return
  }

  tarefaEmArrasto.value = tarefa.id
  evento.dataTransfer?.setData('text/plain', String(tarefa.id))
  if (evento.dataTransfer) evento.dataTransfer.effectAllowed = 'move'
}

function permitirLargada(evento: DragEvent, estado: EstadoTarefa): void {
  evento.preventDefault()
  colunaEmDestaque.value = estado
  if (evento.dataTransfer) evento.dataTransfer.dropEffect = 'move'
}

function terminarLargada(): void {
  colunaEmDestaque.value = null
}

function sairColuna(evento: DragEvent): void {
  const coluna = evento.currentTarget
  const proximoAlvo = evento.relatedTarget

  if (
    coluna instanceof HTMLElement &&
    proximoAlvo instanceof Node &&
    coluna.contains(proximoAlvo)
  ) {
    return
  }

  terminarLargada()
}

async function largarTarefa(
  evento: DragEvent,
  estado: EstadoTarefa,
): Promise<void> {
  evento.preventDefault()
  const tarefaId = Number(
    evento.dataTransfer?.getData('text/plain') ||
      tarefaEmArrasto.value ||
      '',
  )
  const tarefa = tarefas.value.find((item) => item.id === tarefaId)

  terminarLargada()
  tarefaEmArrasto.value = null

  if (tarefa) await alterarEstado(tarefa, estado)
}

// --------------------------------------------------
// ELIMINAR TAREFA
// --------------------------------------------------

async function eliminarTarefa(tarefa: Tarefa) {
  erro.value = ''
  sucesso.value = ''

  if (tarefa.projectStatus === 'archived') {
    erro.value = 'Não é possível eliminar tarefas de projetos arquivados.'
    return
  }
  if (!podeEliminarTarefa(tarefa)) {
    erro.value = 'Apenas um responsável do projeto pode eliminar tarefas.'
    return
  }

  const confirmado = window.confirm(
    `Tens a certeza de que pretendes eliminar a tarefa "${tarefa.title}"? Esta operação não pode ser desfeita.`,
  )

  if (!confirmado) return

  tarefaEmEliminacao.value = tarefa.id

  try {
    await api(
      `/tasks/${tarefa.id}`,
      {
        method: 'DELETE',
      },
    )

    tarefas.value = tarefas.value.filter(
      (item) => item.id !== tarefa.id,
    )

    if (tarefaSelecionada.value?.id === tarefa.id) {
      fecharDetalhes()
    }

    sucesso.value = 'Tarefa eliminada com sucesso.'

  } catch (error: any) {
    console.error('Erro ao eliminar tarefa:', error)

    erro.value =
      error?.data?.detail ||
      'Não foi possível eliminar a tarefa.'

  } finally {
    tarefaEmEliminacao.value = null
  }
}

// --------------------------------------------------
// DATAS
// --------------------------------------------------

function formatarData(data: string) {
  if (!data) return 'Sem prazo'

  const partes = data.split('-')

  const ano = partes[0] ?? ''
  const mes = partes[1] ?? ''
  const dia = partes[2] ?? ''

  if (!ano || !mes || !dia) return 'Data inválida'

  return `${dia}/${mes}/${ano}`
}

function formatarDataHora(data: string | null) {
  if (!data) return 'Não disponível'

  const dataConvertida = new Date(data)

  if (Number.isNaN(dataConvertida.getTime())) {
    return 'Não disponível'
  }

  return dataConvertida.toLocaleString('pt-PT')
}

function classeEstado(estado: EstadoTarefa) {
  return {
    'por-fazer': estado === 'Por fazer',
    'em-curso': estado === 'Em curso',
    concluida: estado === 'Concluída',
    bloqueada: estado === 'Bloqueada',
  }
}

function classePrioridade(prioridade: Prioridade) {
  return {
    'prioridade-baixa': prioridade === 'Baixa',
    'prioridade-media': prioridade === 'Média',
    'prioridade-alta': prioridade === 'Alta',
  }
}

// --------------------------------------------------
// INICIALIZAÇÃO
// --------------------------------------------------

onMounted(() => {
  carregarDados()
})
</script>

<template>
  <div class="page">

    <!-- CABEÇALHO -->
    <header class="page-header">
      <div>
        <NuxtLink to="/projects" class="back-link">
          ← Voltar aos projetos
        </NuxtLink>

        <h1>Tarefas</h1>

        <p>
          Organiza o trabalho, acompanha os prazos e atualiza o progresso.
        </p>
      </div>

      <button
        v-if="podeCriarTarefa"
        class="primary-button"
        type="button"
        @click="abrirFormularioCriar()"
      >
        + Nova tarefa
      </button>
    </header>

    <!-- MENSAGENS -->
    <p v-if="erro" class="error-message" role="alert">
      {{ erro }}
    </p>

    <p v-if="sucesso" class="success-message" role="status">
      {{ sucesso }}
    </p>

    <nav class="board-tabs" aria-label="Tarefas">
      <NuxtLink to="/tasks" class="board-tab">
        <span aria-hidden="true">▦</span> Tarefas
      </NuxtLink>
      <span class="board-total">{{ resumo.total }} tarefas no quadro</span>
    </nav>

    <!-- FORMULÁRIO -->
    <section
      v-if="mostrarFormulario"
      ref="formularioRef"
      class="form-card"
    >
      <div class="form-heading">
        <div>
          <h2>
            {{ modoFormulario === 'criar' ? 'Criar tarefa' : 'Editar tarefa' }}
          </h2>

          <p>
            Preenche os campos para guardar as informações da tarefa.
          </p>
        </div>

        <button
          type="button"
          class="close-button"
          aria-label="Fechar formulário"
          :disabled="aGuardar"
          @click="fecharFormulario"
        >
          ×
        </button>
      </div>

      <form @submit.prevent="guardarTarefa">
        <div class="form-grid">

          <div class="field full-width">
            <label for="titulo">Título *</label>

            <input
              id="titulo"
              v-model="novaTarefa.title"
              type="text"
              maxlength="255"
              placeholder="Ex.: Implementar autenticação"
              required
            />
          </div>

          <div class="field full-width">
            <label for="descricao">Descrição</label>

            <textarea
              id="descricao"
              v-model="novaTarefa.description"
              rows="3"
              maxlength="5000"
              placeholder="Descreve o que é necessário fazer..."
            />
          </div>

          <div class="field">
            <label for="projeto">Projeto *</label>

            <select
              id="projeto"
              v-model="novaTarefa.projectId"
              required
              :disabled="modoFormulario === 'editar' || projetosAtivos.length === 0"
            >
              <option value="" disabled>
                Seleciona um projeto
              </option>

              <option
                v-for="projeto in projetosAtivos"
                :key="projeto.id"
                :value="String(projeto.id)"
              >
                {{ projeto.name }}
              </option>
            </select>

            <small v-if="modoFormulario === 'editar'">
              O projeto de uma tarefa não pode ser alterado.
            </small>

            <small v-else-if="projetosAtivos.length === 0">
              Não existem projetos ativos disponíveis.
            </small>
          </div>

          <div class="field">
            <label for="responsavel">Responsável</label>

            <select
              id="responsavel"
              v-model="novaTarefa.assignedTo"
              :disabled="carregandoMembros || !novaTarefa.projectId"
            >
              <option value="">
                Por atribuir
              </option>

              <option
                v-for="membro in membrosAtivos"
                :key="membro.user_id"
                :value="String(membro.user_id)"
              >
                {{ membro.name }} —
                {{ membro.role === 'owner'
                  ? 'Responsável'
                  : membro.role === 'viewer'
                    ? 'Observador'
                    : 'Colaborador'
                }}
              </option>
            </select>

            <small v-if="carregandoMembros">
              A carregar membros...
            </small>

            <div v-if="erroMembros" class="member-load-error" role="alert">
              <small>{{ erroMembros }}</small>
              <button
                type="button"
                :disabled="carregandoMembros"
                @click="carregarMembrosProjeto(Number(novaTarefa.projectId))"
              >
                Tentar novamente
              </button>
            </div>

            <small
              v-else-if="
                !carregandoMembros &&
                novaTarefa.projectId &&
                membrosAtivos.length === 0
              "
            >
              Este projeto não tem membros ativos. Adiciona o utilizador em
              <NuxtLink to="/projects">Projetos → Membros</NuxtLink>
              antes de o atribuir à tarefa.
            </small>
          </div>

          <div class="field">
            <label for="prazo">Prazo</label>

            <input
              id="prazo"
              v-model="novaTarefa.dueDate"
              type="date"
            />
          </div>

          <div class="field">
            <label for="categoria">Categoria</label>

            <select
              id="categoria"
              v-model="novaTarefa.category"
            >
              <option
                v-for="categoria in categorias"
                :key="categoria"
                :value="categoria"
              >
                {{ categoria }}
              </option>
            </select>
          </div>

          <div class="field">
            <label for="prioridade">Prioridade</label>

            <select
              id="prioridade"
              v-model="novaTarefa.priority"
            >
              <option
                v-for="prioridade in prioridades"
                :key="prioridade"
                :value="prioridade"
              >
                {{ prioridade }}
              </option>
            </select>
          </div>

          <div class="field">
            <label for="estado">Estado</label>

            <select
              id="estado"
              v-model="novaTarefa.status"
            >
              <option
                v-for="estado in estados"
                :key="estado"
                :value="estado"
              >
                {{ estado }}
              </option>
            </select>
          </div>

        </div>

        <div class="form-actions">
          <button
            type="button"
            class="secondary-button"
            :disabled="aGuardar"
            @click="fecharFormulario"
          >
            Cancelar
          </button>

          <button
            type="submit"
            class="primary-button"
            :disabled="aGuardar || (modoFormulario === 'criar' && projetosAtivos.length === 0)"
          >
            {{
              aGuardar
                ? 'A guardar...'
                : modoFormulario === 'criar'
                  ? 'Criar tarefa'
                  : 'Guardar alterações'
            }}
          </button>
        </div>
      </form>
    </section>

    <!-- LISTAGEM -->
    <section class="tasks-section">

      <div class="filters">
        <button
          v-if="podeCriarTarefa"
          class="new-task-button"
          type="button"
          @click="abrirFormularioCriar()"
        >
          <span aria-hidden="true">＋</span> Nova tarefa
        </button>

        <label class="board-search">
          <span aria-hidden="true">⌕</span>
          <input
            v-model="pesquisa"
            type="search"
            placeholder="Pesquisar..."
            aria-label="Pesquisar tarefas"
          />
        </label>

        <select
          v-model="filtroProjeto"
          aria-label="Filtrar por projeto"
        >
          <option value="">
            Todos os projetos
          </option>

          <option
            v-for="projeto in projetosDisponiveis"
            :key="projeto.id"
            :value="String(projeto.id)"
          >
            {{ projeto.name }}
          </option>
        </select>

        <select v-model="filtroEstado" aria-label="Filtrar por estado">
          <option value="">
            Todos os estados
          </option>

          <option
            v-for="estado in estados"
            :key="estado"
            :value="estado"
          >
            {{ estado }}
          </option>
        </select>

        <select v-model="filtroPrioridade" aria-label="Filtrar por prioridade">
          <option value="">
            Todas as prioridades
          </option>

          <option
            v-for="prioridade in prioridades"
            :key="prioridade"
            :value="prioridade"
          >
            {{ prioridade }}
          </option>
        </select>

        <select v-model="filtroCategoria" aria-label="Filtrar por categoria">
          <option value="">
            Todas as categorias
          </option>

          <option
            v-for="categoria in categorias"
            :key="categoria"
            :value="categoria"
          >
            {{ categoria }}
          </option>
        </select>

      </div>

      <div class="kanban-scroll">
        <div v-if="carregando" class="board-loading">
          <span class="board-spinner" aria-hidden="true"></span>
          A carregar tarefas...
        </div>

        <!-- Cada coluna aceita largadas; a função de estado valida novamente as permissões. -->
        <div v-else class="kanban-board">
          <section
            v-for="(coluna, indice) in colunasKanban"
            :key="coluna.estado"
            class="kanban-column"
            :class="[
              `column-${indice}`,
              { 'column-drop-active': colunaEmDestaque === coluna.estado },
            ]"
            @dragenter.prevent="permitirLargada($event, coluna.estado)"
            @dragover="permitirLargada($event, coluna.estado)"
            @dragleave="sairColuna"
            @drop="largarTarefa($event, coluna.estado)"
          >
            <header class="column-heading">
              <span>{{ coluna.estado }}</span>
              <span class="column-count">{{ coluna.tarefas.length }}</span>
              <button
                v-if="podeCriarTarefa"
                type="button"
                :aria-label="`Criar tarefa em ${coluna.estado}`"
                title="Criar tarefa nesta coluna"
                @click="abrirFormularioCriar(coluna.estado)"
              >
                +
              </button>
            </header>

            <div class="column-cards">
              <article
                v-for="tarefa in coluna.tarefas"
                :key="tarefa.id"
                class="kanban-card"
                role="button"
                tabindex="0"
                :aria-label="`Abrir detalhes da tarefa ${tarefa.title}`"
                :class="[
                  classeEstado(tarefa.status),
                  {
                    'card-dragging': tarefaEmArrasto === tarefa.id,
                    'card-archived': tarefa.projectStatus === 'archived',
                  },
                ]"
                :draggable="
                  tarefa.projectStatus !== 'archived' &&
                  podeEditarTarefasDoProjeto(tarefa.projectId)
                "
                @click="consultarTarefa(tarefa)"
                @keydown.enter.prevent="consultarTarefa(tarefa)"
                @keydown.space.prevent="consultarTarefa(tarefa)"
                @dragstart="iniciarArrasto($event, tarefa)"
                @dragend="tarefaEmArrasto = null; terminarLargada()"
              >
                <div class="card-topline">
                  <span class="category">{{ tarefa.category }}</span>
                  <span class="card-id">#{{ tarefa.id }}</span>
                </div>

                <h3 class="card-title">
                  {{ tarefa.title }}
                </h3>

                <div class="card-meta">
                  <span
                    class="priority"
                    :class="classePrioridade(tarefa.priority)"
                  >
                    {{ tarefa.priority }}
                  </span>
                </div>
              </article>

              <div v-if="!coluna.tarefas.length" class="column-empty">
                <span aria-hidden="true">＋</span>
                <span>Arraste uma tarefa para aqui</span>
              </div>
            </div>
          </section>
        </div>
      </div>

      <p class="results-count">
        A mostrar {{ tarefasFiltradas.length }}
        de {{ tarefas.length }} tarefas
      </p>

      <section class="task-table-section" aria-labelledby="task-table-title">
        <header class="task-table-heading">
          <div>
            <span class="section-eyebrow">VISTA DETALHADA</span>
            <h2 id="task-table-title">Lista de tarefas</h2>
            <p>{{ tarefasTabelaFiltradas.length }} tarefa(s) correspondem aos filtros atuais</p>
          </div>
          <label class="table-search">
            <span aria-hidden="true">⌕</span>
            <input
              v-model="pesquisaTabela"
              type="search"
              aria-label="Pesquisar na lista de tarefas"
              placeholder="Pesquisar na lista..."
            />
          </label>
        </header>

        <div class="task-table-scroll">
          <table class="task-table">
            <thead>
              <tr>
                <th
                  v-for="coluna in colunasTabela"
                  :key="coluna.chave"
                  :aria-sort="
                    ordenacaoTabela.chave === coluna.chave
                      ? ordenacaoTabela.ascendente ? 'ascending' : 'descending'
                      : 'none'
                  "
                >
                  <button
                    type="button"
                    @click="ordenarTabela(coluna.chave)"
                  >
                    {{ coluna.rotulo }}
                    <span aria-hidden="true">
                      {{ ordenacaoTabela.chave === coluna.chave
                        ? ordenacaoTabela.ascendente ? '↑' : '↓'
                        : '↕'
                      }}
                    </span>
                  </button>
                </th>
                <th scope="col">Ações</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="tarefa in tarefasDaPaginaTabela" :key="tarefa.id">
                <td class="table-task-id">#{{ tarefa.id }}</td>
                <td>
                  <button
                    type="button"
                    class="table-task-title"
                    @click="consultarTarefa(tarefa)"
                  >
                    {{ tarefa.title }}
                  </button>
                  <small class="table-task-category">{{ tarefa.category }}</small>
                </td>
                <td>{{ tarefa.project }}</td>
                <td>{{ tarefa.responsible }}</td>
                <td>
                  <span class="table-status" :class="classeEstado(tarefa.status)">
                    {{ tarefa.status }}
                  </span>
                </td>
                <td>
                  <span class="priority" :class="classePrioridade(tarefa.priority)">
                    {{ tarefa.priority }}
                  </span>
                </td>
                <td>{{ formatarData(tarefa.dueDate) }}</td>
                <td>
                  <button
                    type="button"
                    class="table-action"
                    :aria-label="`Ver detalhes de ${tarefa.title}`"
                    @click="consultarTarefa(tarefa)"
                  >
                    Detalhes
                  </button>
                </td>
              </tr>
              <tr v-if="!tarefasTabelaFiltradas.length">
                <td colspan="8" class="table-empty">
                  {{ carregando ? 'A carregar tarefas...' : 'Não foram encontradas tarefas.' }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <footer class="table-pagination">
          <div class="table-page-size">
            <label for="table-page-size">Linhas por página</label>
            <select id="table-page-size" v-model.number="tamanhoPaginaTabela">
              <option :value="10">10</option>
              <option :value="25">25</option>
              <option :value="50">50</option>
            </select>
            <span>{{ inicioTabela }}–{{ fimTabela }} de {{ tarefasTabelaFiltradas.length }}</span>
          </div>
          <div class="table-page-controls" aria-label="Paginação da lista de tarefas">
            <button
              type="button"
              aria-label="Página anterior"
              :disabled="paginaTabela <= 1"
              @click="paginaTabela--"
            >
              Anterior
            </button>
            <span>Página {{ paginaTabela }} de {{ totalPaginasTabela }}</span>
            <button
              type="button"
              aria-label="Página seguinte"
              :disabled="paginaTabela >= totalPaginasTabela"
              @click="paginaTabela++"
            >
              Seguinte
            </button>
          </div>
        </footer>
      </section>

    </section>

    <!-- JANELA DE DETALHES -->
    <div
      v-if="mostrarDetalhes && tarefaSelecionada"
      class="modal-overlay"
      @click.self="fecharDetalhes"
      @keydown.esc="fecharDetalhes"
    >
      <section
        class="details-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="details-title"
      >
        <header class="details-header">
          <div>
            <span class="details-eyebrow">DETALHES DA TAREFA</span>
            <h2 id="details-title">
              {{ tarefaSelecionada.title }}
            </h2>
          </div>

          <button
            type="button"
            class="close-button"
            aria-label="Fechar detalhes"
            @click="fecharDetalhes"
          >
            ×
          </button>
        </header>

        <div class="details-content">

          <div class="detail-item full-width">
            <span>Descrição</span>
            <p>
              {{ tarefaSelecionada.description || 'Sem descrição disponível.' }}
            </p>
          </div>

          <div class="detail-item">
            <span>Projeto</span>
            <strong>{{ tarefaSelecionada.project }}</strong>
          </div>

          <div class="detail-item">
            <span>Responsável</span>
            <strong>{{ tarefaSelecionada.responsible }}</strong>
          </div>

          <div class="detail-item">
            <span>Categoria</span>
            <strong>{{ tarefaSelecionada.category }}</strong>
          </div>

          <div class="detail-item">
            <span>Prioridade</span>
            <span
              class="priority"
              :class="classePrioridade(tarefaSelecionada.priority)"
            >
              {{ tarefaSelecionada.priority }}
            </span>
          </div>

          <div class="detail-item">
            <span>Estado</span>
            <select
              class="detail-status-select"
              :class="classeEstado(tarefaSelecionada.status)"
              :value="tarefaSelecionada.status"
              :disabled="
                tarefaSelecionada.projectStatus === 'archived' ||
                !podeEditarTarefasDoProjeto(tarefaSelecionada.projectId)
              "
              :aria-label="`Alterar estado de ${tarefaSelecionada.title}`"
              @change="alterarEstadoPorEvento(tarefaSelecionada, $event)"
            >
              <option
                v-for="estado in estados"
                :key="estado"
                :value="estado"
              >
                {{ estado }}
              </option>
            </select>
          </div>

          <div class="detail-item">
            <span>Prazo</span>
            <strong>{{ formatarData(tarefaSelecionada.dueDate) }}</strong>
          </div>

          <div class="detail-item">
            <span>Data de criação</span>
            <strong>{{ formatarDataHora(tarefaSelecionada.createdAt) }}</strong>
          </div>

          <div class="detail-item">
            <span>Última atualização</span>
            <strong>{{ formatarDataHora(tarefaSelecionada.updatedAt) }}</strong>
          </div>

          <div
            v-if="tarefaSelecionada.completedAt"
            class="detail-item"
          >
            <span>Data de conclusão</span>
            <strong>{{ formatarDataHora(tarefaSelecionada.completedAt) }}</strong>
          </div>

        </div>

        <p v-if="erro" class="error-message" role="alert">
          {{ erro }}
        </p>

        <p v-if="sucesso" class="success-message" role="status">
          {{ sucesso }}
        </p>

        <footer class="details-actions">
          <button
            v-if="podeEliminarTarefa(tarefaSelecionada)"
            type="button"
            class="delete-task-button"
            :disabled="
              tarefaSelecionada.projectStatus === 'archived' ||
              tarefaEmEliminacao === tarefaSelecionada.id
            "
            @click="eliminarTarefa(tarefaSelecionada)"
          >
            {{ tarefaEmEliminacao === tarefaSelecionada.id ? 'A eliminar...' : 'Eliminar tarefa' }}
          </button>

          <button
            type="button"
            class="secondary-button"
            @click="fecharDetalhes"
          >
            Fechar
          </button>

          <button
            v-if="
              tarefaSelecionada.projectStatus !== 'archived' &&
              podeEditarTarefasDoProjeto(tarefaSelecionada.projectId)
            "
            type="button"
            class="primary-button"
            @click="editarTarefa(tarefaSelecionada)"
          >
            Editar tarefa
          </button>
        </footer>
      </section>
    </div>

  </div>
</template>

<style scoped>
.page {
  width: 100%;
  max-width: 1500px;
  min-width: 0;
  margin: 0 auto;
  padding: 12px 0 32px;
  color: #172033;
  scroll-behavior: smooth;
}

.page-header {
  position: relative;
  overflow: hidden;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  padding: 24px 28px;
  margin-bottom: 18px;
  border: 1px solid #e1e7f4;
  border-radius: 20px;
  background:
    radial-gradient(circle at 92% 10%, rgb(199 210 254 / 55%), transparent 25%),
    linear-gradient(120deg, #fff 0%, #f8faff 65%, #f0f3ff 100%);
  box-shadow: 0 8px 24px rgb(23 37 84 / 4%);
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #5c62c7;
  font-size: 12px;
  font-weight: 650;
  text-decoration: none;
}

.back-link:hover {
  text-decoration: underline;
}

.page-header h1 {
  margin: 11px 0 6px;
  color: #1c2b4a;
  font-size: clamp(25px, 2.4vw, 32px);
  font-weight: 800;
  letter-spacing: -1px;
}

.page-header p {
  margin: 0;
  color: #7d8aa1;
  font-size: 13px;
}

.primary-button,
.secondary-button {
  display: inline-flex;
  min-height: 42px;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 0 17px;
  border: 1px solid transparent;
  border-radius: 10px;
  font-weight: 650;
  cursor: pointer;
  transition:
    transform .18s ease,
    background .18s ease,
    border-color .18s ease,
    box-shadow .18s ease,
    opacity .18s ease;
}

.primary-button {
  background: linear-gradient(135deg, var(--tf-primary), var(--tf-primary-hover));
  color: white;
  box-shadow: 0 7px 16px -8px rgb(69 79 201 / 62%);
}

.primary-button:hover {
  background: linear-gradient(135deg, var(--tf-primary-hover), #3730a3);
  transform: translateY(-1px);
  box-shadow: 0 10px 20px -8px rgb(67 56 202 / 62%);
}

.secondary-button {
  border-color: #e2e8f0;
  background: #fff;
  color: #475569;
}

.secondary-button:hover {
  border-color: #cbd5e1;
  background: #f8fafc;
  box-shadow: 0 3px 8px rgb(15 23 42 / 6%);
}

.primary-button:active,
.secondary-button:active {
  transform: translateY(0);
}

.primary-button:focus-visible,
.secondary-button:focus-visible,
.new-task-button:focus-visible,
.delete-task-button:focus-visible {
  outline: 3px solid #c7d2fe;
  outline-offset: 2px;
}

.primary-button:disabled,
.secondary-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error-message,
.success-message {
  margin: 12px 0;
  padding: 12px 14px;
  border-radius: 8px;
  font-size: 14px;
}

.error-message {
  color: #b91c1c;
  background: #fef2f2;
  border: 1px solid #fecaca;
}

.success-message {
  color: #166534;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
}

.board-tabs {
  display: flex;
  align-items: center;
  gap: 24px;
  min-height: 48px;
  padding: 0 14px;
  margin-bottom: 14px;
  border-bottom: 1px solid #dfe5ef;
}

.board-tab {
  display: inline-flex;
  min-height: 48px;
  align-items: center;
  gap: 8px;
  color: #526078;
  border-bottom: 2px solid transparent;
  font-size: 12px;
  font-weight: 650;
}

.board-tab:first-child {
  color: #34446a;
  border-bottom-color: #4f46e5;
}

.board-total {
  margin-left: auto;
  color: #8b97aa;
  font-size: 11px;
}

.form-card {
  max-width: 900px;
  margin: 0 auto 30px;
  padding: 24px;
  border: 1px solid #e7ebf3;
  border-radius: 17px;
  background: white;
  box-shadow: 0 5px 18px rgb(23 37 84 / 3%);
  scroll-margin-top: 24px;
}

.form-heading {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 22px;
}

.form-heading h2 {
  margin: 0 0 6px;
  font-size: 21px;
}

.form-heading p,
.section-heading p {
  margin: 0;
  color: #64748b;
  font-size: 13px;
}

.close-button {
  flex-shrink: 0;
  width: 34px;
  height: 34px;
  border: 0;
  border-radius: 8px;
  background: #f1f5f9;
  color: #475569;
  font-size: 23px;
  cursor: pointer;
}

.close-button:hover {
  background: #e2e8f0;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
  margin-bottom: 20px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
}

.full-width {
  grid-column: 1 / -1;
}

.field label {
  font-size: 14px;
  font-weight: 600;
}

.field input,
.field select,
.field textarea,
.filters input,
.filters select {
  box-sizing: border-box;
  width: 100%;
  min-width: 0;
  padding: 11px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: white;
  color: #172033;
  font: inherit;
}

.field input:focus,
.field select:focus,
.field textarea:focus,
.filters input:focus,
.filters select:focus {
  outline: 2px solid #c7d2fe;
  border-color: #4f46e5;
}

.field input:disabled,
.field select:disabled {
  background: #f8fafc;
  color: #64748b;
  cursor: not-allowed;
}

.field textarea {
  resize: vertical;
}

.field small {
  color: #64748b;
  font-size: 12px;
}

.field small a {
  color: #4f46e5;
  font-weight: 650;
  text-decoration: none;
}

.field small a:hover {
  text-decoration: underline;
}

.member-load-error {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  color: #b91c1c;
}

.member-load-error small {
  color: inherit;
}

.member-load-error button {
  padding: 5px 8px;
  color: #4338ca;
  background: #eef2ff;
  border: 1px solid #dfe4ff;
  border-radius: 6px;
  font: inherit;
  font-weight: 650;
  cursor: pointer;
}

.member-load-error button:disabled {
  opacity: .6;
  cursor: wait;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
  padding-top: 17px;
  border-top: 1px solid #edf0f5;
}

.form-actions .primary-button {
  min-width: 160px;
}

.tasks-section {
  padding: 22px;
  border: 1px solid #e7ebf3;
  border-radius: 18px;
  background: white;
  box-shadow: 0 5px 18px rgb(23 37 84 / 3%);
}

.section-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 17px;
}

.section-heading h2 {
  margin: 0 0 5px;
  color: #243452;
  font-size: 18px;
  font-weight: 750;
}

.section-eyebrow {
  display: block;
  margin-bottom: 6px;
  color: #5b5dc6;
  font-size: 9px;
  font-weight: 800;
  letter-spacing: .12em;
}

.task-count {
  padding: 8px 12px;
  border: 1px solid #e1e7ff;
  border-radius: 999px;
  background: #f3f4ff;
  color: #5146c8;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}

.filters {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  padding: 0 0 16px;
  margin-bottom: 2px;
}

.new-task-button {
  display: inline-flex;
  min-height: 36px;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 0 13px;
  color: #fff;
  background: linear-gradient(135deg, var(--tf-primary), var(--tf-primary-hover));
  border: 1px solid var(--tf-primary-hover);
  border-radius: 9px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 5px 12px -7px rgb(69 79 201 / 70%);
  transition: transform .18s ease, box-shadow .18s ease, background .18s ease;
}

.new-task-button:hover {
  background: linear-gradient(135deg, var(--tf-primary-hover), #3730a3);
  transform: translateY(-1px);
  box-shadow: 0 8px 14px -8px rgb(69 79 201 / 70%);
}

.new-task-button > span {
  font-size: 17px;
}

.board-search {
  display: flex;
  flex: 1 1 170px;
  max-width: 280px;
  min-height: 36px;
  align-items: center;
  gap: 7px;
  padding: 0 10px;
  color: #8290a5;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 7px;
}

.board-search > span {
  font-size: 17px;
}

.board-search input {
  width: 100%;
  min-width: 0;
  padding: 0;
  color: #334155;
  background: transparent;
  border: 0;
  outline: 0;
  font-size: 11px;
}

.board-search input::placeholder {
  color: #9aa7ba;
}

.filters > select {
  width: auto;
  min-width: 132px;
  min-height: 36px;
  padding: 0 10px;
  color: #58667c;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 7px;
  font-size: 10px;
}

.kanban-scroll {
  width: 100%;
  overflow-x: auto;
  padding: 1px 2px 12px;
  scrollbar-color: #cbd5e1 transparent;
  scrollbar-width: thin;
}

.kanban-board {
  display: grid;
  min-width: 882px;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  align-items: start;
  gap: 16px;
}

.kanban-column {
  min-height: 310px;
  overflow: hidden;
  background: #f5f7fb;
  border: 1px solid #edf0f5;
  border-radius: 9px;
  transition: background .16s ease, border-color .16s ease, box-shadow .16s ease;
}

.column-drop-active {
  background: #eef4ff;
  border-color: #93b4f8;
  box-shadow: 0 0 0 3px rgb(79 145 248 / 12%);
}

.column-heading {
  display: flex;
  min-height: 40px;
  align-items: center;
  gap: 9px;
  padding: 0 12px;
  color: #fff;
  font-size: 14px;
  font-weight: 700;
}

.column-0 .column-heading { background: #4b96f7; }
.column-1 .column-heading { background: #f49b12; }
.column-2 .column-heading { background: #08bf7b; }
.column-3 .column-heading { background: #ff6257; }

.column-count {
  display: grid;
  min-width: 21px;
  height: 21px;
  padding: 0 5px;
  place-items: center;
  color: rgb(255 255 255 / 90%);
  background: rgb(255 255 255 / 20%);
  border-radius: 999px;
  font-size: 10px;
}

.column-heading button {
  display: grid;
  width: 25px;
  height: 25px;
  margin-left: auto;
  place-items: center;
  color: #fff;
  background: rgb(255 255 255 / 15%);
  border: 1px solid rgb(255 255 255 / 35%);
  border-radius: 50%;
  font-size: 19px;
  line-height: 1;
  cursor: pointer;
}

.column-heading button:hover {
  background: rgb(255 255 255 / 30%);
}

.column-cards {
  display: flex;
  min-height: 265px;
  flex-direction: column;
  gap: 12px;
  padding: 13px;
}

.kanban-card {
  box-sizing: border-box;
  min-width: 0;
  padding: 13px 14px;
  background: #fff;
  border: 1px solid #e8ebf1;
  border-left: 3px solid #cbd5e1;
  border-radius: 9px;
  box-shadow: 0 2px 6px rgb(24 39 75 / 10%);
  cursor: pointer;
  transition: transform .16s ease, box-shadow .16s ease, opacity .16s ease;
}

.kanban-card.por-fazer { border-left-color: #7b8ba3; }
.kanban-card.em-curso { border-left-color: #4b83ef; }
.kanban-card.concluida { border-left-color: #19a974; }
.kanban-card.bloqueada { border-left-color: #ed6a60; }

.kanban-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 15px rgb(24 39 75 / 13%);
}

.kanban-card:active {
  cursor: grabbing;
}

.kanban-card:focus-visible {
  outline: 3px solid #a5b4fc;
  outline-offset: 2px;
}

.kanban-card.card-dragging {
  opacity: .4;
  transform: rotate(1deg);
}

.kanban-card.card-archived {
  cursor: default;
}

.card-topline,
.card-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.card-topline .category {
  max-width: calc(100% - 45px);
  overflow: hidden;
  margin: 0;
  padding: 3px 7px;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 9px;
}

.card-id {
  color: #9aa5b5;
  font-size: 9px;
  font-variant-numeric: tabular-nums;
}

.card-title {
  margin: 11px 0 0;
  color: #29364d;
  font-size: 12px;
  font-weight: 700;
  line-height: 1.5;
  overflow-wrap: anywhere;
}

.card-meta {
  justify-content: flex-start;
  margin-top: 11px;
}

.card-meta .priority {
  padding: 5px 9px;
  font-size: 10px;
}

.column-empty {
  display: flex;
  min-height: 82px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  color: #a0a9b8;
  border: 1px dashed #dfe4ed;
  border-radius: 7px;
  font-size: 9px;
  text-align: center;
}

.column-empty > span:first-child {
  font-size: 18px;
}

.board-loading {
  display: flex;
  min-height: 260px;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #75839a;
  font-size: 12px;
}

.board-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #dbe3f0;
  border-top-color: #4f46e5;
  border-radius: 50%;
  animation: board-spin .8s linear infinite;
}

@keyframes board-spin {
  to { transform: rotate(360deg); }
}

.category {
  display: inline-flex;
  align-items: center;
  margin-top: 8px;
  padding: 4px 8px;
  border: 1px solid #e9ebf5;
  border-radius: 999px;
  background: #f7f8fc;
  color: #67748b;
  font-size: 10px;
  font-weight: 600;
}

.priority {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border: 1px solid transparent;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  line-height: 1;
  white-space: nowrap;
}

.priority::before {
  width: 7px;
  height: 7px;
  flex: 0 0 7px;
  border-radius: 50%;
  background: currentColor;
  content: '';
}

.priority.prioridade-baixa {
  border-color: #b7ebcb;
  color: #147a49;
  background: #eaf8ef;
}

.prioridade-media {
  border-color: #f5dda0;
  color: #9a6308;
  background: #fff7df;
}

.prioridade-alta {
  border-color: #f4c2c2;
  color: #b33131;
  background: #fff0ef;
}

.detail-status-select {
  min-width: 140px;
  padding: 9px 34px 9px 12px;
  border: 1px solid transparent;
  border-radius: 999px;
  font: inherit;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}

.detail-status-select.por-fazer {
  border-color: #d7dfe9;
  color: #526174;
  background: #f1f4f8;
}

.detail-status-select.em-curso {
  border-color: #c5d7ff;
  color: #315eb7;
  background: #edf3ff;
}

.detail-status-select.concluida {
  border-color: #b7ebcb;
  color: #147a49;
  background: #eaf8ef;
}

.detail-status-select.bloqueada {
  border-color: #f4c2c2;
  color: #b33131;
  background: #fff0ef;
}

.detail-status-select:disabled {
  background: #f8fafc;
  color: #64748b;
  cursor: not-allowed;
}

.detail-status-select:focus-visible {
  outline: 3px solid #c7d2fe;
  outline-offset: 2px;
}

.actions-column {
  min-width: 190px;
}

.action-buttons {
  display: flex;
  align-items: center;
  gap: 6px;
}

.view-button,
.edit-button,
.delete-button {
  padding: 7px 9px;
  border: 0;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}

.view-button {
  background: #f1f5f9;
  color: #334155;
}

.view-button:hover {
  background: #e2e8f0;
}

.edit-button {
  background: #eef2ff;
  color: #4338ca;
}

.edit-button:hover {
  background: #e0e7ff;
}

.delete-button {
  background: #fef2f2;
  color: #b91c1c;
}

.delete-button:hover {
  background: #fee2e2;
}

.edit-button:disabled,
.delete-button:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.empty-state {
  padding: 32px;
  text-align: center;
  color: #64748b;
}

.results-count {
  margin: 13px 2px 0;
  color: #7c879b;
  font-size: 11px;
}

.task-table-section {
  margin-top: 26px;
  padding: 24px;
  border: 1px solid #e6eaf2;
  border-radius: 15px;
  background:
    radial-gradient(ellipse at 2% 0%, rgb(238 242 255 / 70%), transparent 36%),
    #fff;
  box-shadow: 0 8px 24px rgb(23 37 84 / 4%);
  font-family: var(--tf-font);
}

.task-table-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.task-table-heading .section-eyebrow {
  margin-bottom: 5px;
}

.task-table-heading h2 {
  margin: 0 0 5px;
  color: #243452;
  font-size: 20px;
  font-weight: 750;
  letter-spacing: -.035em;
}

.task-table-heading p {
  margin: 0;
  color: #8792a5;
  font-size: 12px;
  line-height: 1.5;
}

.table-search {
  display: flex;
  width: min(100%, 310px);
  min-height: 42px;
  align-items: center;
  gap: 10px;
  padding: 0 13px;
  border: 1px solid #e3e8f1;
  border-radius: 10px;
  background: rgb(255 255 255 / 88%);
  color: #7d8aa1;
  transition: border-color .18s ease, box-shadow .18s ease, background .18s ease;
}

.table-search:focus-within {
  border-color: #818cf8;
  background: #fff;
  box-shadow: 0 0 0 4px rgb(99 102 241 / 10%);
}

.table-search > span {
  font-size: 18px;
}

.table-search input {
  width: 100%;
  min-width: 0;
  border: 0;
  outline: 0;
  color: #26344c;
  font: inherit;
  font-size: 13px;
}

.table-search input::placeholder {
  color: #a0a9b8;
}

.task-table-scroll {
  width: 100%;
  overflow-x: auto;
  border: 1px solid #e8edf4;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 2px 6px rgb(23 37 84 / 2%);
  scrollbar-color: #cbd5e1 transparent;
  scrollbar-width: thin;
}

.task-table {
  width: 100%;
  min-width: 900px;
  border-collapse: collapse;
  text-align: left;
}

.task-table th,
.task-table td {
  padding: 13px 15px;
  border-bottom: 1px solid #eff2f7;
  color: #475569;
  font-size: 12px;
  vertical-align: middle;
}

.task-table th {
  position: sticky;
  top: 0;
  z-index: 1;
  background: #f7f8fc;
  color: #77839a;
  font-size: 10px;
  font-weight: 750;
  letter-spacing: .055em;
  text-transform: uppercase;
  white-space: nowrap;
}

.task-table th:first-child {
  padding-left: 18px;
}

.task-table th button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0;
  border: 0;
  background: transparent;
  color: inherit;
  font: inherit;
  cursor: pointer;
  transition: color .16s ease;
}

.task-table th button span {
  color: #9ba6b7;
  font-size: 12px;
}

.task-table th button:hover,
.task-table th[aria-sort="ascending"] button,
.task-table th[aria-sort="descending"] button {
  color: #4f46e5;
}

.task-table tbody tr:last-child td {
  border-bottom: 0;
}

.task-table tbody tr:hover {
  background: #f8faff;
}

.task-table tbody tr {
  transition: background .15s ease;
}

.task-table .table-task-id {
  padding-left: 18px;
  color: #8995a8;
  font-variant-numeric: tabular-nums;
  font-size: 11px;
  font-weight: 650;
}

.table-task-title {
  display: block;
  max-width: 340px;
  padding: 0;
  border: 0;
  background: transparent;
  color: #26344c;
  font: inherit;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.45;
  text-align: left;
  cursor: pointer;
}

.table-task-title:hover {
  color: #4f46e5;
  text-decoration: underline;
}

.table-task-category {
  display: inline-flex;
  padding: 3px 7px;
  margin-top: 6px;
  border-radius: 5px;
  background: #f1f3f9;
  color: #78859a;
  font-size: 10px;
  font-weight: 550;
}

.table-status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 9px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 650;
  white-space: nowrap;
}

.table-status::before {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  content: '';
}

.table-status.por-fazer { background: #f1f5f9; color: #526078; }
.table-status.em-curso { background: #eff6ff; color: #2563eb; }
.table-status.concluida { background: #ecfdf5; color: #15803d; }
.table-status.bloqueada { background: #fef2f2; color: #b91c1c; }

.table-action {
  padding: 7px 11px;
  border: 1px solid #e2e5ff;
  border-radius: 7px;
  background: #f4f5ff;
  color: #4f46e5;
  font-size: 11px;
  font-weight: 650;
  cursor: pointer;
  transition: background .16s ease, border-color .16s ease, transform .16s ease;
}

.table-action:hover {
  transform: translateY(-1px);
  border-color: #c9ceff;
  background: #e9ebff;
}

.task-table .table-empty {
  padding: 28px 14px;
  color: #8792a5;
  text-align: center;
}

.table-pagination,
.table-page-size,
.table-page-controls {
  display: flex;
  align-items: center;
  gap: 10px;
}

.table-pagination {
  justify-content: space-between;
  gap: 16px;
  padding: 15px 3px 0;
  color: #78859a;
  font-size: 12px;
}

.table-page-size select {
  min-height: 34px;
  padding: 0 9px;
  border: 1px solid #e1e6ef;
  border-radius: 7px;
  background: #fff;
  color: #475569;
}

.table-page-controls button {
  min-height: 34px;
  padding: 0 11px;
  border: 1px solid #e1e6ef;
  border-radius: 7px;
  background: white;
  color: #475569;
  font-size: 11px;
  cursor: pointer;
  transition: background .16s ease, border-color .16s ease;
}

.table-page-controls button:hover:not(:disabled) {
  border-color: #cbd5e1;
  background: #f8fafc;
}

.table-page-controls button:disabled {
  opacity: .45;
  cursor: not-allowed;
}

/* MODAL DE DETALHES */

.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
  background: rgba(15, 23, 42, 0.58);
  overflow-y: auto;
}

.details-modal {
  width: 100%;
  max-width: 680px;
  max-height: 90vh;
  overflow-y: auto;
  padding: 26px;
  border-radius: 16px;
  background: white;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
  animation: modalEntrada 0.2s ease;
}

@keyframes modalEntrada {
  from {
    opacity: 0;
    transform: translateY(12px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.details-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 18px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e2e8f0;
}

.details-eyebrow {
  color: #6366f1;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 1px;
}

.details-header h2 {
  margin: 8px 0 0;
  color: #172033;
  font-size: 22px;
  overflow-wrap: anywhere;
}

.details-content {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
  padding: 24px 0;
}

.detail-item {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
  min-width: 0;
}

.detail-item > span:first-child {
  color: #64748b;
  font-size: 12px;
  font-weight: 600;
}

.detail-item strong {
  color: #172033;
  font-size: 14px;
  overflow-wrap: anywhere;
}

.detail-item p {
  margin: 0;
  color: #334155;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.details-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  padding-top: 18px;
  border-top: 1px solid #e2e8f0;
}

.delete-task-button {
  padding: 12px 16px;
  margin-right: auto;
  color: #b91c1c;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 10px;
  font-weight: 650;
  cursor: pointer;
}

.delete-task-button:hover:not(:disabled) {
  background: #fee2e2;
}

.delete-task-button:disabled {
  opacity: .55;
  cursor: not-allowed;
}

@media (max-width: 1200px) {
  .filters > select {
    flex: 1 1 135px;
  }
}

@media (max-width: 600px) {
  .page {
    padding: 8px 0 24px;
  }

  .page-header {
    align-items: stretch;
    flex-direction: column;
    padding: 20px;
    border-radius: 17px;
  }

  .page-header h1 {
    font-size: 27px;
  }

  .page-header > .primary-button {
    width: 100%;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }

  .full-width {
    grid-column: auto;
  }

  .tasks-section {
    padding: 14px;
    border-radius: 15px;
  }

  .section-heading {
    align-items: flex-start;
  }

  .task-table-heading,
  .table-pagination {
    align-items: stretch;
    flex-direction: column;
  }

  .task-table-section {
    padding: 16px;
    border-radius: 13px;
  }

  .table-search {
    width: auto;
  }

  .table-pagination {
    gap: 11px;
  }

  .table-page-size,
  .table-page-controls {
    justify-content: space-between;
  }

  .task-count {
    padding: 7px 9px;
    font-size: 10px;
  }

  .form-card {
    padding: 16px;
  }

  .form-actions {
    flex-direction: column-reverse;
  }

  .form-actions button {
    width: 100%;
  }

  .form-actions .primary-button {
    min-width: 0;
  }

  .details-modal {
    padding: 18px;
  }

  .details-content {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .details-actions {
    flex-direction: column-reverse;
  }

  .details-actions button {
    width: 100%;
  }

  .delete-task-button {
    margin: 0;
  }
}

@media (prefers-reduced-motion: reduce) {
  .kanban-card,
  .column-drop-active,
  .primary-button,
  .secondary-button,
  .new-task-button {
    transition: none;
  }

  .board-spinner {
    animation-duration: 2s;
  }
}
</style>
