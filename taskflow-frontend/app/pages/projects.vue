
<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

definePageMeta({ layout: 'admin' })

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
  avatar_url: string | null
}

type EstadoProjeto = 'Ativo' | 'Concluído' | 'Arquivado'
type FiltroEstado = 'Todos' | EstadoProjeto
type AcaoProjeto = 'archive' | 'delete'

interface Projeto {
  id: number
  name: string
  description: string
  status: EstadoProjeto
  createdAt: string
}

const config = useRuntimeConfig()
const apiBase = String(config.public.apiBase).replace(/\/$/, '')

// Dados dos projetos
const projetos = ref<Projeto[]>([])
const carregando = ref(false)
const aGuardar = ref(false)
const aAtualizarEstado = ref<number | null>(null)
const aEliminar = ref(false)

// Pesquisa e filtros
const pesquisa = ref('')
const filtroEstado = ref<FiltroEstado>('Todos')

// Formulário de projeto
const mostrarFormulario = ref(false)
const modoEdicao = ref(false)
const projetoEmEdicao = ref<number | null>(null)

const formulario = ref({
  name: '',
  description: '',
})

// Confirmações de projeto
const mostrarConfirmacao = ref(false)
const acaoConfirmada = ref<AcaoProjeto | null>(null)
const projetoSelecionado = ref<Projeto | null>(null)

// Mensagens gerais
const erro = ref('')
const sucesso = ref('')

// Temporário: substituir pelo ID do utilizador autenticado.
const utilizadorId = 1

// --------------------------------------------------
// GESTÃO DE MEMBROS
// --------------------------------------------------

const mostrarModalMembros = ref(false)
const projetoMembros = ref<Projeto | null>(null)
const membros = ref<MembroAPI[]>([])
const utilizadores = ref<UtilizadorAPI[]>([])

const carregandoMembros = ref(false)
const carregandoUtilizadores = ref(false)
const aAdicionarMembro = ref(false)
const membroEmAtualizacao = ref<number | null>(null)
const membroEmRemocao = ref<number | null>(null)

const erroMembros = ref('')
const sucessoMembros = ref('')

const novoMembro = ref({
  user_id: '',
  role: 'member' as 'owner' | 'member',
})

const utilizadoresDisponiveis = computed(() => {
  const idsAssociados = new Set(
    membros.value.map(membro => membro.user_id),
  )

  return utilizadores.value.filter(
    utilizador =>
      utilizador.is_active &&
      !idsAssociados.has(utilizador.id),
  )
})

const totalOwners = computed(
  () => membros.value.filter(membro => membro.role === 'owner').length,
)

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
  }
}

