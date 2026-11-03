<script setup lang="ts">
import { onBeforeUnmount } from 'vue'

import 'sweetalert2/dist/sweetalert2.min.css'
import Swal from 'sweetalert2'

// O painel do membro separa tarefas atribuídas das tarefas acessíveis usadas no radar do projeto.
definePageMeta({
  layout: 'member',
})

type EstadoTarefa = 'to_do' | 'in_progress' | 'completed' | 'blocked'

interface ProjetoAPI {
  id: number
  name: string
  status: 'active' | 'completed' | 'archived'
  created_at: string
  updated_at: string | null
}

interface TarefaAPI {
  id: number
  project_id: number
  title: string
  status: EstadoTarefa
  progress: number
  due_date: string | null
}

interface TarefaRadarAPI {
  id: number
  project_id: number
  title: string
  status: EstadoTarefa
  assigned_to: number | null
  due_date: string | null
  created_at: string
  updated_at: string | null
}

interface TarefaPainel {
  id: number
  title: string
  projectName: string
  status: EstadoTarefa
  progress: number
  dueDate: string | null
}

interface TarefaRadar {
  id: number
  projectId: number
  title: string
  project: string
  status: 'Por fazer' | 'Em curso' | 'Concluída' | 'Bloqueada'
  responsible: string
  dueDate: string | null
  createdAt: string
  updatedAt: string | null
}

const api = useNuxtApp().$api
const auth = useAuth()
const projetos = ref<ProjetoAPI[]>([])
const tarefas = ref<TarefaPainel[]>([])
const tarefasRadar = ref<TarefaRadar[]>([])
const carregando = ref(true)
const erro = ref('')
const radarCarregando = ref(true)
const radarErro = ref('')

const estadosRadar: Record<EstadoTarefa, TarefaRadar['status']> = {
  to_do: 'Por fazer',
  in_progress: 'Em curso',
  completed: 'Concluída',
  blocked: 'Bloqueada',
}

const projetosRadar = computed(() => projetos.value.map(projeto => ({
  id: projeto.id,
  name: projeto.name,
  status: projeto.status === 'active'
    ? 'Ativo' as const
    : projeto.status === 'completed'
      ? 'Concluído' as const
      : 'Arquivado' as const,
  createdAt: projeto.created_at,
  updatedAt: projeto.updated_at,
})))

const tarefasConcluidas = computed(
  () => tarefas.value.filter(tarefa => tarefa.status === 'completed').length,
)
const tarefasAbertas = computed(
  () => tarefas.value.filter(tarefa => tarefa.status !== 'completed').length,
)
const progressoGeral = computed(() => tarefas.value.length
  ? Math.round(tarefas.value.reduce((total, tarefa) => total + tarefa.progress, 0) / tarefas.value.length)
  : 0)
const tarefasAtrasadas = computed(() =>
  tarefas.value.filter(tarefa =>
    tarefa.status !== 'completed' &&
    tarefa.dueDate !== null &&
    tarefa.dueDate.slice(0, 10) < hojeISO(),
  ),
)
const tarefasComPrazoProximo = computed(() =>
  tarefas.value.filter(tarefa => {
    if (!tarefa.dueDate || tarefa.status === 'completed') return false
    const dias = diasAtePrazo(tarefa.dueDate)
    return dias >= 1 && dias <= 3
  }),
)
const tarefasOrdenadas = computed(() =>
  tarefas.value
    .filter(tarefa => tarefa.status !== 'completed' && tarefa.dueDate)
    .sort((a, b) => (a.dueDate ?? '').localeCompare(b.dueDate ?? ''))
    .slice(0, 5),
)
const resumoEstados = computed(() => [
  { label: 'Por fazer', status: 'to_do' as const, color: '#94a3b8' },
  { label: 'Em curso', status: 'in_progress' as const, color: '#5965e8' },
  { label: 'Bloqueadas', status: 'blocked' as const, color: '#e35b68' },
  { label: 'Concluídas', status: 'completed' as const, color: '#25a879' },
].map(item => ({
  ...item,
  count: tarefas.value.filter(tarefa => tarefa.status === item.status).length,
  percentage: tarefas.value.length
    ? Math.round(tarefas.value.filter(tarefa => tarefa.status === item.status).length / tarefas.value.length * 100)
    : 0,
})))

// Normaliza o dia local antes de comparar prazos, sem depender de conversões UTC.
function hojeISO(): string {
  const hoje = new Date()
  return `${hoje.getFullYear()}-${String(hoje.getMonth() + 1).padStart(2, '0')}-${String(hoje.getDate()).padStart(2, '0')}`
}

