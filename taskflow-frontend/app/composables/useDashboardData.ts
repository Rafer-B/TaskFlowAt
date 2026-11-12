
import { onMounted, reactive, ref } from 'vue'
import { fetchAllPages } from '~/composables/usePaginatedApi'

// Tipos do dashboard em português para separar o modelo visual do formato da API.
export type TaskStatus =
  | 'Por fazer'
  | 'Em curso'
  | 'Concluída'
  | 'Bloqueada'

export type TaskPriority = 'Baixa' | 'Média' | 'Alta'

export type ProjectStatus = 'Ativo' | 'Concluído' | 'Arquivado'

export interface DashboardProject {
  id: string
  name: string
  status: ProjectStatus
  dueDate: string | null
  createdAt: string
  updatedAt: string | null
}

export interface DashboardUser {
  id: string
  name: string
  email: string
  isActive: boolean
}

export interface DashboardTask {
  id: string
  projectId: string
  title: string
  project: string
  responsible: string
  dueDate: string | null
  priority: TaskPriority
  status: TaskStatus
  completedAt: string | null
  createdAt: string
  updatedAt: string | null
}

export interface DashboardData {
  projects: DashboardProject[]
  tasks: DashboardTask[]
  users: DashboardUser[]
}

interface ProjetoAPI {
  id: string
  name: string
  description: string | null
  status: 'active' | 'completed' | 'archived'
  created_by: string
  created_at: string
  updated_at: string | null
  archived_at: string | null
}

interface UtilizadorAPI {
  id: string
  name: string
  email: string
  is_active: boolean
}

interface TarefaAPI {
  id: string
  project_id: string
  title: string
  description: string | null
  category: string
  priority: 'low' | 'medium' | 'high'
  status: 'to_do' | 'in_progress' | 'completed' | 'blocked'
  assigned_to: string | null
  assignee_ids: string[]
  created_by: string
  due_date: string | null
  created_at: string
  updated_at: string | null
  completed_at: string | null
}

const estadoProjeto: Record<ProjetoAPI['status'], ProjectStatus> = {
  active: 'Ativo',
  completed: 'Concluído',
  archived: 'Arquivado',
}

const estadoTarefa: Record<TarefaAPI['status'], TaskStatus> = {
  to_do: 'Por fazer',
  in_progress: 'Em curso',
  completed: 'Concluída',
  blocked: 'Bloqueada',
}

const prioridadeTarefa: Record<TarefaAPI['priority'], TaskPriority> = {
  low: 'Baixa',
  medium: 'Média',
  high: 'Alta',
}

// Datas ISO recebidas com hora são reduzidas ao dia para os cálculos do painel.
function apenasData(data: string | null): string | null {
  return data ? data.slice(0, 10) : null
}

export function useDashboardData(_today: Date): DashboardData & {
  carregando: ReturnType<typeof ref<boolean>>
  erro: ReturnType<typeof ref<string>>
  atualizar: () => Promise<void>
} {
  // Centraliza a carga e transformação dos dados consumidos pelos indicadores administrativos.
  const projects = reactive<DashboardProject[]>([])
  const tasks = reactive<DashboardTask[]>([])
  const users = reactive<DashboardUser[]>([])

  const carregando = ref(true)
  const erro = ref('')

  async function carregarDados(): Promise<void> {
    carregando.value = true
    erro.value = ''

    try {
      // As listas são independentes, por isso são pedidas em paralelo antes de as relacionar.
      const [projetosAPI, tarefasAPI, utilizadoresAPI] = await Promise.all([
        fetchAllPages<ProjetoAPI>('/projects/'),
        fetchAllPages<TarefaAPI>('/tasks/'),
        fetchAllPages<UtilizadorAPI>('/users/'),
      ])

      const nomesProjetos = new Map(
        projetosAPI.map((projeto) => [projeto.id, projeto.name]),
      )

      const nomesUtilizadores = new Map(
        utilizadoresAPI.map((utilizador) => [
          utilizador.id,
          utilizador.name,
        ]),
      )

      const projetosConvertidos: DashboardProject[] = projetosAPI.map(
        (projeto) => ({
          id: projeto.id,
          name: projeto.name,
          status: estadoProjeto[projeto.status],
          dueDate: null,
          createdAt: projeto.created_at,
          updatedAt: projeto.updated_at,
        }),
      )

      const utilizadoresConvertidos: DashboardUser[] =
        utilizadoresAPI.map((utilizador) => ({
          id: utilizador.id,
          name: utilizador.name,
          email: utilizador.email,
          isActive: utilizador.is_active,
        }))

      // Os identificadores de projeto e responsável são resolvidos para rótulos legíveis.
      const tarefasConvertidas: DashboardTask[] = tarefasAPI.map(
        (tarefa) => ({
          id: tarefa.id,
          projectId: tarefa.project_id,
          title: tarefa.title,
          project:
            nomesProjetos.get(tarefa.project_id) ??
            'Projeto desconhecido',
          responsible: (tarefa.assignee_ids ?? (
            tarefa.assigned_to === null ? [] : [tarefa.assigned_to]
          ))
            .map((userId) => nomesUtilizadores.get(userId) ?? 'Utilizador desconhecido')
            .join(', ') || 'Por atribuir',
          dueDate: apenasData(tarefa.due_date),
          priority: prioridadeTarefa[tarefa.priority],
          status: estadoTarefa[tarefa.status],
          completedAt: apenasData(tarefa.completed_at),
          createdAt: tarefa.created_at,
          updatedAt: tarefa.updated_at,
        }),
      )

      projects.splice(0, projects.length, ...projetosConvertidos)
      tasks.splice(0, tasks.length, ...tarefasConvertidas)
      users.splice(0, users.length, ...utilizadoresConvertidos)
    } catch (error) {
      console.error('Erro ao carregar o Dashboard:', error)

      erro.value =
        'Não foi possível carregar os dados. Verifique se a API está em execução e tente novamente.'
    } finally {
      carregando.value = false
    }
  }

  onMounted(carregarDados)

  return {
    projects,
    tasks,
    users,
    carregando,
    erro,
    atualizar: carregarDados,
  }
}