function construirUrlAvatar(avatarUrl: string | null): string {
  if (!avatarUrl) return ''

  // Se já for um endereço completo, utiliza-o diretamente.
  if (
    avatarUrl.startsWith('http://') ||
    avatarUrl.startsWith('https://')
  ) {
    return avatarUrl
  }

  // Se for um caminho relativo, associa-o ao endereço da API.
  return `${apiBase}/${avatarUrl.replace(/^\/+/, '')}`
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

// --------------------------------------------------
// CARREGAR PROJETOS
// --------------------------------------------------

async function carregarProjetos() {
  erro.value = ''
  carregando.value = true

  try {
    const resposta = await $fetch<ProjetoAPI[]>(
      `${apiBase}/projects/`,
    )

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

function abrirCriacao() {
  erro.value = ''
  sucesso.value = ''
  modoEdicao.value = false
  projetoEmEdicao.value = null

  formulario.value = {
    name: '',
    description: '',
  }

  mostrarFormulario.value = true
}

function abrirEdicao(projeto: Projeto) {
  erro.value = ''
  sucesso.value = ''
  modoEdicao.value = true
  projetoEmEdicao.value = projeto.id

  formulario.value = {
    name: projeto.name,
    description: projeto.description,
  }

  mostrarFormulario.value = true
}

function fecharFormulario() {
  if (aGuardar.value) return

  mostrarFormulario.value = false
  modoEdicao.value = false
  projetoEmEdicao.value = null
  erro.value = ''

  formulario.value = {
    name: '',
    description: '',
  }
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

  aGuardar.value = true

  try {
    if (modoEdicao.value && projetoEmEdicao.value !== null) {
      const atualizado = await $fetch<ProjetoAPI>(
        `${apiBase}/projects/${projetoEmEdicao.value}`,
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
      const criado = await $fetch<ProjetoAPI>(
        `${apiBase}/projects/`,
        {
          method: 'POST',
          body: {
            name,
            description: description || null,
            created_by: utilizadorId,
          },
        },
      )

      projetos.value.unshift(converterProjeto(criado))

      pesquisa.value = ''
      filtroEstado.value = 'Todos'

      sucesso.value = 'Projeto criado com sucesso. O criador foi associado como responsável.'
    }

    fecharFormulario()
  } catch (error) {
    console.error('Erro ao guardar projeto:', error)
    erro.value = 'Não foi possível guardar o projeto. Verifica os dados e a API.'
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
    const atualizado = await $fetch<ProjetoAPI>(
      `${apiBase}/projects/${projeto.id}`,
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
    await $fetch(
      `${apiBase}/projects/${projeto.id}`,
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
// CARREGAR UTILIZADORES
// --------------------------------------------------

async function carregarUtilizadores() {
  carregandoUtilizadores.value = true

  try {
    utilizadores.value = await $fetch<UtilizadorAPI[]>(
      `${apiBase}/users/`,
    )
  } catch (error) {
    console.error('Erro ao carregar utilizadores:', error)
    erroMembros.value = 'Não foi possível carregar os utilizadores registados.'
  } finally {
    carregandoUtilizadores.value = false
  }
}

// --------------------------------------------------
// ABRIR E FECHAR GESTÃO DE MEMBROS
// --------------------------------------------------

async function abrirMembros(projeto: Projeto) {
  projetoMembros.value = projeto
  mostrarModalMembros.value = true

  membros.value = []
  novoMembro.value = {
    user_id: '',
    role: 'member',
  }

  erroMembros.value = ''
  sucessoMembros.value = ''

  await Promise.all([
    carregarMembros(),
    carregarUtilizadores(),
  ])
}

function fecharMembros() {
  if (
    carregandoMembros.value ||
    aAdicionarMembro.value ||
    membroEmAtualizacao.value !== null ||
    membroEmRemocao.value !== null
  ) {
    return
  }

  mostrarModalMembros.value = false
  projetoMembros.value = null
  membros.value = []
  erroMembros.value = ''
  sucessoMembros.value = ''
}

// --------------------------------------------------
// LISTAR MEMBROS
// --------------------------------------------------

async function carregarMembros() {
  if (!projetoMembros.value) return

  carregandoMembros.value = true
  erroMembros.value = ''

  try {
    membros.value = await $fetch<MembroAPI[]>(
      `${apiBase}/projects/${projetoMembros.value.id}/members`,
    )
  } catch (error) {
    console.error('Erro ao carregar membros:', error)
    erroMembros.value = 'Não foi possível carregar os membros deste projeto.'
  } finally {
    carregandoMembros.value = false
  }
}

// --------------------------------------------------
// ADICIONAR MEMBRO
// --------------------------------------------------

async function adicionarMembro() {
  if (!projetoMembros.value) return

  erroMembros.value = ''
  sucessoMembros.value = ''

  if (!novoMembro.value.user_id) {
    erroMembros.value = 'Seleciona um utilizador para adicionar.'
    return
  }

  aAdicionarMembro.value = true

  try {
    const novo = await $fetch<MembroAPI>(
      `${apiBase}/projects/${projetoMembros.value.id}/members`,
      {
        method: 'POST',
        body: {
          user_id: Number(novoMembro.value.user_id),
          role: novoMembro.value.role,
        },
      },
    )

    membros.value.push(novo)

    novoMembro.value = {
      user_id: '',
      role: 'member',
    }

    sucessoMembros.value = 'Utilizador adicionado ao projeto com sucesso.'
  } catch (error: unknown) {
    console.error('Erro ao adicionar membro:', error)

    const resposta = error as {
      statusCode?: number
      data?: { detail?: string }
    }

    erroMembros.value =
      resposta.data?.detail ||
      'Não foi possível adicionar o utilizador ao projeto.'
  } finally {
    aAdicionarMembro.value = false
  }
}

// --------------------------------------------------
// ALTERAR RESPONSABILIDADE
// --------------------------------------------------

async function alterarResponsabilidade(
  membro: MembroAPI,
  novoRole: 'owner' | 'member',
) {
  if (!projetoMembros.value) return
  if (membro.role === novoRole) return

  erroMembros.value = ''
  sucessoMembros.value = ''
  membroEmAtualizacao.value = membro.user_id

  try {
    const atualizado = await $fetch<MembroAPI>(
      `${apiBase}/projects/${projetoMembros.value.id}/members/${membro.user_id}`,
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

    // Repõe os dados apresentados com o estado atual da API.
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

  const confirmado = window.confirm(
    `Queres remover ${membro.name} deste projeto?`,
  )

  if (!confirmado) return

  erroMembros.value = ''
  sucessoMembros.value = ''
  membroEmRemocao.value = membro.user_id

  try {
    await $fetch(
      `${apiBase}/projects/${projetoMembros.value.id}/members/${membro.user_id}`,
      {
        method: 'DELETE',
      },
    )

    membros.value = membros.value.filter(
      m => m.user_id !== membro.user_id,
    )

    sucessoMembros.value = 'Membro removido do projeto com sucesso.'
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

        <h1>Gestão de projetos</h1>
        <p>Organiza, acompanha e gere todos os teus projetos num único lugar.</p>
      </div>

      <button class="primary-button" @click="abrirCriacao">
        <span>+</span>
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
      <section v-if="mostrarFormulario" class="form-card">
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
            :disabled="aGuardar"
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

          <p v-if="erro && mostrarFormulario" class="form-error">
            {{ erro }}
          </p>

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
              :disabled="aGuardar"
            >
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
          <span class="eyebrow">GESTÃO</span>
          <h2>Os teus projetos</h2>
          <p>Consulta e administra os projetos registados.</p>
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
        <button class="secondary-button" @click="carregarProjetos">
          Tentar novamente
        </button>
      </div>

      <div v-else-if="projetos.length === 0" class="empty-state">
        <div class="empty-icon">▦</div>
        <h3>Ainda não existem projetos</h3>
        <p>Começa por criar o teu primeiro projeto.</p>
        <button class="primary-button" @click="abrirCriacao">
          + Criar projeto
        </button>
      </div>

      <div v-else-if="projetosFiltrados.length === 0" class="empty-state">
        <h3>Nenhum projeto encontrado</h3>
        <p>Altera a pesquisa ou os filtros selecionados.</p>
        <button
          class="secondary-button"
          @click="pesquisa = ''; filtroEstado = 'Todos'"
        >
          Limpar filtros
        </button>
      </div>

      <div v-else class="projects-grid">
        <article
          v-for="projeto in projetosFiltrados"
          :key="projeto.id"
          class="project-card"
        >
          <div class="card-header">
            <div class="project-symbol">▦</div>

            <span
              class="status-badge"
              :class="classeEstado(projeto.status)"
            >
              <span class="status-dot" />
              {{ projeto.status }}
            </span>
          </div>

          <span class="project-reference">
            PROJETO #{{ projeto.id }}
          </span>

          <h3>{{ projeto.name }}</h3>

          <p class="project-description">
            {{ projeto.description || 'Este projeto ainda não tem descrição.' }}
          </p>

          <div class="project-meta">
            <div>
              <small>Criado em</small>
              <strong>{{ formatarData(projeto.createdAt) }}</strong>
            </div>

            <div>
              <small>Estado atual</small>
              <strong>{{ projeto.status }}</strong>
            </div>
          </div>

          <div class="card-actions">
            <button
              class="action-button edit-action"
              type="button"
              @click="abrirEdicao(projeto)"
            >
              <span>✎</span>
              Editar
            </button>

            <NuxtLink
              :to="`/tasks?project=${projeto.id}`"
              class="action-button tasks-action"
            >
              <span>▤</span>
              Tarefas
            </NuxtLink>

            <button
              class="action-button members-action"
              type="button"
              @click="abrirMembros(projeto)"
            >
              <span>♙</span>
              Membros
            </button>
          </div>

          <div class="state-actions">
            <button
              v-if="projeto.status === 'Ativo'"
              type="button"
              class="state-button complete-action"
              :disabled="aAtualizarEstado === projeto.id"
              @click="atualizarEstado(projeto, 'Concluído')"
            >
              ✓ Concluir
            </button>

            <button
              v-if="projeto.status === 'Ativo' || projeto.status === 'Concluído'"
              type="button"
              class="state-button archive-action"
              :disabled="aAtualizarEstado === projeto.id"
              @click="pedirConfirmacao(projeto, 'archive')"
            >
              Arquivar
            </button>

            <button
              v-if="projeto.status !== 'Ativo'"
              type="button"
              class="state-button reactivate-action"
              :disabled="aAtualizarEstado === projeto.id"
              @click="atualizarEstado(projeto, 'Ativo')"
            >
              ↻ Reativar
            </button>

            <button
              type="button"
              class="delete-action"
              :disabled="aEliminar"
              aria-label="Eliminar projeto"
              title="Eliminar projeto"
              @click="pedirConfirmacao(projeto, 'delete')"
            >
              <span>⌫</span>
            </button>
          </div>

          <div
            v-if="aAtualizarEstado === projeto.id"
            class="updating-label"
          >
            A atualizar estado...
          </div>
        </article>
      </div>
    </section>

    <!-- MODAL DE MEMBROS -->
    <Teleport to="body">
      <Transition name="fade">
        <div
          v-if="mostrarModalMembros && projetoMembros"
          class="modal-overlay members-overlay"
          @click.self="fecharMembros"
        >
          <section
            class="members-modal"
            role="dialog"
            aria-modal="true"
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
                :disabled="carregandoMembros || aAdicionarMembro || membroEmAtualizacao !== null || membroEmRemocao !== null"
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
                    <small v-if="!membro.is_active" class="inactive-label">
                      Conta inativa
                    </small>
                  </div>

                  <div class="member-controls">
                    <select
                      :value="membro.role"
                      :disabled="membroEmAtualizacao === membro.user_id || membroEmRemocao === membro.user_id || !membro.is_active"
                      :aria-label="`Responsabilidade de ${membro.name}`"
                      @change="alterarResponsabilidade(membro, ($event.target as HTMLSelectElement).value as 'owner' | 'member')"
                    >
                      <option value="owner">Owner</option>
                      <option value="member">Member</option>
                    </select>

                    <button
                      type="button"
                      class="remove-member-button"
                      :disabled="membroEmRemocao === membro.user_id || membroEmAtualizacao === membro.user_id"
                      title="Remover membro"
                      :aria-label="`Remover ${membro.name}`"
                      @click="removerMembro(membro)"
                    >
                      {{ membroEmRemocao === membro.user_id ? '...' : '×' }}
                    </button>
                  </div>
                </article>
              </div>
            </div>

            <!-- ADICIONAR MEMBRO -->
            <div class="add-member-section">
              <div class="members-section-title">
                <h3>Adicionar utilizador</h3>
              </div>

              <div v-if="carregandoUtilizadores" class="members-loading">
                <span class="spinner" />
                <p>A carregar utilizadores...</p>
              </div>

              <div v-else-if="utilizadoresDisponiveis.length === 0" class="members-empty compact-empty">
                <p>Não existem outros utilizadores ativos disponíveis para adicionar.</p>
              </div>

              <form v-else class="add-member-form" @submit.prevent="adicionarMembro">
                <div class="form-field">
                  <label for="member-user">Utilizador</label>
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
                    <option value="member">Member</option>
                    <option value="owner">Owner</option>
                  </select>
                </div>

                <button
                  type="submit"
                  class="primary-button add-member-submit"
                  :disabled="aAdicionarMembro || !novoMembro.user_id"
                >
                  {{ aAdicionarMembro ? 'A adicionar...' : '+ Adicionar membro' }}
                </button>
              </form>
            </div>

            <div class="members-footer">
              <button
                class="secondary-button"
                type="button"
                @click="fecharMembros"
                :disabled="carregandoMembros || aAdicionarMembro || membroEmAtualizacao !== null || membroEmRemocao !== null"
              >
                Fechar
              </button>
            </div>
          </section>
        </div>
      </Transition>
    </Teleport>

    <!-- MODAL DE CONFIRMAÇÃO DO PROJETO -->
    <Teleport to="body">
      <Transition name="fade">
        <div
          v-if="mostrarConfirmacao && projetoSelecionado"
          class="modal-overlay"
          @click.self="fecharConfirmacao"
        >
          <section
            class="confirmation-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="confirmation-title"
          >
            <div class="modal-icon">
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

            <p v-if="acaoConfirmada === 'delete'" class="modal-warning">
              Esta operação não pode ser desfeita. Se existirem tarefas
              ou membros associados, o servidor poderá impedir a eliminação.
            </p>

            <p v-else class="modal-warning">
              O projeto deixará de estar ativo, mas poderá ser reativado posteriormente.
            </p>

            <div class="modal-actions">
              <button
                class="secondary-button"
                type="button"
                :disabled="aEliminar"
                @click="fecharConfirmacao"
              >
                Cancelar
              </button>

              <button
                v-if="acaoConfirmada === 'delete'"
                class="danger-button"
                type="button"
                :disabled="aEliminar"
                @click="executarAcao"
              >
                {{ aEliminar ? 'A eliminar...' : 'Eliminar projeto' }}
              </button>

              <button
                v-else
                class="primary-button"
                type="button"
                @click="executarAcao"
              >
                Arquivar projeto
              </button>
            </div>
          </section>
        </div>
      </Transition>
    </Teleport>

  </main>
</template>

<style scoped>
.projects-page {
  width: 100%;
  max-width: 1500px;
  margin: 0 auto;
  padding: 32px;
  box-sizing: border-box;
  color: #17233c;
}

.page-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 30px;
}

.breadcrumb {
  display: flex;
  gap: 9px;
  margin-bottom: 15px;
  color: #94a3b8;
  font-size: 12px;
}

.breadcrumb a {
  color: #64748b;
  text-decoration: none;
}

.page-heading h1 {
  margin: 0 0 8px;
  font-size: 29px;
  font-weight: 750;
  letter-spacing: -0.8px;
}

.page-heading p,
.section-heading p {
  margin: 0;
  color: #8792a5;
  font-size: 13px;
  line-height: 1.6;
}

.primary-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 9px;
  min-height: 42px;
  padding: 0 17px;
  border: 0;
  border-radius: 8px;
  background: #3546a8;
  color: white;
  font-size: 13px;
  font-weight: 650;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(53, 70, 168, .14);
  transition: .2s;
}

.primary-button:hover {
  background: #29398f;
  transform: translateY(-1px);
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
  gap: 17px;
  margin-bottom: 30px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 15px;
  min-height: 108px;
  padding: 19px;
  box-sizing: border-box;
  background: white;
  border: 1px solid #edf0f5;
  border-radius: 13px;
  box-shadow: 0 3px 13px rgba(27, 39, 68, .035);
}

.stat-card > div:last-child {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.stat-card span {
  color: #77849a;
  font-size: 11px;
}

.stat-card strong {
  color: #1e2a43;
  font-size: 25px;
}

.stat-card small {
  color: #a0aabc;
  font-size: 10px;
}

.stat-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 46px;
  height: 46px;
  flex: 0 0 46px;
  border-radius: 12px;
  font-size: 22px;
  font-weight: 700;
}

.total-icon { background: #edf0ff; color: #4b55bd; }
.active-icon { background: #e8f7f0; color: #15966a; }
.completed-icon { background: #eaf2ff; color: #3575d5; }
.archived-icon { background: #f0f1f5; color: #68758b; }

.form-card,
.projects-section {
  padding: 25px;
  margin-bottom: 28px;
  background: white;
  border: 1px solid #edf0f5;
  border-radius: 14px;
  box-shadow: 0 3px 13px rgba(27, 39, 68, .035);
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
  color: #1c2942;
  font-size: 20px;
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

.form-error {
  color: #bd3030;
  font-size: 12px;
}

.form-actions,
.modal-actions {
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
}

.secondary-button:hover {
  background: #f7f8fb;
}

.secondary-button:disabled {
  opacity: .5;
  cursor: not-allowed;
}

.results-count {
  padding: 7px 11px;
  border-radius: 7px;
  background: #f0f2ff;
  color: #5363bd;
  font-size: 11px;
  font-weight: 700;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding-bottom: 19px;
  margin-bottom: 21px;
  border-bottom: 1px solid #edf0f5;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 10px;
  width: min(100%, 440px);
  height: 42px;
  padding: 0 12px;
  border: 1px solid #e1e6ef;
  border-radius: 8px;
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
  border-radius: 8px;
  background: white;
  color: #344158;
}

.projects-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
}

.project-card {
  display: flex;
  flex-direction: column;
  min-width: 0;
  padding: 19px;
  border: 1px solid #e9edf4;
  border-radius: 12px;
  background: white;
  transition: .2s;
}

.project-card:hover {
  transform: translateY(-3px);
  border-color: #d9def4;
  box-shadow: 0 9px 23px rgba(35, 49, 91, .075);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  margin-bottom: 17px;
}

.project-symbol {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 41px;
  height: 41px;
  border-radius: 11px;
  background: #edf0ff;
  color: #4d5cba;
  font-size: 21px;
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

.project-reference {
  color: #9aa5b5;
  font-size: 9px;
  font-weight: 750;
  letter-spacing: 1px;
}

.project-card h3 {
  margin: 8px 0;
  color: #26334c;
  font-size: 16px;
  line-height: 1.4;
}

.project-description {
  display: -webkit-box;
  overflow: hidden;
  min-height: 55px;
  margin: 0;
  color: #8792a5;
  font-size: 12px;
  line-height: 1.65;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
}

.project-meta {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-top: 18px;
  padding: 14px 0;
  border-top: 1px solid #edf0f5;
  border-bottom: 1px solid #edf0f5;
}

.project-meta div {
  display: flex;
  flex-direction: column;
  gap: 5px;
  min-width: 0;
}

.project-meta small {
  color: #9ba5b4;
  font-size: 9px;
}

.project-meta strong {
  overflow: hidden;
  color: #526078;
  font-size: 10px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 9px;
  margin-top: 14px;
}

.action-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  min-height: 35px;
  border: 1px solid #e3e7f0;
  border-radius: 7px;
  background: white;
  color: #5363a5;
  text-decoration: none;
  font-size: 11px;
  font-weight: 650;
  cursor: pointer;
}

.action-button:hover {
  background: #f4f5ff;
}

.members-action {
  grid-column: 1 / -1;
  background: #f5f6ff;
  color: #4858ad;
  border-color: #e1e5ff;
}

.state-actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 7px;
  margin-top: 10px;
  padding-top: 11px;
  border-top: 1px solid #edf0f5;
}

.state-button {
  min-height: 29px;
  padding: 0 9px;
  border: 0;
  border-radius: 6px;
  font-size: 10px;
  font-weight: 650;
  cursor: pointer;
}

.complete-action { background: #eaf2ff; color: #376bc0; }
.archive-action { background: #f0f1f5; color: #69768a; }
.reactivate-action { background: #e8f7ef; color: #168653; }

.delete-action {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 29px;
  height: 29px;
  margin-left: auto;
  border: 1px solid #f2dada;
  border-radius: 6px;
  background: white;
  color: #c04444;
  font-size: 17px;
  cursor: pointer;
}

.delete-action:hover {
  background: #fff0f0;
}

.updating-label {
  margin-top: 9px;
  color: #71809a;
  font-size: 10px;
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

/* MODAL GERAL */

.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: rgba(15, 23, 42, .48);
  backdrop-filter: blur(3px);
}

.confirmation-modal {
  width: 100%;
  max-width: 440px;
  padding: 27px;
  border-radius: 15px;
  background: white;
  box-shadow: 0 20px 60px rgba(0, 0, 0, .18);
}

.modal-icon {
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

.confirmation-modal h2 {
  margin: 0 0 10px;
  color: #1e2a43;
  font-size: 20px;
}

.confirmation-modal p {
  color: #77849a;
  font-size: 13px;
  line-height: 1.7;
}

.confirmation-modal p strong {
  color: #344158;
}

.modal-warning {
  padding: 11px;
  border-radius: 8px;
  background: #fff8e8;
  color: #936b24 !important;
  font-size: 11px !important;
}

.modal-actions {
  margin-top: 20px;
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

.members-modal {
  width: 100%;
  max-width: 720px;
  max-height: 90vh;
  overflow-y: auto;
  padding: 26px;
  border-radius: 15px;
  background: white;
  box-shadow: 0 20px 60px rgba(0, 0, 0, .18);
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
  width: 31px;
  height: 31px;
  border: 1px solid #f1dada;
  border-radius: 7px;
  background: white;
  color: #c04444;
  font-size: 19px;
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

  .projects-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 700px) {
  .projects-page {
    padding: 22px 16px;
  }

  .page-heading {
    align-items: stretch;
    flex-direction: column;
  }

  .page-heading h1 {
    font-size: 24px;
  }

  .page-heading > .primary-button {
    width: 100%;
  }

  .projects-grid {
    grid-template-columns: 1fr;
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

  .form-card,
  .projects-section {
    padding: 17px;
  }

  .members-modal {
    padding: 18px;
    max-height: 94vh;
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

  .project-meta {
    grid-template-columns: 1fr;
  }

  .member-summary {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