function diasAtePrazo(data: string): number {
  const prazo = new Date(`${data.slice(0, 10)}T12:00:00`)
  const hoje = new Date(`${hojeISO()}T12:00:00`)
  return Math.round((prazo.getTime() - hoje.getTime()) / 86_400_000)
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

function nomeEstado(status: EstadoTarefa): string {
  const nomes: Record<EstadoTarefa, string> = {
    to_do: 'Por fazer',
    in_progress: 'Em curso',
    completed: 'Concluída',
    blocked: 'Bloqueada',
  }
  return nomes[status]
}

function classePrazo(data: string | null): string {
  if (!data) return 'deadline-normal'
  const dias = diasAtePrazo(data)
  if (dias < 0) return 'deadline-overdue'
  if (dias === 0) return 'deadline-today'
  if (dias <= 3) return 'deadline-soon'
  return 'deadline-normal'
}

async function carregarPainel(): Promise<void> {
  const userId = auth.user.value?.id
  if (userId === undefined) {
    erro.value = 'Não foi possível identificar a sua conta. Volte a iniciar sessão.'
    carregando.value = false
    return
  }

  carregando.value = true
  erro.value = ''
  radarCarregando.value = true
  radarErro.value = ''

  try {
    // O resumo pessoal inclui apenas tarefas atribuídas à conta autenticada.
    const [projetosAPI, tarefasAPI] = await Promise.all([
      api<ProjetoAPI[]>('/projects/'),
      api<TarefaAPI[]>(`/tasks/?assigned_to=${encodeURIComponent(userId)}`),
    ])
    const nomesProjetos = new Map(projetosAPI.map(projeto => [projeto.id, projeto.name]))

    projetos.value = projetosAPI
    tarefas.value = tarefasAPI.map(tarefa => ({
      id: tarefa.id,
      title: tarefa.title,
      projectName: nomesProjetos.get(tarefa.project_id) ?? 'Projeto desconhecido',
      status: tarefa.status,
      progress: tarefa.progress,
      dueDate: tarefa.due_date,
    }))
  } catch (error) {
    console.error('Erro ao carregar o painel do front-office:', error)
    erro.value = 'Não foi possível carregar o painel. Verifique a ligação à API e tente novamente.'
  } finally {
    carregando.value = false
  }

  if (erro.value) {
    radarCarregando.value = false
    return
  }

  try {
    // A segunda consulta alimenta riscos dos projetos acessíveis, não só a lista pessoal.
    const userId = auth.user.value?.id
    const tarefasAcessiveis = await api<TarefaRadarAPI[]>('/tasks/')
    const nomesProjetos = new Map(projetos.value.map(projeto => [projeto.id, projeto.name]))

    tarefasRadar.value = tarefasAcessiveis.map(tarefa => ({
      id: tarefa.id,
      projectId: tarefa.project_id,
      title: tarefa.title,
      project: nomesProjetos.get(tarefa.project_id) ?? 'Projeto desconhecido',
      status: estadosRadar[tarefa.status],
      responsible: tarefa.assigned_to === userId
        ? auth.user.value?.name ?? 'Membro atribuído'
        : tarefa.assigned_to === null
          ? 'Por atribuir'
          : 'Outro membro',
      dueDate: tarefa.due_date,
      createdAt: tarefa.created_at,
      updatedAt: tarefa.updated_at,
    }))
  } catch (error) {
    console.error('Erro ao carregar os riscos dos projetos:', error)
    radarErro.value = 'Não foi possível analisar os riscos. Atualize o painel para tentar novamente.'
  } finally {
    radarCarregando.value = false
  }
}

async function alertarPrazos(): Promise<void> {
  // Guarda a confirmação por utilizador e dia para não repetir o aviso durante a sessão.
  const chaveAlerta = `taskflow-prazos-${auth.user.value?.id}-${hojeISO()}`
  if (sessionStorage.getItem(chaveAlerta)) return

  const atrasadas = tarefasAtrasadas.value.length
  const paraHoje = tarefas.value.filter(tarefa =>
    tarefa.status !== 'completed' &&
    tarefa.dueDate !== null &&
    tarefa.dueDate.slice(0, 10) === hojeISO(),
  ).length
  const proximas = tarefasComPrazoProximo.value.length

  if (!atrasadas && !paraHoje && !proximas) return

  const linhas = [
    atrasadas ? `${atrasadas} tarefa(s) em atraso` : '',
    paraHoje ? `${paraHoje} tarefa(s) com prazo hoje` : '',
    proximas ? `${proximas} tarefa(s) nos próximos 3 dias` : '',
  ].filter(Boolean)

  const resultado = await Swal.fire({
    icon: atrasadas ? 'warning' : 'info',
    title: atrasadas ? 'Atenção aos prazos' : 'Prazos a aproximar-se',
    text: linhas.join(' · '),
    confirmButtonText: 'Ver o meu trabalho',
    showCancelButton: true,
    cancelButtonText: 'Agora não',
    confirmButtonColor: '#5965e8',
    cancelButtonColor: '#64748b',
  })

  sessionStorage.setItem(chaveAlerta, 'visto')
  if (resultado.isConfirmed) await navigateTo('/my-work')
}

let refreshTimer: ReturnType<typeof setInterval> | undefined

function atualizarPainelVisivel(): void {
  if (document.visibilityState === 'visible' && !carregando.value) {
    void carregarPainel()
  }
}

onMounted(async () => {
  // Mantém o painel do membro atualizado sem exigir um botão de atualização.
  refreshTimer = setInterval(atualizarPainelVisivel, 60_000)
  document.addEventListener('visibilitychange', atualizarPainelVisivel)
  await carregarPainel()
  if (!erro.value) await alertarPrazos()
})

onBeforeUnmount(() => {
  if (refreshTimer) clearInterval(refreshTimer)
  document.removeEventListener('visibilitychange', atualizarPainelVisivel)
})
</script>

<template>
  <!-- Os indicadores e a fila de prazos resumem o trabalho pessoal antes do radar partilhado. -->
  <section class="front-dashboard">
    <header class="dashboard-welcome">
      <div>
        <span class="eyebrow"><span></span> VISÃO GERAL</span>
        <h1>Olá, {{ auth.user.value?.name ?? 'bem-vindo/a' }}</h1>
        <p>Acompanhe o progresso dos seus projetos e mantenha os prazos sob controlo.</p>
      </div>
    </header>

    <div v-if="erro" class="dashboard-error" role="alert">
      {{ erro }}
      <button type="button" @click="carregarPainel">Tentar novamente</button>
    </div>

    <div v-if="carregando" class="loading-state" role="status">A carregar o seu painel…</div>

    <template v-else-if="!erro">
      <section class="kpi-grid" aria-label="Indicadores do progresso">
        <article class="kpi-card">
          <span class="kpi-icon icon-projects" aria-hidden="true">▤</span>
          <div><span>Projetos</span><strong>{{ projetos.length }}</strong></div>
          <small>{{ projetos.filter(projeto => projeto.status === 'active').length }} ativos</small>
        </article>
        <article class="kpi-card">
          <span class="kpi-icon icon-tasks" aria-hidden="true">✓</span>
          <div><span>Tarefas atribuídas</span><strong>{{ tarefas.length }}</strong></div>
          <small>{{ tarefasAbertas }} por concluir</small>
        </article>
        <article class="kpi-card">
          <span class="kpi-icon icon-progress" aria-hidden="true">↗</span>
          <div><span>Progresso médio</span><strong>{{ progressoGeral }}%</strong></div>
          <small>{{ tarefasConcluidas }} concluídas</small>
        </article>
        <article class="kpi-card" :class="{ 'kpi-card-alert': tarefasAtrasadas.length }">
          <span class="kpi-icon icon-deadline" aria-hidden="true">◷</span>
          <div><span>Tarefas em atraso</span><strong>{{ tarefasAtrasadas.length }}</strong></div>
          <small>{{ tarefasAtrasadas.length ? 'Precisam da sua atenção' : 'Está em dia' }}</small>
        </article>
      </section>

      <DashboardRiskRadar
        :projects="projetosRadar"
        :tasks="tarefasRadar"
        :loading="radarCarregando"
        :error="radarErro"
      />

      <section class="dashboard-grid">
        <article class="dashboard-panel progress-panel">
          <div class="panel-heading">
            <div>
              <span class="section-eyebrow">DISTRIBUIÇÃO</span>
              <h2>Progresso das tarefas</h2>
            </div>
            <span class="total-pill">{{ tarefas.length }} no total</span>
          </div>
          <div v-if="tarefas.length" class="status-list">
            <div v-for="estado in resumoEstados" :key="estado.status" class="status-row">
              <div class="status-copy">
                <span class="status-dot" :style="{ background: estado.color }"></span>
                <span>{{ estado.label }}</span>
                <strong>{{ estado.count }}</strong>
              </div>
              <div class="status-track" role="progressbar" :aria-label="estado.label" :aria-valuenow="estado.percentage" aria-valuemin="0" aria-valuemax="100">
                <span :style="{ width: `${estado.percentage}%`, background: estado.color }"></span>
              </div>
            </div>
          </div>
          <p v-else class="empty-message">Ainda não tem tarefas atribuídas.</p>
          <NuxtLink class="text-link" to="/my-work">Abrir a minha área <span aria-hidden="true">→</span></NuxtLink>
        </article>

        <article class="dashboard-panel deadlines-panel">
          <div class="panel-heading">
            <div>
              <span class="section-eyebrow">ORGANIZE-SE</span>
              <h2>Prazos próximos</h2>
            </div>
            <span class="deadline-count">{{ tarefasAtrasadas.length }} em atraso</span>
          </div>
          <ul v-if="tarefasOrdenadas.length" class="deadline-list">
            <li v-for="tarefa in tarefasOrdenadas" :key="tarefa.id" class="deadline-item">
              <span class="deadline-marker" :class="classePrazo(tarefa.dueDate)"></span>
              <div class="deadline-copy">
                <strong>{{ tarefa.title }}</strong>
                <span>{{ tarefa.projectName }} · {{ nomeEstado(tarefa.status) }}</span>
              </div>
              <time :class="classePrazo(tarefa.dueDate)">{{ formatarData(tarefa.dueDate) }}</time>
            </li>
          </ul>
          <p v-else class="empty-message">Sem tarefas pendentes com prazo definido.</p>
          <NuxtLink class="text-link" to="/my-work">Ver todas as tarefas <span aria-hidden="true">→</span></NuxtLink>
        </article>
      </section>
    </template>
  </section>
</template>

<style scoped>
.front-dashboard { display: grid; gap: 20px; }
.dashboard-welcome { display: flex; align-items: flex-end; justify-content: space-between; gap: 18px; padding: 25px 27px; color: #fff; background: radial-gradient(ellipse at 82% 0%, rgb(155 165 255 / 27%), transparent 34%), linear-gradient(120deg, #283c71, #4e5ac4 75%, #6066d9); border-radius: 16px; box-shadow: 0 12px 28px rgb(52 64 145 / 16%); }
.eyebrow { display: inline-flex; align-items: center; gap: 7px; color: #d3d9ff; font-size: 9px; font-weight: 800; letter-spacing: .13em; }
.eyebrow > span { width: 6px; height: 6px; background: #68dfbd; border-radius: 50%; box-shadow: 0 0 10px rgb(104 223 189 / 55%); }
.dashboard-welcome h1 { margin: 11px 0 6px; font-size: clamp(24px, 3vw, 31px); font-weight: 700; letter-spacing: -.045em; }
.dashboard-welcome p { margin: 0; color: #d7ddf6; font-size: 13px; line-height: 1.6; }
.kpi-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 13px; }
.kpi-card { position: relative; display: grid; min-height: 112px; grid-template-columns: 39px 1fr; align-content: center; align-items: center; column-gap: 11px; padding: 17px; background: #fff; border: 1px solid #e7ebf3; border-radius: 12px; box-shadow: 0 3px 11px rgb(25 42 78 / 3%); }
.kpi-icon { display: grid; width: 38px; height: 38px; grid-row: span 2; place-items: center; border-radius: 11px; font-size: 17px; font-weight: 700; }
.icon-projects { color: #555ed3; background: #eef0ff; }
.icon-tasks { color: #3282bd; background: #eaf5ff; }
.icon-progress { color: #209a73; background: #e8f8f1; }
.icon-deadline { color: #d48a27; background: #fff5e5; }
.kpi-card-alert .icon-deadline { color: #cf4453; background: #fff0f1; }
.kpi-card > div { display: grid; gap: 5px; }
.kpi-card > div > span { color: #77849a; font-size: 10px; font-weight: 550; }
.kpi-card > div > strong { color: #24334e; font-size: 25px; font-weight: 750; line-height: 1; letter-spacing: -.04em; font-variant-numeric: tabular-nums; }
.kpi-card > small { grid-column: 2; margin-top: 7px; color: #9aa5b7; font-size: 9px; }
.kpi-card-alert > small { color: #c94c57; }
.dashboard-grid { display: grid; grid-template-columns: minmax(0, .95fr) minmax(0, 1.25fr); gap: 15px; }
.dashboard-panel { min-width: 0; padding: 20px; background: #fff; border: 1px solid #e7ebf3; border-radius: 12px; box-shadow: 0 3px 11px rgb(25 42 78 / 3%); }
.panel-heading { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 21px; }
.section-eyebrow { color: #8c98ad; font-size: 8px; font-weight: 800; letter-spacing: .12em; }
.panel-heading h2 { margin: 5px 0 0; color: #263650; font-size: 15px; font-weight: 700; letter-spacing: -.02em; }
.total-pill, .deadline-count { padding: 6px 9px; color: #66738b; background: #f5f7fb; border: 1px solid #edf0f5; border-radius: 20px; font-size: 9px; font-weight: 650; white-space: nowrap; }
.deadline-count { color: #b64c56; background: #fff3f3; border-color: #ffe4e4; }
.status-list { display: grid; gap: 16px; }
.status-row { display: grid; gap: 7px; }
.status-copy { display: flex; align-items: center; gap: 8px; color: #56647b; font-size: 11px; }
.status-copy strong { margin-left: auto; color: #33425d; font-size: 11px; font-variant-numeric: tabular-nums; }
.status-dot { width: 7px; height: 7px; border-radius: 50%; }
.status-track { height: 6px; overflow: hidden; background: #f0f2f7; border-radius: 10px; }
.status-track span { display: block; height: 100%; border-radius: inherit; transition: width .3s ease; }
.text-link { display: inline-flex; align-items: center; gap: 7px; margin-top: 21px; color: #525fd4; font-size: 10px; font-weight: 700; text-decoration: none; }
.text-link:hover { color: #3845b7; }
.deadline-list { display: grid; gap: 0; margin: 0; padding: 0; list-style: none; }
.deadline-item { display: flex; min-width: 0; align-items: center; gap: 10px; padding: 11px 0; border-bottom: 1px solid #f0f2f6; }
.deadline-item:first-child { padding-top: 0; }
.deadline-item:last-child { padding-bottom: 0; border-bottom: 0; }
.deadline-marker { width: 4px; height: 31px; flex: 0 0 4px; background: #cbd5e1; border-radius: 4px; }
.deadline-marker.deadline-overdue { background: #e0505d; }
.deadline-marker.deadline-today { background: #e39b34; }
.deadline-marker.deadline-soon { background: #6674e6; }
.deadline-copy { display: grid; min-width: 0; flex: 1; gap: 4px; }
.deadline-copy strong { overflow: hidden; color: #34425b; font-size: 11px; font-weight: 650; text-overflow: ellipsis; white-space: nowrap; }
.deadline-copy span { overflow: hidden; color: #97a1b1; font-size: 9px; text-overflow: ellipsis; white-space: nowrap; }
.deadline-item time { color: #738097; font-size: 9px; white-space: nowrap; }
.deadline-item time.deadline-overdue { color: #c4424e; font-weight: 700; }
.deadline-item time.deadline-today { color: #bb761e; font-weight: 700; }
.deadline-item time.deadline-soon { color: #5360c9; font-weight: 650; }
.empty-message, .loading-state { padding: 18px 0; color: #929daf; font-size: 11px; text-align: center; }
.loading-state { padding: 44px 15px; background: #fff; border: 1px solid #e7ebf3; border-radius: 12px; }
.dashboard-error { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 12px 14px; color: #a53d47; background: #fff3f3; border: 1px solid #f7d8db; border-radius: 9px; font-size: 11px; }
.dashboard-error button { padding: 7px 10px; color: #a53d47; background: #fff; border: 1px solid #f0c7ca; border-radius: 7px; font-size: 10px; font-weight: 650; cursor: pointer; white-space: nowrap; }

@media (max-width: 1000px) {
  .kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .dashboard-grid { grid-template-columns: 1fr; }
}
@media (max-width: 560px) {
  .dashboard-welcome { align-items: flex-start; flex-direction: column; padding: 20px; }
  .kpi-grid { gap: 9px; }
  .kpi-card { min-height: 100px; grid-template-columns: 32px 1fr; column-gap: 8px; padding: 12px; }
  .kpi-icon { width: 32px; height: 32px; font-size: 15px; }
  .kpi-card > div > span { font-size: 9px; }
  .kpi-card > div > strong { font-size: 22px; }
  .kpi-card > small { font-size: 8px; }
  .dashboard-panel { padding: 16px; }
  .deadline-item { gap: 7px; }
  .deadline-item time { font-size: 8px; }
}
@media (prefers-reduced-motion: reduce) {
  .status-track span { transition: none; }
}
</style>
