
<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'

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
  role: 'owner' | 'member'
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

const config = useRuntimeConfig()
const apiBase = String(config.public.apiBase).replace(/\/$/, '')
const route = useRoute()

// Temporário até implementarmos autenticação.
const utilizadorId = 1

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

const mostrarFormulario = ref(false)
const modoFormulario = ref<ModoFormulario>('criar')
const tarefaEmEdicao = ref<number | null>(null)

const mostrarDetalhes = ref(false)
const tarefaSelecionada = ref<Tarefa | null>(null)

const formularioRef = ref<HTMLElement | null>(null)

const erro = ref('')
const sucesso = ref('')
const carregando = ref(false)
const aGuardar = ref(false)
const tarefaEmEliminacao = ref<number | null>(null)
const carregandoMembros = ref(false)

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
    (projeto) => projeto.status === 'active',
  ),
)

const membrosAtivos = computed(() =>
  membrosProjeto.value.filter(
    (membro) => membro.is_active,
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

async function abrirFormularioCriar() {
  erro.value = ''
  sucesso.value = ''
  mostrarDetalhes.value = false

  limparFormulario()

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

  if (!projectId) {
    carregandoMembros.value = false
    return
  }

  carregandoMembros.value = true

  try {
    const membros = await $fetch<MembroAPI[]>(
      `${apiBase}/projects/${projectId}/members`,
    )

    if (pedidoAtual !== pedidoMembros) return

    membrosProjeto.value = membros

  } catch (error) {
    console.error('Erro ao carregar membros do projeto:', error)

    if (pedidoAtual === pedidoMembros) {
      membrosProjeto.value = []
      erro.value = 'Não foi possível carregar os membros deste projeto.'
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
    const [
      listaProjetos,
      listaUtilizadores,
      listaTarefas,
    ] = await Promise.all([
      $fetch<ProjetoAPI[]>(`${apiBase}/projects/`),
      $fetch<UtilizadorAPI[]>(`${apiBase}/users/`),
      $fetch<TarefaAPI[]>(`${apiBase}/tasks/`),
    ])

    projetosDisponiveis.value = listaProjetos.map((projeto) => ({
      id: projeto.id,
      name: projeto.name,
      status: projeto.status,
      created_by: projeto.created_by,
    }))

    utilizadores.value = listaUtilizadores.filter(
      (utilizador) => utilizador.is_active,
    )

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

  aGuardar.value = true

  try {
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
      resultado = await $fetch<TarefaAPI>(
        `${apiBase}/tasks/`,
        {
          method: 'POST',
          body: {
            project_id: projetoId,
            ...corpo,
            created_by: utilizadorId,
          },
        },
      )

      tarefas.value.unshift(converterTarefa(resultado))
      sucesso.value = 'Tarefa criada com sucesso.'

    } else {
      resultado = await $fetch<TarefaAPI>(
        `${apiBase}/tasks/${tarefaEmEdicao.value}`,
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
  evento: Event,
) {
  const elemento = evento.target as HTMLSelectElement

  const estadoAnterior = tarefa.status
  const novoEstado = elemento.value as EstadoTarefa

  if (!estados.includes(novoEstado)) return
  if (novoEstado === estadoAnterior) return

  if (tarefa.projectStatus === 'archived') {
    erro.value = 'Não é possível alterar tarefas de projetos arquivados.'
    elemento.value = estadoAnterior
    return
  }

  erro.value = ''
  sucesso.value = ''

  tarefa.status = novoEstado

  try {
    const atualizada = await $fetch<TarefaAPI>(
      `${apiBase}/tasks/${tarefa.id}`,
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
      tarefas.value[indice] = converterTarefa(atualizada)
    }

    sucesso.value = 'Estado da tarefa atualizado.'

  } catch (error: any) {
    console.error('Erro ao atualizar estado:', error)

    tarefa.status = estadoAnterior
    elemento.value = estadoAnterior

    erro.value =
      error?.data?.detail ||
      'Não foi possível atualizar o estado da tarefa.'
  }
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

  const confirmado = window.confirm(
    `Tens a certeza de que pretendes eliminar a tarefa "${tarefa.title}"? Esta operação não pode ser desfeita.`,
  )

  if (!confirmado) return

  tarefaEmEliminacao.value = tarefa.id

  try {
    await $fetch(
      `${apiBase}/tasks/${tarefa.id}`,
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

// --------------------------------------------------
// CLASSES CSS
// --------------------------------------------------

function classeEstado(estado: EstadoTarefa) {
  return {
    'por-fazer': estado === 'Por fazer',
    'em-curso': estado === 'Em curso',
    'concluida': estado === 'Concluída',
    'bloqueada': estado === 'Bloqueada',
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
  <main class="page">

    <!-- CABEÇALHO -->
    <header class="page-header">
      <div>
        <NuxtLink to="/" class="back-link">
          ← Voltar ao painel
        </NuxtLink>

        <h1>Tarefas</h1>

        <p>
          Organiza o trabalho, acompanha os prazos e atualiza o progresso.
        </p>
      </div>

      <button
        class="primary-button"
        type="button"
        @click="abrirFormularioCriar"
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

    <!-- CARREGAMENTO -->
    <p v-if="carregando" class="empty-state">
      A carregar tarefas...
    </p>

    <!-- RESUMO -->
    <section class="summary-grid">
      <article class="summary-card">
        <span>Total de tarefas</span>
        <strong>{{ resumo.total }}</strong>
      </article>

      <article class="summary-card summary-todo">
        <span>Por fazer</span>
        <strong>{{ resumo.porFazer }}</strong>
      </article>

      <article class="summary-card summary-progress">
        <span>Em curso</span>
        <strong>{{ resumo.emCurso }}</strong>
      </article>

      <article class="summary-card summary-completed">
        <span>Concluídas</span>
        <strong>{{ resumo.concluidas }}</strong>
      </article>

      <article class="summary-card summary-blocked">
        <span>Bloqueadas</span>
        <strong>{{ resumo.bloqueadas }}</strong>
      </article>
    </section>

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
                {{ membro.name }} — {{ membro.role === 'owner' ? 'Responsável' : 'Membro' }}
              </option>
            </select>

            <small v-if="carregandoMembros">
              A carregar membros...
            </small>

            <small v-else-if="novaTarefa.projectId && membrosAtivos.length === 0">
              Este projeto ainda não tem membros ativos.
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

      <div class="section-heading">
        <div>
          <span class="section-eyebrow">ACOMPANHAMENTO</span>
          <h2>Lista de tarefas</h2>
          <p>Consulta e gere as tarefas dos projetos.</p>
        </div>
        <span class="task-count">
          {{ tarefasFiltradas.length }}
          {{ tarefasFiltradas.length === 1 ? 'tarefa' : 'tarefas' }}
        </span>
      </div>

      <!-- FILTROS -->
      <div class="filters">

        <input
          v-model="pesquisa"
          type="search"
          placeholder="Pesquisar tarefa, projeto ou responsável..."
          aria-label="Pesquisar tarefas"
        />

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

        <select
          v-model="filtroEstado"
          aria-label="Filtrar por estado"
        >
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

        <select
          v-model="filtroPrioridade"
          aria-label="Filtrar por prioridade"
        >
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

        <select
          v-model="filtroCategoria"
          aria-label="Filtrar por categoria"
        >
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

      <!-- TABELA -->
      <div class="table-container">
        <table>

          <thead>
            <tr>
              <th>Tarefa</th>
              <th>Projeto</th>
              <th>Responsável</th>
              <th>Prazo</th>
              <th>Prioridade</th>
              <th>Estado</th>
              <th class="actions-column">Ações</th>
            </tr>
          </thead>

          <tbody>

            <tr
              v-for="tarefa in tarefasFiltradas"
              :key="tarefa.id"
            >

              <td>
                <div class="task-title">
                  {{ tarefa.title }}
                </div>

                <div
                  v-if="tarefa.description"
                  class="task-description"
                >
                  {{ tarefa.description }}
                </div>

                <span class="category">
                  {{ tarefa.category }}
                </span>
              </td>

              <td>
                {{ tarefa.project }}
              </td>

              <td>
                {{ tarefa.responsible }}
              </td>

              <td>
                {{ formatarData(tarefa.dueDate) }}
              </td>

              <td>
                <span
                  class="priority"
                  :class="classePrioridade(tarefa.priority)"
                >
                  {{ tarefa.priority }}
                </span>
              </td>

              <td>
                <select
                  class="status-select"
                  :class="classeEstado(tarefa.status)"
                  :value="tarefa.status"
                  :disabled="tarefa.projectStatus === 'archived'"
                  :aria-label="`Estado da tarefa ${tarefa.title}`"
                  @change="alterarEstado(tarefa, $event)"
                >
                  <option
                    v-for="estado in estados"
                    :key="estado"
                    :value="estado"
                  >
                    {{ estado }}
                  </option>
                </select>
              </td>

              <td>
                <div class="action-buttons">
                  <button
                    type="button"
                    class="view-button"
                    title="Consultar detalhes"
                    @click="consultarTarefa(tarefa)"
                  >
                    Ver
                  </button>

                  <button
                    type="button"
                    class="edit-button"
                    :disabled="tarefa.projectStatus === 'archived'"
                    title="Editar tarefa"
                    @click="editarTarefa(tarefa)"
                  >
                    Editar
                  </button>

                  <button
                    type="button"
                    class="delete-button"
                    :disabled="
                      tarefa.projectStatus === 'archived' ||
                      tarefaEmEliminacao === tarefa.id
                    "
                    title="Eliminar tarefa"
                    @click="eliminarTarefa(tarefa)"
                  >
                    {{
                      tarefaEmEliminacao === tarefa.id
                        ? 'A eliminar...'
                        : 'Eliminar'
                    }}
                  </button>
                </div>
              </td>

            </tr>

            <tr v-if="!carregando && tarefasFiltradas.length === 0">
              <td colspan="7" class="empty-state">
                Não foram encontradas tarefas com estes filtros.
              </td>
            </tr>

          </tbody>
        </table>
      </div>

      <p class="results-count">
        A mostrar {{ tarefasFiltradas.length }}
        de {{ tarefas.length }} tarefas
      </p>

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
            <span
              class="status-select"
              :class="classeEstado(tarefaSelecionada.status)"
            >
              {{ tarefaSelecionada.status }}
            </span>
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

        <footer class="details-actions">
          <button
            type="button"
            class="secondary-button"
            @click="fecharDetalhes"
          >
            Fechar
          </button>

          <button
            v-if="tarefaSelecionada.projectStatus !== 'archived'"
            type="button"
            class="primary-button"
            @click="editarTarefa(tarefaSelecionada)"
          >
            Editar tarefa
          </button>
        </footer>
      </section>
    </div>

  </main>
</template>

<style scoped>
.page {
  max-width: 1500px;
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
  border: 0;
  border-radius: 10px;
  padding: 12px 18px;
  font-weight: 650;
  cursor: pointer;
  transition: transform .2s ease, background .2s ease, box-shadow .2s ease, opacity .2s ease;
}

.primary-button {
  border: 1px solid #4f46e5;
  background: linear-gradient(135deg, #5b5ce2, #4338ca);
  color: white;
  box-shadow: 0 7px 16px -8px rgb(67 56 202 / 62%);
}

.primary-button:hover {
  background: linear-gradient(135deg, #4f46e5, #3730a3);
  transform: translateY(-2px);
  box-shadow: 0 10px 20px -8px rgb(67 56 202 / 62%);
}

.secondary-button {
  background: #f1f5f9;
  color: #334155;
}

.secondary-button:hover {
  background: #e2e8f0;
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

.summary-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 18px;
}

.summary-card {
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-height: 100px;
  padding: 17px 18px;
  border: 1px solid #e7ebf3;
  border-radius: 16px;
  background: linear-gradient(145deg, #fff 65%, #f8f9ff);
  box-shadow: 0 5px 16px rgb(23 37 84 / 3%);
  transition: transform .2s ease, box-shadow .2s ease, border-color .2s ease;
}

.summary-card::before {
  position: absolute;
  top: 0;
  right: 0;
  left: 0;
  height: 3px;
  background: #7c83ef;
  content: '';
}

.summary-card:hover {
  transform: translateY(-2px);
  border-color: #d9e0ef;
  box-shadow: 0 12px 22px -15px rgb(23 37 84 / 38%);
}

.summary-card span {
  color: #6f7d95;
  font-size: 12px;
  font-weight: 600;
}

.summary-card strong {
  color: #1e2b50;
  font-size: 29px;
  font-weight: 800;
  line-height: 1;
  font-variant-numeric: tabular-nums;
}

.summary-todo::before {
  background: #94a3b8;
}

.summary-progress::before {
  background: #3b82f6;
}

.summary-completed::before {
  background: #22a06b;
}

.summary-blocked::before {
  background: #ef6262;
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

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
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
  display: grid;
  grid-template-columns:
    minmax(220px, 2fr)
    repeat(4, minmax(140px, 1fr));
  gap: 10px;
  padding: 13px;
  margin-bottom: 16px;
  border: 1px solid #edf0f5;
  border-radius: 13px;
  background: #f8faff;
}

.table-container {
  overflow-x: auto;
  border: 1px solid #e8edf5;
  border-radius: 13px;
  background: #fff;
  scrollbar-color: #cbd5e1 transparent;
  scrollbar-width: thin;
}

table {
  width: 100%;
  min-width: 980px;
  border-collapse: collapse;
  text-align: left;
  font-size: 13px;
}

th {
  padding: 13px 12px;
  border-bottom: 1px solid #e8edf5;
  background: #f7f9fd;
  color: #738098;
  font-size: 10px;
  font-weight: 750;
  letter-spacing: .07em;
  text-transform: uppercase;
  white-space: nowrap;
}

td {
  padding: 14px 12px;
  border-bottom: 1px solid #edf0f5;
  vertical-align: middle;
  color: #526078;
}

tbody tr {
  transition: background .16s ease;
}

tbody tr:hover {
  background: #fafbff;
}

tbody tr:last-child td {
  border-bottom: 0;
}

.task-title {
  min-width: 180px;
  font-weight: 600;
  color: #263552;
  font-size: 13px;
}

.task-description {
  max-width: 280px;
  margin-top: 5px;
  color: #64748b;
  line-height: 1.5;
  overflow-wrap: anywhere;
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

.priority,
.status-select {
  display: inline-block;
  border: 0;
  border-radius: 20px;
  padding: 7px 10px;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}

.prioridade-baixa {
  color: #166534;
  background: #dcfce7;
}

.prioridade-media {
  color: #92400e;
  background: #fef3c7;
}

.prioridade-alta {
  color: #b91c1c;
  background: #fee2e2;
}

.status-select {
  max-width: 130px;
  cursor: pointer;
}

.status-select:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.status-select.por-fazer {
  color: #475569;
  background: #f1f5f9;
}

.status-select.em-curso {
  color: #1d4ed8;
  background: #dbeafe;
}

.status-select.concluida {
  color: #166534;
  background: #dcfce7;
}

.status-select.bloqueada {
  color: #b91c1c;
  background: #fee2e2;
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
  justify-content: flex-end;
  gap: 10px;
  padding-top: 18px;
  border-top: 1px solid #e2e8f0;
}

@media (max-width: 1200px) {
  .filters {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .filters input {
    grid-column: 1 / -1;
  }
}

@media (max-width: 900px) {
  .summary-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
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

  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 9px;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }

  .full-width {
    grid-column: auto;
  }

  .filters {
    grid-template-columns: 1fr;
  }

  .filters input {
    grid-column: auto;
  }

  .tasks-section {
    padding: 14px;
    border-radius: 15px;
  }

  .summary-card {
    min-height: 88px;
    padding: 14px;
  }

  .summary-card strong {
    font-size: 26px;
  }

  .section-heading {
    align-items: flex-start;
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

  .action-buttons {
    flex-wrap: wrap;
  }
}
</style>
