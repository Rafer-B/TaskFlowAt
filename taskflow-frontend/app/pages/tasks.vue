
<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

definePageMeta({
  layout: 'admin',
})

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
  responsible: string
  dueDate: string
  priority: Prioridade
  status: EstadoTarefa
  category: Categoria
}

interface ProjetoOpcao {
  id: number
  name: string
}

const config = useRuntimeConfig()
const apiBase = config.public.apiBase
const route = useRoute()

// --------------------------------------------------
// DADOS
// --------------------------------------------------

const tarefas = ref<Tarefa[]>([])
const projetosDisponiveis = ref<ProjetoOpcao[]>([])
const utilizadores = ref<UtilizadorAPI[]>([])

const pesquisa = ref('')
const filtroEstado = ref('')
const filtroPrioridade = ref('')

const mostrarFormulario = ref(false)
const erro = ref('')
const carregando = ref(false)
const aGuardar = ref(false)

// --------------------------------------------------
// OPÇÕES DOS CAMPOS
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
// CONVERSÃO DOS VALORES ENTRE FRONTEND E API
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
// FORMULÁRIO DE NOVA TAREFA
// --------------------------------------------------

const novaTarefa = ref({
  title: '',
  description: '',
  projectId: '',
  assignedTo: '',
  dueDate: '',
  priority: 'Média' as Prioridade,
  status: 'Por fazer' as EstadoTarefa,
  category: 'Desenvolvimento' as Categoria,
})

// Temporário: substituir pelo ID do utilizador autenticado
// quando implementarmos a autenticação.
const utilizadorId = 1

function limparFormulario() {
  const primeiroProjeto = projetosDisponiveis.value[0]

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
}

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
      ].some((valor) => valor.toLowerCase().includes(termo))

    const correspondeEstado =
      !filtroEstado.value ||
      tarefa.status === filtroEstado.value

    const correspondePrioridade =
      !filtroPrioridade.value ||
      tarefa.priority === filtroPrioridade.value

    return (
      correspondePesquisa &&
      correspondeEstado &&
      correspondePrioridade
    )
  })
})

// --------------------------------------------------
// RESUMO DAS TAREFAS
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
// CONVERTER TAREFA RECEBIDA DA API
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
    responsible: responsavel?.name ?? 'Por atribuir',
    dueDate: tarefa.due_date
      ? tarefa.due_date.slice(0, 10)
      : '',
    priority: prioridadeDaAPI[tarefa.priority],
    status: estadoDaAPI[tarefa.status],
    category: categoriaDaAPI[tarefa.category],
  }
}

// --------------------------------------------------
// CARREGAR PROJETOS, UTILIZADORES E TAREFAS
// --------------------------------------------------

async function carregarDados() {
  erro.value = ''
  carregando.value = true

  try {
    const [listaProjetos, listaUtilizadores] = await Promise.all([
      $fetch<ProjetoAPI[]>(`${apiBase}/projects/`),
      $fetch<UtilizadorAPI[]>(`${apiBase}/users/`),
    ])

    projetosDisponiveis.value = listaProjetos.map((projeto) => ({
      id: projeto.id,
      name: projeto.name,
    }))

    utilizadores.value = listaUtilizadores.filter(
      (utilizador) => utilizador.is_active,
    )

    // Verificar se existe um projeto indicado na URL.
    const projectQuery = route.query.project

    const projectId = Array.isArray(projectQuery)
      ? projectQuery[0]
      : projectQuery

    const primeiroProjeto = projetosDisponiveis.value[0]

    if (
      projectId &&
      /^\d+$/.test(projectId) &&
      projetosDisponiveis.value.some(
        (projeto) => projeto.id === Number(projectId),
      )
    ) {
      novaTarefa.value.projectId = projectId
    } else if (primeiroProjeto) {
      novaTarefa.value.projectId = String(primeiroProjeto.id)
    }

    // Carregar tarefas depois de carregar projetos e utilizadores.
    const listaTarefas = await $fetch<TarefaAPI[]>(
      `${apiBase}/tasks/`,
    )

    tarefas.value = listaTarefas.map(converterTarefa)
  } catch (error) {
    console.error('Erro ao carregar dados das tarefas:', error)

    erro.value =
      'Não foi possível carregar as tarefas, os projetos ou os utilizadores. Confirma se a API está ativa.'
  } finally {
    carregando.value = false
  }
}

// --------------------------------------------------
// CRIAR TAREFA
// --------------------------------------------------

