/* // Dados temporários para o dashboard.
// A estrutura imita a resposta esperada do FastAPI. Quando a API estiver pronta,
// basta substituir o corpo desta função por um pedido a `runtimeConfig.public.apiBase`.
// As datas são geradas em relação a "hoje", para o dashboard parecer sempre atual.

//export type TaskStatus = 'Por fazer' | 'Em curso' | 'Concluída' | 'Bloqueada'
export type TaskPriority = 'Baixa' | 'Média' | 'Alta'
export type ProjectStatus = 'Ativo' | 'Concluído' | 'Arquivado'

export interface DashboardProject {
  id: number
  name: string
  status: ProjectStatus
  dueDate: string
}

export interface DashboardTask {
  id: number
  title: string
  project: string
  responsible: string
  dueDate: string
  priority: TaskPriority
  status: TaskStatus
  completedAt: string | null
}

export interface DashboardData {
  projects: DashboardProject[]
  tasks: DashboardTask[]
}

interface TaskSeed {
  title: string
  project: string
  responsible: string
  due: number
  priority: TaskPriority
  status: TaskStatus
  doneOffset?: number
}

export function useDashboardData(today: Date): DashboardData {
  const day = (offset: number) => toISODay(addDays(today, offset))

  const taskflow = 'Desenvolvimento do TaskFlow'
  const bases = 'Projeto de Bases de Dados'
  const seguranca = 'Trabalho de Segurança'
  const engenharia = 'Relatório de Engenharia de Software'
  const redes = 'Estudo de Redes'

  const projects: DashboardProject[] = [
    { id: 1, name: taskflow, status: 'Ativo', dueDate: day(21) },
    { id: 2, name: bases, status: 'Ativo', dueDate: day(14) },
    { id: 3, name: seguranca, status: 'Ativo', dueDate: day(9) },
    { id: 4, name: engenharia, status: 'Ativo', dueDate: day(30) },
    { id: 5, name: redes, status: 'Concluído', dueDate: day(-4) }
  ]

  // Ordenadas da mais antiga para a mais recente.
  const seeds: TaskSeed[] = [
    { title: 'Mapear a topologia da rede', project: redes, responsible: 'Maria Lopes', due: -7, priority: 'Média', status: 'Concluída', doneOffset: -6 },
    { title: 'Documentar as configurações', project: redes, responsible: 'João Costa', due: -4, priority: 'Baixa', status: 'Concluída', doneOffset: -3 },
    { title: 'Apresentar os resultados', project: redes, responsible: 'Maria Lopes', due: -4, priority: 'Alta', status: 'Concluída', doneOffset: -3 },
    { title: 'Desenhar os diagramas UML', project: engenharia, responsible: 'Maria Lopes', due: -5, priority: 'Média', status: 'Concluída', doneOffset: -5 },
    { title: 'Normalizar o esquema relacional', project: bases, responsible: 'Ana Silva', due: -4, priority: 'Alta', status: 'Concluída', doneOffset: -4 },
    { title: 'Rever o relatório final', project: bases, responsible: 'João Costa', due: -1, priority: 'Baixa', status: 'Concluída', doneOffset: -1 },
    { title: 'Configurar a autenticação', project: taskflow, responsible: 'João Costa', due: -2, priority: 'Alta', status: 'Em curso' },
    { title: 'Criar o modelo da base de dados', project: taskflow, responsible: 'Ana Silva', due: 5, priority: 'Alta', status: 'Em curso' },
    { title: 'Desenhar o dashboard', project: taskflow, responsible: 'Maria Lopes', due: 0, priority: 'Média', status: 'Concluída', doneOffset: 0 },
    { title: 'Pesquisar ferramentas de segurança', project: seguranca, responsible: 'Maria Lopes', due: 2, priority: 'Média', status: 'Por fazer' },
    { title: 'Validar os requisitos da aplicação', project: taskflow, responsible: 'Por atribuir', due: 10, priority: 'Média', status: 'Bloqueada' },
    { title: 'Implementar a página de projetos', project: taskflow, responsible: 'João Costa', due: 8, priority: 'Alta', status: 'Em curso' },
    { title: 'Definir os endpoints da API', project: taskflow, responsible: 'Ana Silva', due: 3, priority: 'Alta', status: 'Em curso' },
    { title: 'Escrever as consultas SQL', project: bases, responsible: 'João Costa', due: 4, priority: 'Média', status: 'Por fazer' },
    { title: 'Comparar soluções HIDS e NIDS', project: seguranca, responsible: 'Maria Lopes', due: 6, priority: 'Média', status: 'Em curso' },
    { title: 'Configurar o laboratório de testes', project: seguranca, responsible: 'Por atribuir', due: 7, priority: 'Alta', status: 'Bloqueada' },
    { title: 'Redigir a documentação técnica', project: engenharia, responsible: 'Ana Silva', due: 14, priority: 'Baixa', status: 'Por fazer' }
  ]

  const tasks: DashboardTask[] = seeds.map((seed, index) => ({
    id: index + 1,
    title: seed.title,
    project: seed.project,
    responsible: seed.responsible,
    dueDate: day(seed.due),
    priority: seed.priority,
    status: seed.status,
    completedAt: seed.doneOffset === undefined ? null : day(seed.doneOffset)
  }))

  return { projects, tasks }
} */


import { onMounted, reactive, ref } from 'vue'

export type TaskStatus = 'Por fazer' | 'Em curso' | 'Concluída' | 'Bloqueada'
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
} {
  const config = useRuntimeConfig()
  const apiBase = config.public.apiBase

  // Mantemos os mesmos arrays reativos usados pelo Dashboard.
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
        projetosAPI.map((p) => [p.id, p.name]),
      )

      const nomesUtilizadores = new Map(
        utilizadoresAPI.map((u) => [u.id, u.name]),
      )

      const projetosConvertidos: DashboardProject[] = projetosAPI.map((p) => ({
        id: p.id,
        name: p.name,
        status: estadoProjeto[p.status],
        // A tabela projects não tem um campo de prazo.
        dueDate: null,
      }))

      const tarefasConvertidas: DashboardTask[] = tarefasAPI.map((t) => ({
        id: t.id,
        title: t.title,
        project: nomesProjetos.get(t.project_id) ?? 'Projeto desconhecido',
        responsible: t.assigned_to == null
          ? 'Por atribuir'
          : nomesUtilizadores.get(t.assigned_to) ?? 'Utilizador desconhecido',
        dueDate: apenasData(t.due_date),
        priority: prioridadeTarefa[t.priority],
        status: estadoTarefa[t.status],
        completedAt: apenasData(t.completed_at),
      }))

      projects.splice(0, projects.length, ...projetosConvertidos)
      tasks.splice(0, tasks.length, ...tarefasConvertidas)
    } catch (error) {
      console.error('Erro ao carregar dados do Dashboard:', error)
      erro.value = 'Não foi possível carregar os dados do Dashboard. Confirma se a API está em execução.'
    } finally {
      carregando.value = false
    }
  }

  onMounted(carregarDados)

  return { projects, tasks, carregando, erro }
}
