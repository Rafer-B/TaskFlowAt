
<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { scrollToPanel } from '~/composables/usePanelScroll'
import { fetchAllPages } from '~/composables/usePaginatedApi'

// Centraliza catálogo, estado e associações; as capacidades do papel controlam ações disponíveis.
definePageMeta({ layout: 'admin' })

interface ProjetoAPI {
  id: string
  name: string
  description: string | null
  status: 'active' | 'completed' | 'archived'
  team_id: string | null
  created_by: string
  created_at: string
  updated_at: string
  archived_at: string | null
  current_user_role: 'admin' | 'owner' | 'contributor' | 'viewer'
}

interface MembroAPI {
  project_id: string
  user_id: string
  name: string
  email: string
  is_active: boolean
  role: 'owner' | 'contributor' | 'viewer'
  avatar_url: string | null
}

interface UtilizadorDisponivelAPI {
  id: string
  name: string
  email: string
  avatar_url: string | null
}

interface EquipaDisponivelAPI {
  id: string
  name: string
  can_associate_projects: boolean
}

interface MembroEquipaAPI {
  user_id: string
  name: string
  email: string
  avatar_url: string | null
}

interface EquipaProjetoAPI {
  id: string
  name: string
  can_manage: boolean
}

type EstadoProjeto = 'Ativo' | 'Concluído' | 'Arquivado'
type FiltroEstado = 'Todos' | EstadoProjeto
type AcaoProjeto = 'archive' | 'delete'
type ChaveOrdenacaoProjetos = 'id' | 'name' | 'status' | 'createdAt' | 'currentUserRole'

const colunasTabelaProjetos: Array<{
  chave: ChaveOrdenacaoProjetos
  rotulo: string
}> = [
  { chave: 'id', rotulo: 'ID' },
  { chave: 'name', rotulo: 'Projeto' },
  { chave: 'status', rotulo: 'Estado' },
  { chave: 'currentUserRole', rotulo: 'O teu papel' },
  { chave: 'createdAt', rotulo: 'Criado em' },
]

interface Projeto {
  id: string
  name: string
  description: string
  status: EstadoProjeto
  createdAt: string
  teamId: string | null
  currentUserRole: ProjetoAPI['current_user_role']
}

const config = useRuntimeConfig()
const apiBase = String(config.public.apiBase).replace(/\/$/, '')
const api = useNuxtApp().$api
const auth = useAuth()
const route = useRoute()

// Dados dos projetos
const projetos = ref<Projeto[]>([])
const carregando = ref(false)
const aGuardar = ref(false)
const aAtualizarEstado = ref<string | null>(null)
const aEliminar = ref(false)

// Pesquisa e filtros
const pesquisa = ref('')
const filtroEstado = ref<FiltroEstado>('Todos')
const paginaProjetos = ref(1)
const tamanhoPaginaProjetos = ref(10)
const ordenacaoProjetos = ref<{
  chave: ChaveOrdenacaoProjetos
  ascendente: boolean
}>({
  chave: 'name',
  ascendente: true,
})

watch(
  () => route.query.search,
  (value) => {
    pesquisa.value = Array.isArray(value) ? value[0] ?? '' : value ?? ''
  },
  { immediate: true },
)

// Formulário de projeto
const mostrarFormulario = ref(false)
const formularioRef = ref<HTMLElement | null>(null)
const modoEdicao = ref(false)
const projetoEmEdicao = ref<string | null>(null)
const equipasDisponiveis = ref<EquipaDisponivelAPI[]>([])
const membrosCandidatos = ref<UtilizadorDisponivelAPI[]>([])
const membrosSelecionados = ref<string[]>([])
const tarefasIniciais = ref<Array<{ title: string; description: string }>>([])
const aCarregarOpcoesCriacao = ref(false)
const opcoesCriacaoCarregadas = ref(false)

const formulario = ref({
  name: '',
  description: '',
  team_id: '',
})

// Confirmações de projeto
const mostrarConfirmacao = ref(false)
const acaoConfirmada = ref<AcaoProjeto | null>(null)
const projetoSelecionado = ref<Projeto | null>(null)

// Mensagens gerais
const erro = ref('')
const sucesso = ref('')

// --------------------------------------------------
// GESTÃO DE MEMBROS
// --------------------------------------------------

const mostrarPainelMembros = ref(false)
const painelMembrosRef = ref<HTMLElement | null>(null)
const membroPendenteRemocao = ref<string | null>(null)
const projetoMembros = ref<Projeto | null>(null)
const membros = ref<MembroAPI[]>([])
const utilizadoresDisponiveis = ref<UtilizadorDisponivelAPI[]>([])
const equipaProjeto = ref<EquipaProjetoAPI | null>(null)
const membrosEquipa = ref<MembroEquipaAPI[]>([])
const utilizadoresDisponiveisEquipa = ref<MembroEquipaAPI[]>([])

const carregandoMembros = ref(false)
const carregandoUtilizadoresDisponiveis = ref(false)
const aAdicionarMembro = ref(false)
const aAdicionarMembroEquipa = ref(false)
const membroEmAtualizacao = ref<string | null>(null)
const membroEmRemocao = ref<string | null>(null)

const erroMembros = ref('')
const sucessoMembros = ref('')

const novoMembro = ref({
  user_id: '',
  role: 'contributor' as 'owner' | 'contributor' | 'viewer',
})
const novoMembroEquipa = ref('')

const totalOwners = computed(
  () => membros.value.filter(membro => membro.role === 'owner').length,
)

// Administradores ou responsáveis podem gerir dados e membros do projeto.
const podeGerirProjeto = (projeto: Projeto): boolean =>
  auth.user.value?.role === 'admin' ||
  projeto.currentUserRole === 'owner'

const podeCriarTarefas = (projeto: Projeto): boolean =>
  auth.user.value?.role === 'admin' ||
  projeto.currentUserRole === 'owner' ||
  projeto.currentUserRole === 'contributor'

// --------------------------------------------------
// ESTADOS DOS PROJETOS
// --------------------------------------------------

const estadosAPI: Record<ProjetoAPI['status'], EstadoProjeto> = {
  active: 'Ativo',
  completed: 'Concluído',
  archived: 'Arquivado',
}

const estadosUI: Record<EstadoProjeto, ProjetoAPI['status']> = {
  Ativo: 'active',
  'Concluído': 'completed',
  Arquivado: 'archived',
}

function converterProjeto(projeto: ProjetoAPI): Projeto {
  return {
    id: projeto.id,
    name: projeto.name,
    description: projeto.description ?? '',
    status: estadosAPI[projeto.status],
    createdAt: projeto.created_at,
    teamId: projeto.team_id,
    currentUserRole: projeto.current_user_role,
  }
}