async function adicionarTarefa() {
  erro.value = ''

  const titulo = novaTarefa.value.title.trim()
  const projetoId = Number(novaTarefa.value.projectId)

  const responsavelId = novaTarefa.value.assignedTo
    ? Number(novaTarefa.value.assignedTo)
    : null

  if (!titulo) {
    erro.value = 'O título da tarefa é obrigatório.'
    return
  }

  if (
    !projetoId ||
    !projetosDisponiveis.value.some(
      (projeto) => projeto.id === projetoId,
    )
  ) {
    erro.value = 'Seleciona um projeto válido.'
    return
  }

  if (
    responsavelId !== null &&
    !utilizadores.value.some(
      (utilizador) => utilizador.id === responsavelId,
    )
  ) {
    erro.value = 'Seleciona um responsável válido.'
    return
  }

  aGuardar.value = true

  try {
    const criada = await $fetch<TarefaAPI>(
      `${apiBase}/tasks/`,
      {
        method: 'POST',

        body: {
          project_id: projetoId,
          title: titulo,
          description:
            novaTarefa.value.description.trim() || null,
          category: categoriaParaAPI[novaTarefa.value.category],
          priority: prioridadeParaAPI[novaTarefa.value.priority],
          status: estadoParaAPI[novaTarefa.value.status],
          assigned_to: responsavelId,
          created_by: utilizadorId,
          due_date: novaTarefa.value.dueDate
            ? `${novaTarefa.value.dueDate}T00:00:00`
            : null,
        },
      },
    )

    tarefas.value.unshift(converterTarefa(criada))

    limparFormulario()
    mostrarFormulario.value = false
  } catch (error) {
    console.error('Erro ao criar tarefa:', error)

    erro.value =
      'Não foi possível guardar a tarefa. Confirma se o projeto e os IDs dos utilizadores existem.'
  } finally {
    aGuardar.value = false
  }
}

// --------------------------------------------------
// ALTERAR ESTADO DA TAREFA
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

  erro.value = ''

  // Atualização visual imediata.
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
  } catch (error) {
    console.error(
      'Erro ao atualizar o estado da tarefa:',
      error,
    )

    // Reverter alteração se a API devolver um erro.
    tarefa.status = estadoAnterior
    elemento.value = estadoAnterior

    erro.value =
      'Não foi possível atualizar o estado da tarefa. A alteração foi revertida.'
  }
}

// --------------------------------------------------
// FORMATAÇÃO DE DATAS
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
        @click="mostrarFormulario = !mostrarFormulario"
      >
        {{ mostrarFormulario ? 'Cancelar' : '+ Nova tarefa' }}
      </button>
    </header>

    <!-- CARREGAMENTO -->
    <p v-if="carregando" class="empty-state">
      A carregar tarefas...
    </p>

    <!-- ERROS -->
    <p v-if="erro" class="error-message" role="alert">
      {{ erro }}
    </p>

    <!-- RESUMO -->
    <section class="summary-grid">
      <article class="summary-card">
        <span>Total de tarefas</span>
        <strong>{{ resumo.total }}</strong>
      </article>

      <article class="summary-card">
        <span>Por fazer</span>
        <strong>{{ resumo.porFazer }}</strong>
      </article>

      <article class="summary-card">
        <span>Em curso</span>
        <strong>{{ resumo.emCurso }}</strong>
      </article>

      <article class="summary-card">
        <span>Concluídas</span>
        <strong>{{ resumo.concluidas }}</strong>
      </article>

      <article class="summary-card">
        <span>Bloqueadas</span>
        <strong>{{ resumo.bloqueadas }}</strong>
      </article>
    </section>

    <!-- FORMULÁRIO DE CRIAÇÃO -->
    <section
      v-if="mostrarFormulario"
      class="form-card"
    >
      <h2>Criar tarefa</h2>

      <form @submit.prevent="adicionarTarefa">

        <div class="form-grid">

          <div class="field full-width">
            <label for="titulo">Título *</label>

            <input
              id="titulo"
              v-model="novaTarefa.title"
              type="text"
              maxlength="200"
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
              maxlength="2000"
              placeholder="Descreve o que é necessário fazer..."
            />
          </div>

          <div class="field">
            <label for="projeto">Projeto *</label>

            <select
              id="projeto"
              v-model="novaTarefa.projectId"
              required
              :disabled="projetosDisponiveis.length === 0"
            >
              <option value="" disabled>
                Seleciona um projeto
              </option>

              <option
                v-for="projeto in projetosDisponiveis"
                :key="projeto.id"
                :value="String(projeto.id)"
              >
                {{ projeto.name }}
              </option>
            </select>

            <small v-if="projetosDisponiveis.length === 0">
              Não existem projetos disponíveis.
            </small>
          </div>

          <div class="field">
            <label for="responsavel">Responsável</label>

            <select
              id="responsavel"
              v-model="novaTarefa.assignedTo"
            >
              <option value="">
                Por atribuir
              </option>

              <option
                v-for="utilizador in utilizadores"
                :key="utilizador.id"
                :value="String(utilizador.id)"
              >
                {{ utilizador.name }}
              </option>
            </select>
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
            <label for="estado">Estado inicial</label>

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

        <p
          v-if="erro"
          class="error-message"
          role="alert"
        >
          {{ erro }}
        </p>

        <button
          type="submit"
          class="primary-button"
          :disabled="aGuardar || projetosDisponiveis.length === 0"
        >
          {{ aGuardar ? 'A guardar...' : 'Guardar tarefa' }}
        </button>

      </form>
    </section>

    <!-- LISTAGEM DE TAREFAS -->
    <section class="tasks-section">

      <!-- FILTROS -->
      <div class="filters">

        <input
          v-model="pesquisa"
          type="search"
          placeholder="Pesquisar tarefa, projeto ou responsável..."
          aria-label="Pesquisar tarefas"
        />

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

                <div class="task-description">
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

            </tr>

            <tr v-if="tarefasFiltradas.length === 0">
              <td
                colspan="6"
                class="empty-state"
              >
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

  </main>
