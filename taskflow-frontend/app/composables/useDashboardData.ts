
import { onMounted, reactive, ref } from 'vue'

export type TaskStatus =
  | 'Por fazer'
  | 'Em curso'
  | 'Concluída'
  | 'Bloqueada'

export type TaskPriority = 'Baixa' | 'Média' | 'Alta'

export type ProjectStatus = 'Ativo' | 'Concluído' | 'Arquivado'

export interface DashboardProject {
  id: number
  name: string
  status: ProjectStatus
  dueDate: string | null
}

export interface DashboardTask {
  id: number
  title: string
  project: string
  responsible: string
  dueDate: string | null
  priority: TaskPriority
  status: TaskStatus
  completedAt: string | null
}

export interface DashboardData {
  projects: DashboardProject[]
  tasks: DashboardTask[]
}

interface ProjetoAPI {
  id: number
  name: string
  description: string | null
  status: 'active' | 'completed' | 'archived'
  created_by: number
  created_at: string
  updated_at: string | null
  archived_at: string | null
}

interface UtilizadorAPI {
  id: number
  name: string
  email: string
  is_active: boolean
}

interface TarefaAPI {
  id: number
  project_id: number
  title: string
  description: string | null
  category: string
  priority: 'low' | 'medium' | 'high'
  status: 'to_do' | 'in_progress' | 'completed' | 'blocked'
  assigned_to: number | null
  created_by: number
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

function apenasData(data: string | null): string | null {
  return data ? data.slice(0, 10) : null
}

export function useDashboardData(_today: Date): DashboardData & {
  carregando: ReturnType<typeof ref<boolean>>
  erro: ReturnType<typeof ref<string>>
  atualizar: () => Promise<void>
} {
  const config = useRuntimeConfig()
  const apiBase = String(config.public.apiBase).replace(/\/$/, '')

  const projects = reactive<DashboardProject[]>([])
  const tasks = reactive<DashboardTask[]>([])

  const carregando = ref(true)
  const erro = ref('')

  async function carregarDados() {
    carregando.value = true
    erro.value = ''

    try {
      const [projetosAPI, tarefasAPI, utilizadoresAPI] = await Promise.all([
        $fetch<ProjetoAPI[]>(`${apiBase}/projects/`),
        $fetch<TarefaAPI[]>(`${apiBase}/tasks/`),
        $fetch<UtilizadorAPI[]>(`${apiBase}/users/`),
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

      const projetosConvertidos: DashboardProject[] =
        projetosAPI.map((projeto) => ({
          id: projeto.id,
          name: projeto.name,
          status: estadoProjeto[projeto.status],
          dueDate: null,
        }))

      const tarefasConvertidas: DashboardTask[] =
        tarefasAPI.map((tarefa) => ({
          id: tarefa.id,
          title: tarefa.title,
          project:
            nomesProjetos.get(tarefa.project_id) ??
            'Projeto desconhecido',
          responsible:
            tarefa.assigned_to == null
              ? 'Por atribuir'
              : nomesUtilizadores.get(tarefa.assigned_to) ??
                'Utilizador desconhecido',
          dueDate: apenasData(tarefa.due_date),
          priority: prioridadeTarefa[tarefa.priority],
          status: estadoTarefa[tarefa.status],
          completedAt: apenasData(tarefa.completed_at),
        }))

      projects.splice(0, projects.length, ...projetosConvertidos)
      tasks.splice(0, tasks.length, ...tarefasConvertidas)
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
    carregando,
    erro,
    atualizar: carregarDados,
  }
}