function construirUrlAvatar(avatarUrl: string | null): string {
  return obterUrlAvatar(avatarUrl, apiBase)
}
function formatarData(data: string): string {
  if (!data) return 'Data indisponível'

  const dataValida = new Date(data)

  if (Number.isNaN(dataValida.getTime())) {
    return 'Data indisponível'
  }

  return new Intl.DateTimeFormat('pt-PT', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(dataValida)
}

function classeEstado(estado: EstadoProjeto): string {
  const classes: Record<EstadoProjeto, string> = {
    Ativo: 'active',
    'Concluído': 'completed',
    Arquivado: 'archived',
  }

  return classes[estado]
}

function nomePapelProjeto(papel: ProjetoAPI['current_user_role']): string {
  const nomes: Record<ProjetoAPI['current_user_role'], string> = {
    admin: 'Administrador',
    owner: 'Responsável',
    contributor: 'Colaborador',
    viewer: 'Observador',
  }
  return nomes[papel]
}

// --------------------------------------------------
// INDICADORES E FILTROS
// --------------------------------------------------

const totalProjetos = computed(() => projetos.value.length)

const projetosAtivos = computed(
  () => projetos.value.filter(p => p.status === 'Ativo').length,
)

const projetosConcluidos = computed(
  () => projetos.value.filter(p => p.status === 'Concluído').length,
)

const projetosArquivados = computed(
  () => projetos.value.filter(p => p.status === 'Arquivado').length,
)

const projetosFiltrados = computed(() => {
  const termo = pesquisa.value.trim().toLowerCase()

  return projetos.value.filter(projeto => {
    const correspondePesquisa =
      !termo ||
      `${projeto.name} ${projeto.description}`
        .toLowerCase()
        .includes(termo)

    const correspondeEstado =
      filtroEstado.value === 'Todos' ||
      projeto.status === filtroEstado.value

    return correspondePesquisa && correspondeEstado
  })
})

const projetosOrdenados = computed(() => {
  const { chave, ascendente } = ordenacaoProjetos.value

  return [...projetosFiltrados.value].sort((a, b) => {
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

const totalPaginasProjetos = computed(() =>
  Math.max(1, Math.ceil(projetosOrdenados.value.length / tamanhoPaginaProjetos.value)),
)

const projetosDaPagina = computed(() => {
  const inicio = (paginaProjetos.value - 1) * tamanhoPaginaProjetos.value
  return projetosOrdenados.value.slice(inicio, inicio + tamanhoPaginaProjetos.value)
})

const inicioProjetos = computed(() =>
  projetosOrdenados.value.length
    ? (paginaProjetos.value - 1) * tamanhoPaginaProjetos.value + 1
    : 0,
)

const fimProjetos = computed(() =>
  Math.min(
    paginaProjetos.value * tamanhoPaginaProjetos.value,
    projetosOrdenados.value.length,
  ),
)

watch([pesquisa, filtroEstado, tamanhoPaginaProjetos], () => {
  paginaProjetos.value = 1
})

watch(totalPaginasProjetos, (total) => {
  if (paginaProjetos.value > total) paginaProjetos.value = total
})

function ordenarProjetos(chave: ChaveOrdenacaoProjetos): void {
  ordenacaoProjetos.value = ordenacaoProjetos.value.chave === chave
    ? { chave, ascendente: !ordenacaoProjetos.value.ascendente }
    : { chave, ascendente: true }
  paginaProjetos.value = 1
}

// --------------------------------------------------
// CARREGAR PROJETOS
// --------------------------------------------------

async function carregarProjetos() {
  erro.value = ''
  carregando.value = true

  try {
    const resposta = await fetchAllPages<ProjetoAPI>('/projects/')

    projetos.value = resposta.map(converterProjeto)
  } catch (error) {
    console.error('Erro ao carregar projetos:', error)
    erro.value = 'Não foi possível carregar os projetos. Verifica a ligação à API.'
  } finally {
    carregando.value = false
  }
}

// --------------------------------------------------
// CRIAR E EDITAR PROJETOS
// --------------------------------------------------

async function abrirCriacao() {
  erro.value = ''
  sucesso.value = ''
  modoEdicao.value = false
  projetoEmEdicao.value = null
  membrosSelecionados.value = []
  tarefasIniciais.value = []
  equipasDisponiveis.value = []
  membrosCandidatos.value = []
  opcoesCriacaoCarregadas.value = false

  formulario.value = {
    name: '',
    description: '',
    team_id: '',
  }

  mostrarFormulario.value = true
  await scrollToPanel(formularioRef)
  await carregarOpcoesCriacao()
}

async function carregarOpcoesCriacao() {
  aCarregarOpcoesCriacao.value = true
  erro.value = ''
  try {
    const [equipas, candidatos] = await Promise.all([
      fetchAllPages<EquipaDisponivelAPI>('/teams/'),
      fetchAllPages<UtilizadorDisponivelAPI>('/projects/member-candidates'),
    ])
    equipasDisponiveis.value = equipas.filter(
      equipa => equipa.can_associate_projects,
    )
    membrosCandidatos.value = candidatos
    opcoesCriacaoCarregadas.value = true
  } catch (error) {
    console.error('Erro ao carregar opções para novo projeto:', error)
    erro.value = mensagemErroMembro(error)
  } finally {
    aCarregarOpcoesCriacao.value = false
  }
}

function adicionarTarefaInicial() {
  tarefasIniciais.value.push({ title: '', description: '' })
}

function removerTarefaInicial(index: number) {
  tarefasIniciais.value.splice(index, 1)
}

async function abrirEdicao(projeto: Projeto) {
  erro.value = ''
  sucesso.value = ''
  modoEdicao.value = true
  projetoEmEdicao.value = projeto.id

  formulario.value = {
    name: projeto.name,
    description: projeto.description,
    team_id: '',
  }

  mostrarFormulario.value = true
  await scrollToPanel(formularioRef)
}

function limparFormulario() {
  mostrarFormulario.value = false
  modoEdicao.value = false
  projetoEmEdicao.value = null
  erro.value = ''
  membrosSelecionados.value = []
  tarefasIniciais.value = []

  formulario.value = {
    name: '',
    description: '',
    team_id: '',
  }
}

function fecharFormulario() {
  if (aGuardar.value || aCarregarOpcoesCriacao.value) return

  limparFormulario()
}

async function guardarProjeto() {
  erro.value = ''
  sucesso.value = ''

  const name = formulario.value.name.trim()
  const description = formulario.value.description.trim()

  if (!name) {
    erro.value = 'O nome do projeto é obrigatório.'
    return
  }

  if (!modoEdicao.value && !auth.user.value) {
    erro.value = 'A sessão expirou. Inicia sessão novamente.'
    return
  }

  if (!modoEdicao.value && !opcoesCriacaoCarregadas.value) {
    erro.value = 'Carrega as opções de membros e equipas antes de criar o projeto.'
    return
  }

  if (
    !modoEdicao.value &&
    tarefasIniciais.value.some(tarefa => !tarefa.title.trim())
  ) {
    erro.value = 'Preenche o título de cada tarefa inicial ou remove a tarefa vazia.'
    return
  }

  aGuardar.value = true

  try {
    // O modo do formulário escolhe entre PATCH e POST sem duplicar a preparação dos campos.
    if (modoEdicao.value && projetoEmEdicao.value !== null) {
      const atualizado = await api<ProjetoAPI>(
        `/projects/${projetoEmEdicao.value}`,
        {
          method: 'PATCH',
          body: {
            name,
            description: description || null,
          },
        },
      )

      const index = projetos.value.findIndex(
        p => p.id === projetoEmEdicao.value,
      )

      if (index !== -1) {
        projetos.value[index] = converterProjeto(atualizado)
      }

      sucesso.value = 'Projeto atualizado com sucesso.'
    } else {
      const criado = await api<ProjetoAPI>(
        '/projects/',
        {
          method: 'POST',
          body: {
            name,
            description: description || null,
            team_id: formulario.value.team_id || null,
            member_ids: membrosSelecionados.value,
            tasks: tarefasIniciais.value.map(tarefa => ({
              title: tarefa.title.trim(),
              description: tarefa.description.trim() || null,
            })),
          },
        },
      )

      projetos.value.unshift(converterProjeto(criado))

      pesquisa.value = ''
      filtroEstado.value = 'Todos'

      sucesso.value = 'Projeto criado com sucesso, com as associações selecionadas.'
    }

    limparFormulario()
  } catch (error) {
    console.error('Erro ao guardar projeto:', error)
    erro.value = mensagemErroMembro(error)
  } finally {
    aGuardar.value = false
  }
}

// --------------------------------------------------
// ESTADOS DOS PROJETOS
// --------------------------------------------------

async function atualizarEstado(
  projeto: Projeto,
  novoEstado: EstadoProjeto,
) {
  erro.value = ''
  sucesso.value = ''
  aAtualizarEstado.value = projeto.id

  try {
    const atualizado = await api<ProjetoAPI>(
      `/projects/${projeto.id}`,
      {
        method: 'PATCH',
        body: {
          status: estadosUI[novoEstado],
        },
      },
    )

    const index = projetos.value.findIndex(
      p => p.id === projeto.id,
    )

    if (index !== -1) {
      projetos.value[index] = converterProjeto(atualizado)
    }

    sucesso.value = novoEstado === 'Ativo'
      ? 'Projeto reativado com sucesso.'
      : novoEstado === 'Concluído'
        ? 'Projeto concluído com sucesso.'
        : 'Projeto arquivado com sucesso.'
  } catch (error) {
    console.error('Erro ao atualizar estado:', error)
    erro.value = 'Não foi possível alterar o estado do projeto.'
  } finally {
    aAtualizarEstado.value = null
  }
}

function pedirConfirmacao(
  projeto: Projeto,
  acao: AcaoProjeto,
) {
  projetoSelecionado.value = projeto
  acaoConfirmada.value = acao
  mostrarConfirmacao.value = true
}

function fecharConfirmacao() {
  if (aEliminar.value) return

  mostrarConfirmacao.value = false
  projetoSelecionado.value = null
  acaoConfirmada.value = null
}

async function executarAcao() {
  const projeto = projetoSelecionado.value
  const acao = acaoConfirmada.value

  if (!projeto || !acao) return

  if (acao === 'archive') {
    // Arquivar preserva os registos; eliminar é uma operação separada e irreversível.
    mostrarConfirmacao.value = false
    await atualizarEstado(projeto, 'Arquivado')
    projetoSelecionado.value = null
    acaoConfirmada.value = null
    return
  }

  if (acao === 'delete') {
    await eliminarProjeto(projeto)
  }
}

async function eliminarProjeto(projeto: Projeto) {
  erro.value = ''
  sucesso.value = ''
  aEliminar.value = true

  try {
    await api(
      `/projects/${projeto.id}`,
      {
        method: 'DELETE',
      },
    )

    projetos.value = projetos.value.filter(
      p => p.id !== projeto.id,
    )

    sucesso.value = 'Projeto eliminado com sucesso.'
    mostrarConfirmacao.value = false
    projetoSelecionado.value = null
    acaoConfirmada.value = null
  } catch (error: unknown) {
    console.error('Erro ao eliminar projeto:', error)

    const resposta = error as {
      statusCode?: number
      data?: { detail?: string }
    }

    // O conflito indica dependências que impedem a eliminação do projeto.
    if (resposta.statusCode === 409) {
      erro.value =
        'Não é possível eliminar este projeto porque existem tarefas ou membros associados.'
    } else if (resposta.statusCode === 404) {
      erro.value = 'Este projeto já não existe.'
    } else {
      erro.value = resposta.data?.detail ||
        'Não foi possível eliminar o projeto.'
    }

    mostrarConfirmacao.value = false
    projetoSelecionado.value = null
    acaoConfirmada.value = null
  } finally {
    aEliminar.value = false
  }
}

// --------------------------------------------------
// ABRIR E FECHAR GESTÃO DE MEMBROS
// --------------------------------------------------

async function abrirMembros(projeto: Projeto) {
  projetoMembros.value = projeto
  mostrarPainelMembros.value = true
  await scrollToPanel(painelMembrosRef)
  membroPendenteRemocao.value = null

  membros.value = []
  equipaProjeto.value = null
  membrosEquipa.value = []
  novoMembro.value = {
    user_id: '',
    role: 'contributor',
  }
  novoMembroEquipa.value = ''
  utilizadoresDisponiveis.value = []
  utilizadoresDisponiveisEquipa.value = []

  erroMembros.value = ''
  sucessoMembros.value = ''

  await carregarMembros()
}

function fecharMembros() {
  if (
    carregandoMembros.value ||
    carregandoUtilizadoresDisponiveis.value ||
    aAdicionarMembro.value ||
    aAdicionarMembroEquipa.value ||
    membroEmAtualizacao.value !== null ||
    membroEmRemocao.value !== null
  ) {
    return
  }

  mostrarPainelMembros.value = false
  projetoMembros.value = null
  membroPendenteRemocao.value = null
  membros.value = []
  equipaProjeto.value = null
  membrosEquipa.value = []
  utilizadoresDisponiveis.value = []
  utilizadoresDisponiveisEquipa.value = []
  erroMembros.value = ''
  sucessoMembros.value = ''
}

// --------------------------------------------------
// LISTAR MEMBROS
// --------------------------------------------------

async function carregarMembros() {
  if (!projetoMembros.value) return

  carregandoMembros.value = true
  carregandoUtilizadoresDisponiveis.value = true
  erroMembros.value = ''

  try {
    const projeto = projetoMembros.value
    const podeGerir = podeGerirProjeto(projeto)
    const [membrosProjeto, utilizadoresProjeto] = await Promise.all([
      fetchAllPages<MembroAPI>(`/projects/${projeto.id}/members`),
      podeGerir
        ? fetchAllPages<UtilizadorDisponivelAPI>(
            `/projects/${projeto.id}/available-members`,
          )
        : Promise.resolve([]),
    ])
    membros.value = membrosProjeto
    utilizadoresDisponiveis.value = utilizadoresProjeto

    if (projeto.teamId !== null) {
      const [equipa, membrosDaEquipa] = await Promise.all([
        api<EquipaProjetoAPI>(`/teams/${projeto.teamId}`),
        fetchAllPages<MembroEquipaAPI>(`/teams/${projeto.teamId}/members`),
      ])
      equipaProjeto.value = equipa
      membrosEquipa.value = membrosDaEquipa
      utilizadoresDisponiveisEquipa.value = equipa.can_manage
        ? await fetchAllPages<MembroEquipaAPI>(
            `/teams/${projeto.teamId}/available-members`,
          )
        : []
    }

    erroMembros.value = ''
  } catch (error) {
    console.error('Erro ao carregar membros:', error)
    erroMembros.value = mensagemErroMembro(error)
  } finally {
    carregandoMembros.value = false
    carregandoUtilizadoresDisponiveis.value = false
  }
}

async function adicionarMembroEquipa() {
  if (!equipaProjeto.value?.can_manage || !novoMembroEquipa.value) return

  erroMembros.value = ''
  sucessoMembros.value = ''
  aAdicionarMembroEquipa.value = true

  try {
    const userId = novoMembroEquipa.value
    const novo = await api<MembroEquipaAPI>(
      `/teams/${equipaProjeto.value.id}/members`,
      {
        method: 'POST',
        body: { user_id: userId },
      },
    )
    membrosEquipa.value.push(novo)
    utilizadoresDisponiveisEquipa.value =
      utilizadoresDisponiveisEquipa.value.filter(
        utilizador => utilizador.user_id !== userId,
      )
    novoMembroEquipa.value = ''
    sucessoMembros.value = `Utilizador adicionado à equipa ${equipaProjeto.value.name}.`
  } catch (error) {
    console.error('Erro ao adicionar membro à equipa:', error)
    erroMembros.value = mensagemErroMembro(error)
  } finally {
    aAdicionarMembroEquipa.value = false
  }
}

function mensagemErroMembro(error: unknown): string {
  if (typeof error === 'object' && error !== null && 'data' in error) {
    const data = error.data
    if (
      typeof data === 'object' &&
      data !== null &&
      'detail' in data
    ) {
      if (typeof data.detail === 'string') return data.detail
      if (Array.isArray(data.detail)) {
        const primeiraMensagem = data.detail.find(
          (item): item is { msg: string } =>
            typeof item === 'object' &&
            item !== null &&
            'msg' in item &&
            typeof item.msg === 'string',
        )
        if (primeiraMensagem) return primeiraMensagem.msg
      }
    }
  }
  return 'Não foi possível concluir a operação. Confirma a ligação e as permissões.'
}

// --------------------------------------------------
// ADICIONAR MEMBRO
// --------------------------------------------------

async function adicionarMembro() {
  if (!projetoMembros.value) return

  erroMembros.value = ''
  sucessoMembros.value = ''

  const userId = novoMembro.value.user_id
  const utilizadorSelecionado = utilizadoresDisponiveis.value.find(
    utilizador => utilizador.id === userId,
  )
  if (!utilizadorSelecionado) {
    erroMembros.value = 'Seleciona uma conta existente e ativa.'
    return
  }

  aAdicionarMembro.value = true

  try {
    const novo = await api<MembroAPI>(
      `/projects/${projetoMembros.value.id}/members`,
      {
        method: 'POST',
        body: {
          user_id: userId,
          role: novoMembro.value.role,
        },
      },
    )

    membros.value.push(novo)

    novoMembro.value = {
      user_id: '',
      role: 'contributor',
    }

    sucessoMembros.value = 'Utilizador adicionado ao projeto com sucesso.'
    await carregarMembros()
  } catch (error: unknown) {
    console.error('Erro ao adicionar membro:', error)
    erroMembros.value = mensagemErroMembro(error)
  } finally {
    aAdicionarMembro.value = false
  }
}

// --------------------------------------------------
// ALTERAR RESPONSABILIDADE
// --------------------------------------------------

async function alterarResponsabilidade(
  membro: MembroAPI,
  novoRole: 'owner' | 'contributor' | 'viewer',
) {
  if (!projetoMembros.value) return
  if (membro.role === novoRole) return

  erroMembros.value = ''
  sucessoMembros.value = ''
  membroEmAtualizacao.value = membro.user_id

  try {
    const atualizado = await api<MembroAPI>(
      `/projects/${projetoMembros.value.id}/members/${membro.user_id}`,
      {
        method: 'PATCH',
        body: {
          role: novoRole,
        },
      },
    )

    const index = membros.value.findIndex(
      m => m.user_id === membro.user_id,
    )

    if (index !== -1) {
      membros.value[index] = atualizado
    }

    sucessoMembros.value = 'Responsabilidade atualizada com sucesso.'
  } catch (error: unknown) {
    console.error('Erro ao alterar responsabilidade:', error)

    const resposta = error as {
      statusCode?: number
      data?: { detail?: string }
    }

    erroMembros.value =
      resposta.data?.detail ||
      'Não foi possível alterar a responsabilidade.'

    // Repõe os dados apresentados com o estado atual da API após falha do PATCH.
    await carregarMembros()
  } finally {
    membroEmAtualizacao.value = null
  }
}

// --------------------------------------------------
// REMOVER MEMBRO
// --------------------------------------------------

async function removerMembro(membro: MembroAPI) {
  if (!projetoMembros.value) return

  if (membroPendenteRemocao.value !== membro.user_id) {
    membroPendenteRemocao.value = membro.user_id
    return
  }

  erroMembros.value = ''
  sucessoMembros.value = ''
  membroEmRemocao.value = membro.user_id

  try {
    await api(
      `/projects/${projetoMembros.value.id}/members/${membro.user_id}`,
      {
        method: 'DELETE',
      },
    )

    membros.value = membros.value.filter(
      m => m.user_id !== membro.user_id,
    )

    sucessoMembros.value = 'Membro removido do projeto com sucesso.'
    membroPendenteRemocao.value = null
    await carregarMembros()
  } catch (error: unknown) {
    console.error('Erro ao remover membro:', error)

    const resposta = error as {
      statusCode?: number
      data?: { detail?: string }
    }

    erroMembros.value =
      resposta.data?.detail ||
      'Não foi possível remover este membro.'
  } finally {
    membroEmRemocao.value = null
  }
}

onMounted(carregarProjetos)
</script>

<template>
  <main class="projects-page">

    <header class="page-heading">
      <div>
        <div class="breadcrumb">
          <NuxtLink to="/">Dashboard</NuxtLink>
          <span>/</span>
          <span>Projetos</span>
        </div>

        <h1>Projetos</h1>
        <p>Cria projetos, organiza equipas e acompanha o trabalho colaborativo.</p>
      </div>

      <button class="primary-button" aria-label="Novo projeto" @click="abrirCriacao">
        <ActionIcon name="add" />
        Novo projeto
      </button>
    </header>

    <!-- MENSAGENS GERAIS -->
    <Transition name="fade">
      <div v-if="sucesso" class="feedback success-feedback">
        <span>✓</span>
        {{ sucesso }}
        <button @click="sucesso = ''">×</button>
      </div>
    </Transition>

    <Transition name="fade">
      <div v-if="erro && !mostrarFormulario" class="feedback error-feedback">
        <span>!</span>
        {{ erro }}
        <button @click="erro = ''">×</button>
      </div>
    </Transition>

    <!-- ESTATÍSTICAS -->
    <section class="stats-grid">
      <article class="stat-card">
        <div class="stat-icon total-icon">▦</div>
        <div>
          <span>Total de projetos</span>
          <strong>{{ totalProjetos }}</strong>
          <small>Projetos registados</small>
        </div>
      </article>

      <article class="stat-card">
        <div class="stat-icon active-icon">◷</div>
        <div>
          <span>Projetos ativos</span>
          <strong>{{ projetosAtivos }}</strong>
          <small>Em desenvolvimento</small>
        </div>
      </article>

      <article class="stat-card">
        <div class="stat-icon completed-icon">✓</div>
        <div>
          <span>Concluídos</span>
          <strong>{{ projetosConcluidos }}</strong>
          <small>Projetos finalizados</small>
        </div>
      </article>

      <article class="stat-card">
        <div class="stat-icon archived-icon">▤</div>
        <div>
          <span>Arquivados</span>
          <strong>{{ projetosArquivados }}</strong>
          <small>Projetos arquivados</small>
        </div>
      </article>
    </section>

    <!-- FORMULÁRIO DE PROJETO -->
    <Transition name="form">
      <section v-if="mostrarFormulario" ref="formularioRef" class="form-card">
        <div class="form-heading">
          <div>
            <span class="eyebrow">
              {{ modoEdicao ? 'ATUALIZAÇÃO' : 'NOVO REGISTO' }}
            </span>

            <h2>
              {{ modoEdicao ? 'Editar projeto' : 'Criar novo projeto' }}
            </h2>

            <p>
              {{ modoEdicao
                ? 'Atualiza as informações deste projeto.'
                : 'Preenche os dados para adicionar um projeto ao TaskFlowAt.'
              }}
            </p>
          </div>

          <button
            class="close-button"
            type="button"
            :disabled="aGuardar || aCarregarOpcoesCriacao"
            @click="fecharFormulario"
          >
            ×
          </button>
        </div>

        <form @submit.prevent="guardarProjeto">
          <div class="form-field">
            <label for="project-name">
              Nome do projeto <span>*</span>
            </label>

            <input
              id="project-name"
              v-model="formulario.name"
              type="text"
              maxlength="255"
              placeholder="Ex.: Desenvolvimento do TaskFlowAt"
              required
            />
          </div>

          <div class="form-field">
            <label for="project-description">Descrição</label>

            <textarea
              id="project-description"
              v-model="formulario.description"
              rows="4"
              placeholder="Descreve os objetivos deste projeto..."
            />
          </div>

          <div
            v-if="!modoEdicao && !opcoesCriacaoCarregadas"
            class="creation-options-loading"
          >
            <p v-if="aCarregarOpcoesCriacao">A carregar equipas e membros disponíveis...</p>
            <template v-else>
              <p>Não foi possível carregar as opções de associação.</p>
              <button
                type="button"
                class="secondary-button action-tooltip"
                aria-label="Tentar novamente"
                :disabled="aCarregarOpcoesCriacao"
                @click="carregarOpcoesCriacao"
              >
                <ActionIcon name="refresh" />
                Tentar novamente
              </button>
            </template>
          </div>

          <template v-if="!modoEdicao && opcoesCriacaoCarregadas">
            <section class="creation-section">
              <div class="creation-section-heading">
                <h3>Associar a uma equipa</h3>
                <span>Opcional</span>
              </div>
              <div class="form-field">
                <label for="project-team">Equipa</label>
                <select id="project-team" v-model="formulario.team_id">
                  <option value="">Sem equipa</option>
                  <option
                    v-for="equipa in equipasDisponiveis"
                    :key="equipa.id"
                    :value="String(equipa.id)"
                  >
                    {{ equipa.name }}
                  </option>
                </select>
                <small v-if="!equipasDisponiveis.length">
                  Não tens equipas disponíveis para associar.
                </small>
              </div>
            </section>

            <section class="creation-section">
              <div class="creation-section-heading">
                <div>
                  <h3>Adicionar membros</h3>
                  <span>{{ membrosSelecionados.length }} selecionado(s) · máximo 100</span>
                </div>
                <small>O criador será responsável automaticamente</small>
              </div>
              <div v-if="membrosCandidatos.length" class="creation-member-list">
                <label
                  v-for="membro in membrosCandidatos"
                  :key="membro.id"
                  class="creation-member-option"
                >
                  <input
                    v-model="membrosSelecionados"
                    type="checkbox"
                    :value="membro.id"
                    :disabled="!membrosSelecionados.includes(membro.id) && membrosSelecionados.length >= 100"
                  />
                  <span class="member-avatar">
                    <img
                      v-if="membro.avatar_url"
                      :src="construirUrlAvatar(membro.avatar_url)"
                      :alt="`Fotografia de ${membro.name}`"
                    />
                    <span v-else>{{ membro.name.charAt(0).toUpperCase() }}</span>
                  </span>
                  <span class="creation-member-copy">
                    <strong>{{ membro.name }}</strong>
                    <small>{{ membro.email }}</small>
                  </span>
                </label>
              </div>
              <p v-else class="creation-empty-note">
                Não há outros utilizadores ativos para adicionar.
              </p>
            </section>

            <section class="creation-section">
              <div class="creation-section-heading">
                <div>
                  <h3>Tarefas iniciais</h3>
                  <span>Opcional · {{ tarefasIniciais.length }}</span>
                </div>
                <button
                  type="button"
                  class="secondary-button add-initial-task"
                  aria-label="Adicionar tarefa inicial"
                  :disabled="tarefasIniciais.length >= 100"
                  @click="adicionarTarefaInicial"
                >
                  <ActionIcon name="add" />
                  {{ tarefasIniciais.length >= 100 ? 'Limite de 100 tarefas' : '+ Adicionar tarefa' }}
                </button>
              </div>
              <div
                v-for="(tarefa, index) in tarefasIniciais"
                :key="index"
                class="initial-task-fields"
              >
                <div class="form-field">
                  <label :for="`initial-task-title-${index}`">Título da tarefa</label>
                  <input
                    :id="`initial-task-title-${index}`"
                    v-model="tarefa.title"
                    type="text"
                    maxlength="255"
                    placeholder="Ex.: Definir objetivos"
                    required
                  />
                </div>
                <div class="form-field">
                  <label :for="`initial-task-description-${index}`">Descrição</label>
                  <input
                    :id="`initial-task-description-${index}`"
                    v-model="tarefa.description"
                    type="text"
                    maxlength="5000"
                    placeholder="Detalhes (opcional)"
                  />
                </div>
                <button
                  type="button"
                  class="remove-initial-task action-tooltip"
                  :aria-label="`Remover tarefa ${index + 1}`"
                  @click="removerTarefaInicial(index)"
                >
                  <ActionIcon name="delete" /> Remover
                </button>
              </div>
            </section>
          </template>

          <p v-if="erro && mostrarFormulario" class="form-error">
            {{ erro }}
          </p>

          <div class="form-actions">
            <button
              type="button"
              class="secondary-button action-tooltip"
              aria-label="Cancelar"
              :disabled="aGuardar || aCarregarOpcoesCriacao"
              @click="fecharFormulario"
            >
              <ActionIcon name="close" />
              Cancelar
            </button>

            <button
              type="submit"
              class="primary-button"
              :aria-label="aGuardar ? 'A guardar' : modoEdicao ? 'Guardar alterações' : 'Criar projeto'"
              :disabled="aGuardar || aCarregarOpcoesCriacao || (!modoEdicao && !opcoesCriacaoCarregadas)"
            >
              <ActionIcon :name="modoEdicao ? 'save' : 'add'" />
              {{ aGuardar
                ? 'A guardar...'
                : modoEdicao
                  ? 'Guardar alterações'
                  : 'Criar projeto'
              }}
            </button>
          </div>
        </form>
      </section>
    </Transition>

    <!-- LISTAGEM DE PROJETOS -->
    <section class="projects-section">
      <div class="section-heading">
        <div>
          <span class="eyebrow">ESPAÇO DE TRABALHO</span>
          <h2 id="projects-table-title">Os teus projetos</h2>
          <p>Pesquisa e ordena a lista para encontrares rapidamente um projeto.</p>
        </div>

        <span class="results-count">
          {{ projetosFiltrados.length }}
          {{ projetosFiltrados.length === 1 ? 'projeto' : 'projetos' }}
        </span>
      </div>

      <div class="toolbar">
        <div class="search-box">
          <span>⌕</span>
          <input
            v-model="pesquisa"
            type="search"
            placeholder="Pesquisar projetos..."
            aria-label="Pesquisar projetos por nome ou descrição"
          />
        </div>

        <div class="filter-control">
          <label for="project-filter">Estado:</label>
          <select id="project-filter" v-model="filtroEstado">
            <option value="Todos">Todos</option>
            <option value="Ativo">Ativos</option>
            <option value="Concluído">Concluídos</option>
            <option value="Arquivado">Arquivados</option>
          </select>
        </div>
      </div>

      <div v-if="carregando" class="empty-state">
        <span class="spinner" />
        <p>A carregar projetos...</p>
      </div>

      <div v-else-if="erro && projetos.length === 0" class="empty-state">
        <h3>Não foi possível carregar os projetos</h3>
        <p>Verifica a ligação ao servidor.</p>
        <button class="secondary-button action-tooltip" aria-label="Tentar novamente" @click="carregarProjetos">
          <ActionIcon name="refresh" />
          Tentar novamente
        </button>
      </div>

      <div v-else-if="projetos.length === 0" class="empty-state">
        <div class="empty-icon">▦</div>
        <h3>Ainda não existem projetos</h3>
        <p>Começa por criar o teu primeiro projeto.</p>
        <button class="primary-button" aria-label="Criar projeto" @click="abrirCriacao">
          <ActionIcon name="add" />
          Criar projeto
        </button>
      </div>

      <div v-else-if="projetosFiltrados.length === 0" class="empty-state">
        <h3>Nenhum projeto encontrado</h3>
        <p>Altera a pesquisa ou os filtros selecionados.</p>
        <button
          class="secondary-button action-tooltip"
          aria-label="Limpar filtros"
          @click="pesquisa = ''; filtroEstado = 'Todos'"
        >
          <ActionIcon name="close" />
          Limpar filtros
        </button>
      </div>

      <div v-else class="projects-table-scroll">
        <table class="projects-table" aria-labelledby="projects-table-title">
          <thead>
            <tr>
              <th
                v-for="coluna in colunasTabelaProjetos"
                :key="coluna.chave"
                :aria-sort="
                  ordenacaoProjetos.chave === coluna.chave
                    ? ordenacaoProjetos.ascendente ? 'ascending' : 'descending'
                    : 'none'
                "
              >
                <button
                  type="button"
                  @click="ordenarProjetos(coluna.chave)"
                >
                  {{ coluna.rotulo }}
                  <span aria-hidden="true">
                    {{ ordenacaoProjetos.chave === coluna.chave
                      ? ordenacaoProjetos.ascendente ? '↑' : '↓'
                      : '↕'
                    }}
                  </span>
                </button>
              </th>
              <th scope="col">Ações</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="projeto in projetosDaPagina" :key="projeto.id">
              <td class="project-id-cell">#{{ projeto.id }}</td>
              <td class="project-name-cell">
                <strong>{{ projeto.name }}</strong>
                <small>{{ projeto.description || 'Sem descrição' }}</small>
              </td>
              <td>
                <span class="status-badge" :class="classeEstado(projeto.status)">
                  <span class="status-dot" />
                  {{ projeto.status }}
                </span>
                <small
                  v-if="aAtualizarEstado === projeto.id"
                  class="updating-label"
                >
                  A atualizar...
                </small>
              </td>
              <td>{{ nomePapelProjeto(projeto.currentUserRole) }}</td>
              <td>{{ formatarData(projeto.createdAt) }}</td>
              <td class="project-actions-cell">
                <div class="project-row-actions">
                  <button
                    v-if="podeGerirProjeto(projeto)"
                    class="action-button action-tooltip"
                    aria-label="Editar projeto"
                    type="button"
                    @click="abrirEdicao(projeto)"
                  >
                    <ActionIcon name="edit" />
                    Editar
                  </button>

                  <NuxtLink
                    :to="`/tasks?project=${projeto.id}`"
                    class="action-button action-tooltip"
                    :aria-label="podeCriarTarefas(projeto) ? 'Tarefas' : 'Ver tarefas'"
                  >
                    <ActionIcon name="tasks" />
                    {{ podeCriarTarefas(projeto) ? 'Tarefas' : 'Ver tarefas' }}
                  </NuxtLink>

                  <button
                    class="action-button members-action action-tooltip"
                    aria-label="Membros"
                    type="button"
                    @click="abrirMembros(projeto)"
                  >
                    <ActionIcon name="team" />
                    Membros
                  </button>

                  <button
                    v-if="podeGerirProjeto(projeto) && projeto.status === 'Ativo'"
                    type="button"
                    class="state-button complete-action action-tooltip"
                    aria-label="Concluir projeto"
                    :disabled="aAtualizarEstado === projeto.id"
                    @click="atualizarEstado(projeto, 'Concluído')"
                  >
                    <ActionIcon name="check" />
                    Concluir
                  </button>

                  <button
                    v-if="podeGerirProjeto(projeto) && (projeto.status === 'Ativo' || projeto.status === 'Concluído')"
                    type="button"
                    class="state-button archive-action action-tooltip"
                    aria-label="Arquivar projeto"
                    :disabled="aAtualizarEstado === projeto.id"
                    @click="pedirConfirmacao(projeto, 'archive')"
                  >
                    <ActionIcon name="archive" />
                    Arquivar
                  </button>

                  <button
                    v-if="podeGerirProjeto(projeto) && projeto.status !== 'Ativo'"
                    type="button"
                    class="state-button reactivate-action action-tooltip"
                    aria-label="Reativar projeto"
                    :disabled="aAtualizarEstado === projeto.id"
                    @click="atualizarEstado(projeto, 'Ativo')"
                  >
                    <ActionIcon name="undo" />
                    Reativar
                  </button>

                  <button
                    v-if="auth.user.value?.role === 'admin'"
                    type="button"
                    class="delete-action action-tooltip"
                    :disabled="aEliminar"
                    :aria-label="`Eliminar projeto ${projeto.name}`"
                    @click="pedirConfirmacao(projeto, 'delete')"
                  >
                    <ActionIcon name="delete" /> Eliminar
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>

        <footer class="projects-pagination">
          <div class="projects-page-size">
            <label for="projects-page-size">Projetos por página</label>
            <select id="projects-page-size" v-model.number="tamanhoPaginaProjetos">
              <option :value="10">10</option>
              <option :value="25">25</option>
              <option :value="50">50</option>
            </select>
            <span>{{ inicioProjetos }}–{{ fimProjetos }} de {{ projetosOrdenados.length }}</span>
          </div>
          <div class="projects-page-controls" aria-label="Paginação dos projetos">
            <button
              type="button"
              class="action-tooltip"
              aria-label="Página anterior"
              :disabled="paginaProjetos <= 1"
              @click="paginaProjetos--"
            >
              <ActionIcon name="back" />
              Anterior
            </button>
            <span>Página {{ paginaProjetos }} de {{ totalPaginasProjetos }}</span>
            <button
              type="button"
              class="action-tooltip"
              aria-label="Página seguinte"
              :disabled="paginaProjetos >= totalPaginasProjetos"
              @click="paginaProjetos++"
            >
              <ActionIcon name="forward" />
              Seguinte
            </button>
          </div>
        </footer>
      </div>
    </section>

    <section
      v-if="mostrarPainelMembros && projetoMembros"
      ref="painelMembrosRef"
      class="inline-members-panel"
    >
          <section
            class="member-management-panel"
            aria-labelledby="members-title"
          >
            <div class="members-heading">
              <div>
                <span class="eyebrow">GESTÃO DO PROJETO</span>
                <h2 id="members-title">Membros do projeto</h2>
                <p>{{ projetoMembros.name }}</p>
              </div>

              <button
                class="close-button"
                type="button"
                @click="fecharMembros"
                :disabled="carregandoMembros || aAdicionarMembro || aAdicionarMembroEquipa || membroEmAtualizacao !== null || membroEmRemocao !== null"
                aria-label="Fechar"
              >
                ×
              </button>
            </div>

            <div class="member-summary">
              <div>
                <strong>{{ membros.length }}</strong>
                <span>{{ membros.length === 1 ? 'Membro associado' : 'Membros associados' }}</span>
              </div>

              <div>
                <strong>{{ totalOwners }}</strong>
                <span>{{ totalOwners === 1 ? 'Responsável' : 'Responsáveis' }}</span>
              </div>
            </div>

            <div v-if="erroMembros" class="feedback error-feedback">
              <span>!</span>
              {{ erroMembros }}
              <button @click="erroMembros = ''">×</button>
            </div>

            <div v-if="sucessoMembros" class="feedback success-feedback">
              <span>✓</span>
              {{ sucessoMembros }}
              <button @click="sucessoMembros = ''">×</button>
            </div>

            <!-- LISTA DE MEMBROS -->
            <div class="members-list-section">
              <div class="members-section-title">
                <h3>Equipa do projeto</h3>
                <button
                  type="button"
                  class="refresh-button"
                  :disabled="carregandoMembros"
                  @click="carregarMembros"
                >
                  ↻ Atualizar
                </button>
              </div>

              <div v-if="carregandoMembros" class="members-loading">
                <span class="spinner" />
                <p>A carregar membros...</p>
              </div>

              <div
                v-else-if="membros.length === 0"
                class="members-empty"
              >
                <span>♙</span>
                <strong>Sem membros associados</strong>
                <p>Adiciona utilizadores para formar a equipa deste projeto.</p>
              </div>

              <div v-else class="members-list">
                <article
                  v-for="membro in membros"
                  :key="membro.user_id"
                  class="member-row"
                >
                  <div class="member-avatar">
                    <img
                      v-if="membro.avatar_url"
                      :src="construirUrlAvatar(membro.avatar_url)"
                      :alt="`Fotografia de ${membro.name}`"
                      @error="($event.target as HTMLImageElement).style.display = 'none'"
                    />

                    <span v-else>
                      {{ membro.name.charAt(0).toUpperCase() }}
                    </span>
                  </div>

                  <div class="member-information">
                    <strong>{{ membro.name }}</strong>
                    <span>{{ membro.email }}</span>
                    <small class="project-role-label">
                      {{ nomePapelProjeto(membro.role) }}
                    </small>
                    <small v-if="!membro.is_active" class="inactive-label">
                      Conta inativa
                    </small>
                  </div>

                  <div class="member-controls">
                    <select
                      v-if="projetoMembros && podeGerirProjeto(projetoMembros)"
                      :value="membro.role"
                      :disabled="membroEmAtualizacao === membro.user_id || membroEmRemocao === membro.user_id || !membro.is_active"
                      :aria-label="`Responsabilidade de ${membro.name}`"
                      @change="alterarResponsabilidade(membro, ($event.target as HTMLSelectElement).value as 'owner' | 'contributor' | 'viewer')"
                    >
                      <option value="owner">Responsável</option>
                      <option value="contributor">Colaborador</option>
                      <option value="viewer">Observador</option>
                    </select>

                    <button
                      v-if="projetoMembros && podeGerirProjeto(projetoMembros) && membroPendenteRemocao !== membro.user_id"
                      type="button"
                      class="remove-member-button action-tooltip"
                      :disabled="membroEmRemocao === membro.user_id || membroEmAtualizacao === membro.user_id"
                      title="Remover membro"
                      :aria-label="`Remover ${membro.name}`"
                      @click="removerMembro(membro)"
                    >
                      <ActionIcon name="delete" /> Remover
                    </button>
                  </div>
                  <div v-if="membroPendenteRemocao === membro.user_id" class="inline-member-confirm">
                    <span>Remover {{ membro.name }} deste projeto?</span>
                    <button type="button" class="secondary-button action-tooltip" aria-label="Cancelar" @click="membroPendenteRemocao = null">
                      <ActionIcon name="close" /> Cancelar
                    </button>
                    <button type="button" class="danger-button action-tooltip" aria-label="Confirmar remoção" @click="removerMembro(membro)">
                      <ActionIcon name="delete" /> Confirmar
                    </button>
                  </div>
                </article>
              </div>
            </div>

            <!-- ADICIONAR MEMBRO -->
            <div
              v-if="projetoMembros && podeGerirProjeto(projetoMembros)"
              class="add-member-section"
            >
              <div class="members-section-title">
                <h3>Adicionar utilizador</h3>
              </div>

              <div v-if="carregandoUtilizadoresDisponiveis" class="members-loading">
                <span class="spinner" />
                <p>A carregar contas existentes...</p>
              </div>

              <div
                v-else-if="utilizadoresDisponiveis.length === 0"
                class="members-empty compact-empty"
              >
                <p>Não há outras contas ativas disponíveis para este projeto.</p>
                <small>
                  Contas novas têm de ser criadas primeiro por um administrador.
                </small>
              </div>

              <form
                v-else
                class="add-member-form"
                @submit.prevent="adicionarMembro"
              >
                <div class="form-field">
                  <label for="member-user">Conta existente</label>
                  <select
                    id="member-user"
                    v-model="novoMembro.user_id"
                    required
                  >
                    <option value="" disabled>Seleciona um utilizador</option>
                    <option
                      v-for="utilizador in utilizadoresDisponiveis"
                      :key="utilizador.id"
                      :value="String(utilizador.id)"
                    >
                      {{ utilizador.name }} — {{ utilizador.email }}
                    </option>
                  </select>
                </div>

                <div class="form-field">
                  <label for="member-role">Responsabilidade</label>
                  <select
                    id="member-role"
                    v-model="novoMembro.role"
                  >
                    <option value="contributor">Colaborador</option>
                    <option value="viewer">Observador</option>
                    <option value="owner">Responsável</option>
                  </select>
                </div>

                <button
                  type="submit"
                  class="primary-button add-member-submit"
                  aria-label="Adicionar membro"
                  :disabled="aAdicionarMembro || !novoMembro.user_id"
                >
                  <ActionIcon name="add" />
                  {{ aAdicionarMembro ? 'A adicionar...' : 'Adicionar membro' }}
                </button>
              </form>
            </div>

            <section v-if="equipaProjeto" class="add-member-section">
              <div class="members-section-title">
                <h3>Membros da equipa · {{ equipaProjeto.name }}</h3>
              </div>

              <div v-if="carregandoMembros" class="members-loading">
                <span class="spinner" />
                <p>A carregar membros da equipa...</p>
              </div>

              <div v-else-if="membrosEquipa.length" class="members-list">
                <article
                  v-for="membro in membrosEquipa"
                  :key="membro.user_id"
                  class="member-row"
                >
                  <div class="member-avatar">
                    <img
                      v-if="membro.avatar_url"
                      :src="construirUrlAvatar(membro.avatar_url)"
                      :alt="`Fotografia de ${membro.name}`"
                      @error="($event.target as HTMLImageElement).style.display = 'none'"
                    />
                    <span v-else>{{ membro.name.charAt(0).toUpperCase() }}</span>
                  </div>
                  <div class="member-information">
                    <strong>{{ membro.name }}</strong>
                    <span>{{ membro.email }}</span>
                  </div>
                </article>
              </div>

              <div v-else class="members-empty compact-empty">
                <p>A equipa ainda não tem membros.</p>
              </div>

              <form
                v-if="equipaProjeto.can_manage"
                class="add-member-form team-member-form"
                @submit.prevent="adicionarMembroEquipa"
              >
                <div class="form-field">
                  <label for="team-member-user">Adicionar à equipa</label>
                  <select
                    id="team-member-user"
                    v-model="novoMembroEquipa"
                    :disabled="carregandoUtilizadoresDisponiveis || aAdicionarMembroEquipa"
                    required
                  >
                    <option value="" disabled>Seleciona um utilizador</option>
                    <option
                      v-for="utilizador in utilizadoresDisponiveisEquipa"
                      :key="utilizador.user_id"
                      :value="String(utilizador.user_id)"
                    >
                      {{ utilizador.name }} — {{ utilizador.email }}
                    </option>
                  </select>
                </div>

                <button
                  type="submit"
                  class="primary-button add-member-submit"
                  aria-label="Adicionar à equipa"
                  :disabled="aAdicionarMembroEquipa || !novoMembroEquipa"
                >
                  <ActionIcon name="add" />
                  {{ aAdicionarMembroEquipa ? 'A adicionar...' : 'Adicionar à equipa' }}
                </button>
                <p
                  v-if="!carregandoUtilizadoresDisponiveis && !utilizadoresDisponiveisEquipa.length"
                  class="team-members-empty"
                >
                  Não há outras contas ativas disponíveis para esta equipa.
                </p>
              </form>
            </section>
            <div v-else-if="projetoMembros.teamId === null" class="members-empty compact-empty">
              <p>Este projeto ainda não está associado a uma equipa.</p>
            </div>

            <div class="members-footer">
              <button
                class="secondary-button action-tooltip"
                type="button"
                aria-label="Fechar"
                @click="fecharMembros"
                :disabled="carregandoMembros || aAdicionarMembro || aAdicionarMembroEquipa || membroEmAtualizacao !== null || membroEmRemocao !== null"
              >
                <ActionIcon name="close" />
                Fechar
              </button>
            </div>
          </section>
    </section>

    <section
      v-if="mostrarConfirmacao && projetoSelecionado"
      class="inline-project-confirmation"
    >
          <section
            class="project-confirm-card"
            aria-labelledby="confirmation-title"
          >
            <div class="confirmation-icon">
              {{ acaoConfirmada === 'delete' ? '!' : '▤' }}
            </div>

            <h2 id="confirmation-title">
              {{ acaoConfirmada === 'delete'
                ? 'Eliminar projeto?'
                : 'Arquivar projeto?'
              }}
            </h2>

            <p>
              Tens a certeza de que pretendes
              {{ acaoConfirmada === 'delete' ? 'eliminar' : 'arquivar' }}
              o projeto
              <strong>{{ projetoSelecionado.name }}</strong>?
            </p>

            <p v-if="acaoConfirmada === 'delete'" class="confirmation-warning">
              Esta operação não pode ser desfeita. Se existirem tarefas
              ou membros associados, o servidor poderá impedir a eliminação.
            </p>

            <p v-else class="confirmation-warning">
              O projeto deixará de estar ativo, mas poderá ser reativado posteriormente.
            </p>

            <div class="confirmation-actions">
              <button
                class="secondary-button action-tooltip"
                type="button"
                aria-label="Cancelar"
                :disabled="aEliminar"
                @click="fecharConfirmacao"
              >
                <ActionIcon name="close" />
                Cancelar
              </button>

              <button
                v-if="acaoConfirmada === 'delete'"
                class="danger-button action-tooltip"
                type="button"
                :aria-label="aEliminar ? 'A eliminar' : 'Eliminar projeto'"
                :disabled="aEliminar"
                @click="executarAcao"
              >
                <ActionIcon :name="acaoConfirmada === 'delete' ? 'delete' : 'archive'" />
                {{ aEliminar ? 'A eliminar...' : 'Eliminar projeto' }}
              </button>

              <button
                v-else
                class="primary-button action-tooltip"
                type="button"
                aria-label="Arquivar projeto"
                @click="executarAcao"
              >
                <ActionIcon name="archive" />
                Arquivar projeto
              </button>
            </div>
          </section>
    </section>

  </main>
</template>

<style scoped>
.projects-page {
  width: 100%;
  max-width: 1600px;
  margin: 0 auto;
  padding: 12px 0 32px;
  box-sizing: border-box;
  color: #17233c;
}

.page-heading {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 25px 28px;
  margin-bottom: 20px;
  border: 1px solid #e1e7f4;
  border-radius: 20px;
  background:
    radial-gradient(circle at 92% 10%, rgb(199 210 254 / 55%), transparent 25%),
    linear-gradient(120deg, #fff 0%, #f8faff 65%, #f0f3ff 100%);
  box-shadow: 0 8px 24px rgb(23 37 84 / 4%);
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 9px;
  margin-bottom: 12px;
  color: #94a3b8;
  font-size: 11px;
  font-weight: 600;
}

.breadcrumb a {
  color: #596a8a;
  text-decoration: none;
}

.breadcrumb a:hover {
  color: #4f46e5;
}

.page-heading h1 {
  margin: 0 0 6px;
  color: #1c2b4a;
  font-size: clamp(24px, 2.4vw, 31px);
  font-weight: 800;
  letter-spacing: -1px;
}

.page-heading p,
.section-heading p {
  margin: 0;
  color: #7d8aa1;
  font-size: 14px;
  line-height: 1.6;
}

.primary-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 9px;
  min-height: 44px;
  padding: 0 18px;
  border: 1px solid var(--tf-primary-hover);
  border-radius: 11px;
  background: linear-gradient(135deg, var(--tf-primary), var(--tf-primary-hover));
  color: white;
  font-size: 13px;
  font-weight: 650;
  cursor: pointer;
  box-shadow: 0 7px 16px -8px rgb(69 79 201 / 62%);
  transition: transform .2s ease, box-shadow .2s ease, background .2s ease;
}

.primary-button:hover {
  background: linear-gradient(135deg, var(--tf-primary-hover), #3730a3);
  transform: translateY(-1px);
  box-shadow: 0 10px 20px -8px rgb(67 56 202 / 62%);
}

.primary-button:active {
  transform: translateY(0);
}

.primary-button:focus-visible,
.secondary-button:focus-visible,
.action-button:focus-visible,
.state-button:focus-visible,
.delete-action:focus-visible {
  outline: 3px solid #c7d2fe;
  outline-offset: 2px;
}

.form-actions .primary-button {
  min-width: 160px;
}

.primary-button:disabled,
.state-button:disabled,
.delete-action:disabled {
  opacity: .55;
  cursor: not-allowed;
  transform: none;
}

.feedback {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 13px 15px;
  margin-bottom: 18px;
  border-radius: 9px;
  font-size: 13px;
}

.success-feedback {
  background: #eaf8f0;
  color: #167348;
}

.error-feedback {
  background: #fff0f0;
  color: #b42318;
}

.feedback button {
  margin-left: auto;
  border: 0;
  background: transparent;
  color: inherit;
  font-size: 21px;
  cursor: pointer;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 20px;
}

.stat-card {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  gap: 15px;
  min-height: 104px;
  padding: 18px;
  box-sizing: border-box;
  background: white;
  border: 1px solid #e7ebf3;
  border-radius: 17px;
  box-shadow: 0 5px 16px rgb(23 37 84 / 3%);
  transition: transform .2s ease, box-shadow .2s ease, border-color .2s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  border-color: #d9e0ef;
  box-shadow: 0 12px 22px -15px rgb(23 37 84 / 38%);
}

.stat-card > div:last-child {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.stat-card span {
  color: #6f7d95;
  font-size: 12px;
  font-weight: 600;
}

.stat-card strong {
  color: #1e2b50;
  font-size: 29px;
  font-weight: 800;
  line-height: 1.05;
  font-variant-numeric: tabular-nums;
}

.stat-card small {
  color: #96a0b1;
  font-size: 10px;
}

.stat-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  flex: 0 0 44px;
  border-radius: 13px;
  font-size: 20px;
  font-weight: 700;
}

.total-icon { background: #edf0ff; color: #4b55bd; }
.active-icon { background: #e8f7f0; color: #15966a; }
.completed-icon { background: #eaf2ff; color: #3575d5; }
.archived-icon { background: #f0f1f5; color: #68758b; }

.form-card,
.projects-section {
  padding: 22px;
  margin-bottom: 20px;
  background: white;
  border: 1px solid #e7ebf3;
  border-radius: 18px;
  box-shadow: 0 5px 18px rgb(23 37 84 / 3%);
}

.form-card,
.inline-members-panel {
  scroll-margin-top: 96px;
}

.form-heading,
.section-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 22px;
}

.eyebrow {
  display: block;
  margin-bottom: 7px;
  color: #5363bd;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 1.2px;
}

.form-heading h2,
.section-heading h2 {
  margin: 0 0 7px;
  color: #243452;
  font-size: 18px;
  font-weight: 750;
}

.form-heading p {
  margin: 0;
  color: #8792a5;
  font-size: 12px;
}

.close-button {
  width: 33px;
  height: 33px;
  flex: 0 0 33px;
  border: 0;
  border-radius: 8px;
  background: #f3f5f9;
  color: #68758b;
  font-size: 22px;
  cursor: pointer;
}

.close-button:disabled {
  opacity: .5;
  cursor: not-allowed;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 17px;
}

.form-field label {
  color: #344158;
  font-size: 13px;
  font-weight: 650;
}

.form-field label span {
  color: #dc4545;
}

.form-field input,
.form-field textarea,
.form-field select {
  width: 100%;
  box-sizing: border-box;
  padding: 12px 14px;
  border: 1px solid #dfe4ed;
  border-radius: 8px;
  outline: none;
  background: white;
  color: #26344c;
  font: inherit;
  font-size: 13px;
}

.form-field input:focus,
.form-field textarea:focus,
.form-field select:focus {
  border-color: #6978d2;
  box-shadow: 0 0 0 3px rgba(83, 99, 189, .1);
}

.form-field textarea {
  resize: vertical;
}

.creation-options-loading,
.creation-section {
  margin-top: 20px;
  padding-top: 18px;
  border-top: 1px solid #edf0f5;
}

.creation-options-loading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: #78859a;
  font-size: 12px;
}

.creation-options-loading p {
  margin: 0;
}

.creation-section-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.creation-section-heading h3 {
  margin: 0;
  color: #344158;
  font-size: 13px;
}

.creation-section-heading span,
.creation-empty-note,
.form-field small,
.creation-section-heading > small {
  color: #8792a5;
  font-size: 11px;
}

.creation-section .form-field {
  margin-bottom: 0;
}

.creation-member-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  max-height: 220px;
  overflow-y: auto;
}

.creation-member-option {
  display: flex;
  align-items: center;
  gap: 9px;
  min-width: 0;
  padding: 9px;
  border: 1px solid #edf0f5;
  border-radius: 9px;
  cursor: pointer;
}

.creation-member-option input {
  flex: 0 0 auto;
  accent-color: #5363bd;
}

.creation-member-option .member-avatar {
  width: 34px;
  height: 34px;
  flex-basis: 34px;
}

.creation-member-copy {
  display: flex;
  flex-direction: column;
  min-width: 0;
  gap: 3px;
}

.creation-member-copy strong,
.creation-member-copy small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.creation-member-copy strong {
  color: #344158;
  font-size: 11px;
}

.creation-member-copy small {
  color: #8792a5;
  font-size: 10px;
}

.creation-empty-note {
  margin: 0;
}

.add-initial-task {
  min-height: 34px;
}

.initial-task-fields {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) 34px;
  align-items: end;
  gap: 10px;
  padding: 12px;
  margin-top: 9px;
  border: 1px solid #edf0f5;
  border-radius: 9px;
  background: #fafbfe;
}

.initial-task-fields .form-field {
  min-width: 0;
}

.remove-initial-task {
  min-height: 40px;
  padding: 0 10px;
  border: 1px solid #f1dada;
  border-radius: 7px;
  background: white;
  color: #c04444;
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
}

.form-error {
  color: #bd3030;
  font-size: 12px;
}

.form-actions,
.confirmation-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
  padding-top: 17px;
  border-top: 1px solid #edf0f5;
}

.secondary-button {
  min-height: 40px;
  padding: 0 15px;
  border: 1px solid #e1e6ee;
  border-radius: 8px;
  background: white;
  color: #657187;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: background .18s ease, border-color .18s ease, box-shadow .18s ease;
}

.secondary-button:hover {
  border-color: #cbd5e1;
  background: #f7f8fb;
  box-shadow: 0 3px 8px rgb(15 23 42 / 6%);
}

.secondary-button:disabled {
  opacity: .5;
  cursor: not-allowed;
}

.results-count {
  padding: 8px 12px;
  border: 1px solid #e1e7ff;
  border-radius: 999px;
  background: #f3f4ff;
  color: #5146c8;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 13px;
  margin-bottom: 18px;
  border: 1px solid #edf0f5;
  border-radius: 13px;
  background: #f8faff;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 10px;
  width: min(100%, 440px);
  height: 42px;
  padding: 0 12px;
  border: 1px solid #e1e6ef;
  border-radius: 10px;
  background: #fff;
  transition: border-color .2s ease, box-shadow .2s ease;
}

.search-box:focus-within {
  border-color: #9698ed;
  box-shadow: 0 0 0 3px rgb(99 102 241 / 9%);
}

.search-box span {
  color: #8d99ad;
  font-size: 22px;
}

.search-box input {
  width: 100%;
  border: 0;
  outline: none;
  color: #344158;
  font: inherit;
  font-size: 12px;
}

.filter-control {
  display: flex;
  align-items: center;
  gap: 9px;
  color: #78859a;
  font-size: 12px;
}

.filter-control select {
  padding: 10px 12px;
  border: 1px solid #e1e6ef;
  border-radius: 10px;
  background: white;
  color: #344158;
  cursor: pointer;
}

.projects-table-scroll {
  width: 100%;
  max-height: 600px;
  overflow: auto;
  border: 1px solid #e8edf4;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 2px 6px rgb(23 37 84 / 2%);
  scrollbar-color: #cbd5e1 transparent;
  scrollbar-width: thin;
}

.projects-table {
  width: 100%;
  min-width: 1080px;
  border-collapse: collapse;
  text-align: left;
}

.projects-table th,
.projects-table td {
  padding: 13px 15px;
  border-bottom: 1px solid #eff2f7;
  color: #475569;
  font-size: 12px;
  vertical-align: middle;
}

.projects-table th {
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

.projects-table th button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0;
  border: 0;
  background: transparent;
  color: inherit;
  font: inherit;
  cursor: pointer;
}

.projects-table th button:focus-visible,
.project-row-actions button:focus-visible,
.project-row-actions a:focus-visible,
.projects-page-controls button:focus-visible {
  outline: 3px solid #c7d2fe;
  outline-offset: 2px;
}

.projects-table th button:hover,
.projects-table th[aria-sort="ascending"] button,
.projects-table th[aria-sort="descending"] button {
  color: #4f46e5;
}

.projects-table th button span {
  color: #9ba6b7;
  font-size: 12px;
}

.projects-table tbody tr:last-child td {
  border-bottom: 0;
}

.projects-table tbody tr:hover {
  background: #f8faff;
}

.projects-table .project-name-cell {
  min-width: 240px;
}

.project-name-cell strong,
.project-name-cell small {
  display: block;
}

.projects-table .project-id-cell {
  color: #8995a8;
  font-variant-numeric: tabular-nums;
  font-size: 11px;
  font-weight: 650;
  white-space: nowrap;
}

.project-name-cell strong {
  margin-bottom: 4px;
  color: #26344c;
  font-size: 13px;
  overflow-wrap: anywhere;
}

.project-name-cell small {
  display: -webkit-box;
  overflow: hidden;
  max-width: 360px;
  margin-bottom: 5px;
  color: #8792a5;
  line-height: 1.45;
  overflow-wrap: anywhere;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 9px;
  border-radius: 20px;
  font-size: 10px;
  font-weight: 700;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.status-badge.active { background: #e8f7ef; color: #168653; }
.status-badge.completed { background: #eaf1ff; color: #376bc0; }
.status-badge.archived { background: #eff1f5; color: #69768a; }

.action-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  min-height: 32px;
  padding: 0 9px;
  border: 1px solid #e3e7f0;
  border-radius: 7px;
  background: white;
  color: #5363a5;
  text-decoration: none;
  font-size: 10px;
  font-weight: 650;
  cursor: pointer;
  transition: transform .18s ease, background .18s ease, border-color .18s ease, box-shadow .18s ease;
}

.action-button:hover {
  transform: translateY(-1px);
  border-color: #cfd5f3;
  background: #f4f5ff;
  box-shadow: 0 4px 10px rgb(35 49 91 / 7%);
}

.members-action {
  background: #f5f6ff;
  color: #4858ad;
  border-color: #e1e5ff;
}

.project-actions-cell {
  min-width: 430px;
}

.project-row-actions {
  display: flex;
  align-items: center;
  flex-wrap: nowrap;
  gap: 6px;
  padding: 2px;
}

.project-row-actions > button {
  flex: 0 0 auto;
}

.state-button {
  min-height: 29px;
  padding: 0 9px;
  border: 1px solid transparent;
  border-radius: 6px;
  font-size: 10px;
  font-weight: 650;
  cursor: pointer;
  transition: transform .18s ease, border-color .18s ease, box-shadow .18s ease;
}

.state-button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 3px 8px rgb(35 49 91 / 8%);
}

.complete-action { background: #eaf2ff; color: #376bc0; border-color: #d7e4ff; }
.archive-action { background: #f0f1f5; color: #69768a; border-color: #e0e3e9; }
.reactivate-action { background: #e8f7ef; color: #168653; border-color: #ccebd9; }

.delete-action {
  min-height: 29px;
  padding: 0 9px;
  border: 1px solid #f2dada;
  border-radius: 6px;
  background: white;
  color: #c04444;
  font-size: 10px;
  font-weight: 650;
  cursor: pointer;
  transition: background .18s ease, border-color .18s ease, box-shadow .18s ease;
}

.delete-action:hover {
  border-color: #ecc3c3;
  background: #fff0f0;
  box-shadow: 0 3px 8px rgb(192 68 68 / 10%);
}

.updating-label {
  display: block;
  margin-top: 5px;
  color: #71809a;
  font-size: 10px;
}

.projects-pagination,
.projects-page-size,
.projects-page-controls {
  display: flex;
  align-items: center;
  gap: 10px;
}

.projects-pagination {
  justify-content: space-between;
  gap: 16px;
  padding: 15px 3px 0;
  color: #78859a;
  font-size: 12px;
}

.projects-page-size select {
  min-height: 34px;
  padding: 0 9px;
  border: 1px solid #e1e6ef;
  border-radius: 7px;
  background: #fff;
  color: #475569;
}

.projects-page-controls button {
  min-height: 34px;
  padding: 0 11px;
  border: 1px solid #e1e6ef;
  border-radius: 7px;
  background: #fff;
  color: #475569;
  font-size: 11px;
  cursor: pointer;
}

.projects-page-controls button:disabled {
  opacity: .45;
  cursor: not-allowed;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 230px;
  gap: 10px;
  text-align: center;
}

.empty-state h3 {
  margin: 0;
  color: #344158;
  font-size: 16px;
}

.empty-state p {
  margin: 0 0 10px;
  color: #8a96a9;
  font-size: 12px;
}

.empty-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 50px;
  height: 50px;
  border-radius: 14px;
  background: #f0f2ff;
  color: #5363bd;
  font-size: 24px;
}

.spinner {
  width: 25px;
  height: 25px;
  border: 3px solid #e5e9f5;
  border-top-color: #5363bd;
  border-radius: 50%;
  animation: spin .7s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.inline-members-panel,
.inline-project-confirmation {
  margin-top: 18px;
  padding: 18px;
  background: #fff;
  border: 1px solid #e1e7f4;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgb(23 37 84 / 5%);
}

.project-confirm-card {
  width: 100%;
  max-width: 720px;
}

.confirmation-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  margin-bottom: 17px;
  border-radius: 12px;
  background: #fff0f0;
  color: #c04444;
  font-size: 22px;
  font-weight: 800;
}

.project-confirm-card h2 {
  margin: 0 0 10px;
  color: #1e2a43;
  font-size: 20px;
}

.project-confirm-card p {
  color: #77849a;
  font-size: 13px;
  line-height: 1.7;
}

.project-confirm-card p strong {
  color: #344158;
}

.confirmation-warning {
  padding: 11px;
  border-radius: 8px;
  background: #fff8e8;
  color: #936b24 !important;
  font-size: 11px !important;
}

.confirmation-actions {
  margin-top: 20px;
}

.inline-member-confirm {
  display: flex;
  align-items: center;
  flex-wrap: nowrap;
  gap: 8px;
  width: 100%;
  margin-top: 8px;
  padding: 8px;
  color: #825b22;
  background: #fff8eb;
  border: 1px solid #f3dfb8;
  border-radius: 8px;
  font-size: 10px;
}

.inline-member-confirm > * {
  flex: 0 0 auto;
}

.inline-member-confirm > span {
  min-width: 0;
  flex: 1 1 auto;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.danger-button {
  min-height: 40px;
  padding: 0 15px;
  border: 0;
  border-radius: 8px;
  background: #c53d3d;
  color: white;
  font-size: 12px;
  font-weight: 650;
  cursor: pointer;
}

.danger-button:hover {
  background: #a92e2e;
}

.danger-button:disabled {
  opacity: .6;
  cursor: not-allowed;
}

/* GESTÃO DE MEMBROS */

.member-management-panel {
  width: 100%;
  max-width: none;
  padding: 0;
  border: 0;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
}

.members-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #edf0f5;
}

.members-heading h2 {
  margin: 0 0 7px;
  color: #1e2a43;
  font-size: 21px;
}

.members-heading p {
  margin: 0;
  color: #8792a5;
  font-size: 12px;
}

.member-summary {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin: 19px 0;
}

.member-summary > div {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 13px;
  border: 1px solid #edf0f5;
  border-radius: 9px;
  background: #fafbfe;
}

.member-summary strong {
  color: #3446a2;
  font-size: 21px;
}

.member-summary span {
  color: #8792a5;
  font-size: 11px;
}

.members-list-section,
.add-member-section {
  margin-top: 22px;
}

.members-section-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 13px;
}

.members-section-title h3 {
  margin: 0;
  color: #344158;
  font-size: 14px;
}

.refresh-button {
  padding: 6px 9px;
  border: 1px solid #e3e7f0;
  border-radius: 6px;
  background: white;
  color: #5363a5;
  font-size: 10px;
  cursor: pointer;
}

.refresh-button:disabled {
  opacity: .5;
  cursor: not-allowed;
}

.members-list {
  display: flex;
  flex-direction: column;
  gap: 9px;
}

.member-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border: 1px solid #edf0f5;
  border-radius: 9px;
}

.member-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  width: 39px;
  height: 39px;
  flex: 0 0 39px;
  border-radius: 50%;
  background: #edf0ff;
  color: #4d5cba;
  font-size: 15px;
  font-weight: 750;
}

.member-avatar img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
}

.member-avatar span {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
}

.member-information {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-width: 0;
  gap: 4px;
}

.member-information strong {
  overflow: hidden;
  color: #344158;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.member-information span {
  overflow: hidden;
  color: #8792a5;
  font-size: 10px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.project-role-label {
  color: #4f46e5;
  font-size: 10px;
  font-weight: 700;
}

.inactive-label {
  color: #bd4545;
  font-size: 10px;
}

.member-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.member-controls select {
  min-height: 33px;
  padding: 0 9px;
  border: 1px solid #e1e6ef;
  border-radius: 7px;
  background: white;
  color: #536078;
  font-size: 11px;
}

.member-controls select:disabled {
  opacity: .6;
}

.remove-member-button {
  min-height: 31px;
  padding: 0 9px;
  border: 1px solid #f1dada;
  border-radius: 7px;
  background: white;
  color: #c04444;
  font-size: 10px;
  font-weight: 700;
  cursor: pointer;
}

.remove-member-button:hover {
  background: #fff0f0;
}

.remove-member-button:disabled {
  opacity: .5;
  cursor: not-allowed;
}

.members-loading,
.members-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 9px;
  padding: 25px 15px;
  text-align: center;
}

.members-empty > span {
  color: #9aa5b5;
  font-size: 26px;
}

.members-empty strong {
  color: #526078;
  font-size: 12px;
}

.members-empty p,
.members-loading p {
  margin: 0;
  color: #8792a5;
  font-size: 11px;
  line-height: 1.6;
}

.compact-empty {
  padding: 12px;
  border: 1px dashed #e1e6ef;
  border-radius: 8px;
}

.add-member-section {
  padding-top: 19px;
  border-top: 1px solid #edf0f5;
}

.add-member-form {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 140px auto;
  align-items: end;
  gap: 12px;
}

.add-member-form .form-field {
  margin: 0;
}

.add-member-form .form-field label {
  font-size: 11px;
}

.add-member-form .form-field select {
  min-height: 42px;
  padding: 9px;
  font-size: 11px;
}

.add-member-submit {
  min-height: 42px;
  padding: 0 12px;
  white-space: nowrap;
  font-size: 11px;
}

.team-member-form {
  grid-template-columns: minmax(0, 1fr) auto;
  margin-top: 14px;
}

.team-members-empty {
  grid-column: 1 / -1;
  margin: 0;
  color: #8792a5;
  font-size: 11px;
}

.members-footer {
  display: flex;
  justify-content: flex-end;
  padding-top: 19px;
  margin-top: 20px;
  border-top: 1px solid #edf0f5;
}

.fade-enter-active,
.fade-leave-active,
.form-enter-active,
.form-leave-active {
  transition: opacity .2s, transform .2s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.form-enter-from,
.form-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* RESPONSIVIDADE */

@media (max-width: 1150px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 700px) {
  .projects-page {
    padding: 8px 0 24px;
  }

  .page-heading {
    align-items: stretch;
    flex-direction: column;
    gap: 18px;
    padding: 21px;
    border-radius: 17px;
  }

  .page-heading h1 {
    font-size: 24px;
  }

  .page-heading > .primary-button {
    width: 100%;
  }

  .toolbar {
    align-items: stretch;
    flex-direction: column;
  }

  .search-box {
    width: 100%;
  }

  .filter-control {
    justify-content: space-between;
  }

  .filter-control select {
    flex: 1;
  }

  .projects-pagination {
    align-items: stretch;
    flex-direction: column;
  }

  .projects-page-size,
  .projects-page-controls {
    justify-content: space-between;
  }

  .form-card,
  .projects-section {
    padding: 17px;
  }

  .creation-member-list {
    grid-template-columns: 1fr;
  }

  .initial-task-fields {
    grid-template-columns: minmax(0, 1fr) auto;
  }

  .initial-task-fields .form-field:nth-child(2) {
    grid-column: 1;
  }

  .remove-initial-task {
    grid-column: 2;
    grid-row: 1 / span 2;
  }

  .inline-members-panel {
    padding: 18px;
    max-height: none;
  }

  .add-member-form {
    grid-template-columns: 1fr;
  }

  .add-member-submit {
    width: 100%;
  }

  .member-row {
    flex-wrap: wrap;
  }

  .member-controls {
    width: 100%;
    justify-content: flex-end;
  }

  .member-controls select {
    flex: 1;
  }
}

@media (max-width: 390px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }

  .stat-card {
    min-height: 80px;
  }

  .member-summary {
    grid-template-columns: 1fr 1fr;
  }
}

@media (prefers-reduced-motion: reduce) {
  .primary-button,
  .secondary-button,
  .action-button,
  .state-button,
  .delete-action {
    transition: none;
  }
}
</style>