</template>

<style scoped>
.page {
  max-width: 1400px;
  margin: 0 auto;
  padding: 36px 24px;
  color: #172033;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  margin-bottom: 28px;
}

.back-link {
  color: #4f46e5;
  font-size: 14px;
  text-decoration: none;
}

.back-link:hover {
  text-decoration: underline;
}

.page-header h1 {
  margin: 14px 0 6px;
  font-size: 32px;
}

.page-header p {
  margin: 0;
  color: #64748b;
}

.primary-button {
  border: 0;
  border-radius: 8px;
  padding: 12px 18px;
  background: #4f46e5;
  color: white;
  font-weight: 600;
  cursor: pointer;
  transition: background .2s ease, opacity .2s ease;
}

.primary-button:hover {
  background: #4338ca;
}

.primary-button:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 28px;
}

.summary-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 20px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  background: white;
}

.summary-card span {
  color: #64748b;
  font-size: 13px;
}

.summary-card strong {
  font-size: 28px;
}

.form-card {
  max-width: 850px;
  margin-bottom: 30px;
  padding: 24px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  background: white;
}

.form-card h2 {
  margin-top: 0;
  font-size: 21px;
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

.field textarea {
  resize: vertical;
}

.field small {
  color: #b45309;
  font-size: 12px;
}

.error-message {
  margin: 12px 0;
  color: #b91c1c;
  font-size: 14px;
}

.tasks-section {
  padding: 22px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  background: white;
}

.filters {
  display: grid;
  grid-template-columns:
    minmax(220px, 2fr)
    minmax(160px, 1fr)
    minmax(160px, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.table-container {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
  font-size: 13px;
}

th {
  padding: 14px 12px;
  background: #f8fafc;
  color: #64748b;
  font-weight: 600;
  white-space: nowrap;
}

td {
  padding: 16px 12px;
  border-bottom: 1px solid #e2e8f0;
  vertical-align: top;
}

.task-title {
  min-width: 180px;
  font-weight: 600;
  color: #172033;
}

.task-description {
  max-width: 280px;
  margin-top: 5px;
  color: #64748b;
  line-height: 1.5;
}

.category {
  display: inline-block;
  margin-top: 8px;
  color: #475569;
  font-size: 11px;
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

.empty-state {
  padding: 32px;
  text-align: center;
  color: #64748b;
}

.results-count {
  margin: 16px 0 0;
  color: #64748b;
  font-size: 13px;
}

@media (max-width: 900px) {
  .summary-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .filters {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 600px) {
  .page {
    padding: 24px 14px;
  }

  .page-header {
    align-items: stretch;
    flex-direction: column;
  }

  .page-header h1 {
    font-size: 27px;
  }

  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .form-grid {
    grid-template-columns: 1fr;
  }

  .full-width {
    grid-column: auto;
  }

  .tasks-section {
    padding: 12px;
  }
}
</style>
