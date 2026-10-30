<script setup lang="ts">

import { computed } from 'vue'

import type {
  DashboardTask,
  TaskPriority,
  TaskStatus,
} from '~/composables/useDashboardData'

import {
  toISODay,
  addDays,
  parseISODay,
  diffInDays,
  formatarDataHora,
} from '~/utils/dates'

definePageMeta({
  layout: 'admin',
})

const todayISO = useState('dashboard-today', () => toISODay(new Date()))
const today = computed(() => parseISODay(todayISO.value))

const {
  projects,
  tasks,
  carregando,
  erro,
} = useDashboardData(today.value)

const STATUS_COLORS: Record<TaskStatus, string> = {
  'Por fazer': '#94a3b8',
  'Em curso': '#3b82f6',
  'Concluída': '#22c55e',
  'Bloqueada': '#ef4444'
}

const STATUS_ORDER: TaskStatus[] = ['Em curso', 'Por fazer', 'Bloqueada', 'Concluída']
const PRIORITY_WEIGHT: Record<TaskPriority, number> = { Alta: 0, 'Média': 1, Baixa: 2 }

const dateLabel = computed(() => {
  const text = today.value.toLocaleDateString('pt-PT', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })

  return text.charAt(0).toUpperCase() + text.slice(1)
})

const dateTimeLabel = formatarDataHora(new Date())

const countByStatus = (status: TaskStatus) => tasks.filter((t) => t.status === status).length

const activeProjects = computed(() => projects.filter((p) => p.status === 'Ativo'))
const finishedProjects = computed(() => projects.filter((p) => p.status === 'Concluído').length)
// Estes valores têm de ser computed porque a API carrega os dados depois do onMounted.
const inProgress = computed(() => countByStatus('Em curso'))
const todo = computed(() => countByStatus('Por fazer'))
const done = computed(() => countByStatus('Concluída'))
const blocked = computed(() => countByStatus('Bloqueada'))

const completionRate = computed(() =>
  tasks.length ? Math.round((done.value / tasks.length) * 100) : 0
)

const kpiCards = computed(() => [
  { label: 'Projetos ativos', value: activeProjects.value.length, hint: '', tone: 'indigo', icon: 'folder', trend: 'up' },
  { label: 'Em curso', value: inProgress.value, hint: '', tone: 'blue', icon: 'bolt', trend: 'up' },
  { label: 'Concluídas', value: done.value, hint: completionRate.value + '% de conclusão', tone: 'green', icon: 'check', progress: completionRate.value, trend: 'up' },
  { label: 'Bloqueadas', value: blocked.value, hint: blocked.value > 0 ? 'Requer ação' : '', tone: 'red', icon: 'alert', trend: blocked.value > 0 ? 'down' : 'none' }
])

const weekly = computed(() =>
  Array.from({ length: 7 }, (_, i) => {
    const date = addDays(today.value, i - 6)
    const iso = toISODay(date)
    return {
      label: date.toLocaleDateString('pt-PT', { weekday: 'short' }).replace('.', ''),
      value: tasks.filter((t) => {
  if (!t.completedAt) return false

  return t.completedAt.slice(0, 10) === iso
}).length
    }
  })
)

const weeklyTotal = computed(() => weekly.value.reduce((s, v) => s + v.value, 0))

const statusSegments = computed(() =>
  STATUS_ORDER.map((status) => ({ label: status, value: countByStatus(status), color: STATUS_COLORS[status] }))
)

const openTasks = computed(() => tasks.filter((t) => t.status !== 'Concluída'))

function daysUntil(task: DashboardTask): number {
  if (!task.dueDate) return Number.POSITIVE_INFINITY
  return diffInDays(today.value, parseISODay(task.dueDate))
}

function dueLabel(task: DashboardTask): string {
  if (!task.dueDate) return 'Sem prazo'

  const days = daysUntil(task)

  if (days < 0) {
    return `Atrasada há ${Math.abs(days)} ${Math.abs(days) === 1 ? 'dia' : 'dias'}`
  }

  if (days === 0) return 'Hoje'
  if (days === 1) return 'Amanhã'

  return `Em ${days} dias`
}

function dueTone(task: DashboardTask): 'late' | 'soon' | 'ok' {
  if (!task.dueDate) return 'ok'

  const days = daysUntil(task)

  if (days < 0) return 'late'
  if (days <= 3) return 'soon'

  return 'ok'
}

const attention = computed(() =>
  openTasks.value
    .map((t) => ({ task: t, tone: dueTone(t), days: daysUntil(t) }))
    .sort((a, b) => {
      const wa = PRIORITY_WEIGHT[a.task.priority]
      const wb = PRIORITY_WEIGHT[b.task.priority]
      if (wa !== wb) return wa - wb
      return a.days - b.days
    })
    .slice(0, 6)
)

const projectsWithProgress = computed(() =>
  activeProjects.value.map((p) => {
    const ptasks = tasks.filter((t) => t.project === p.name)
    const pdone = ptasks.filter((t) => t.status === 'Concluída').length
    const progress = ptasks.length ? Math.round((pdone / ptasks.length) * 100) : 0
    const members = Array.from(new Set(ptasks.map((t) => t.responsible)))
    return { ...p, progress, members }
  })
)
</script>

<template>
  <main class="dashboard">
      <p v-if="carregando" role="status">
          A carregar dados do Dashboard...
      </p>

      <p v-if="erro" class="error-message" role="alert">
          {{ erro }}
      </p>
    <header class="page-hero animate-in" style="animation-delay: 60ms">
  <div class="hero-kicker">
    <span class="dot" aria-hidden="true"></span>
    TaskFlow <span class="hero-separator">/</span> Dashboard
  </div>

  <h1>Visão geral</h1>

  <p class="hero-description">
    Acompanhe os seus projetos, monitorize as tarefas e consulte os prazos
    mais importantes num único lugar.
  </p>

  <div class="hero-meta">
    <div class="hero-date-group">
    <span class="hero-date">
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <rect x="3" y="5" width="18" height="16" rx="2"></rect>
        <path d="M16 3v4M8 3v4M3 10h18"></path>
      </svg>
      {{ dateLabel }}
    </span>

    <span class="hero-time">
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <circle cx="12" cy="12" r="9"></circle>
        <path d="M12 7v5l3 2"></path>
      </svg>
      {{ dateTimeLabel }}
    </span>
  </div>

  <NuxtLink to="/projects" class="btn btn-ghost">
    Ver todos os projetos
  </NuxtLink>
  </div>
</header>

    
<div class="kpi-grid">
  <article
    v-for="(card, i) in kpiCards"
    :key="card.label"
    class="kpi-card"
    :class="`kpi-${card.tone}`"
    :style="{ animationDelay: `${120 + i * 70}ms` }"
  >
    <div class="kpi-top">
      <div class="kpi-icon">
        <svg v-if="card.tone === 'indigo'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
          <path d="M3 7a2 2 0 0 1 2-2h5l2 2h7a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
          <path d="M3 9h18"/>
        </svg>
        <svg v-else-if="card.tone === 'blue'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
          <path d="m13 2-9 12h7l-1 8 10-13h-7z"/>
        </svg>
        <svg v-else-if="card.tone === 'green'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <path d="m5 12 4 4L19 6"/>
        </svg>
        <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
          <circle cx="12" cy="12" r="9"/>
          <path d="M12 7v6m0 4h.01"/>
        </svg>
      </div>
      <span class="kpi-label">{{ card.label }}</span>
    </div>

    <div class="kpi-value">{{ card.value }}</div>

    <div class="kpi-bottom">
      <span>{{ card.hint || 'Dados atuais do projeto' }}</span>
    </div>

    <div
      v-if="card.progress !== undefined"
      class="kpi-progress"
      role="progressbar"
      :aria-valuenow="card.progress"
      aria-valuemin="0"
      aria-valuemax="100"
    >
      <span :style="{ width: `${card.progress}%` }"></span>
    </div>
  </article>
</div>


    <div class="grid-2">
      <div class="content-card animate-in" style="animation-delay: 240ms">
        <div class="section-header">
          <div>
            <h2>Conclusões da semana</h2>
            <p>{{ weeklyTotal }} tarefa{{ weeklyTotal !== 1 ? 's' : '' }} nos últimos 7 dias</p>
          </div>
        </div>
        <DashboardBarChart :data="weekly" ::highlight="6" unit="tarefas" />
      </div>

      <div class="content-card animate-in" style="animation-delay: 300ms">
        <div class="section-header">
          <div>
            <h2>Estado das tarefas</h2>
            <p>{{ tasks.length }} tarefa{{ tasks.length !== 1 ? 's' : '' }} no total</p>
          </div>
        </div>
        <DashboardDonutChart
          :segments="statusSegments"
          :center-value="done"
          center-label="Concluídas"
        />
      </div>
    </div>
    <div class="content-card animate-in" style="animation-delay: 360ms">
      <div class="section-header section-actions">
        <div>
          <h2>Precisam de atenção</h2>
          <p>Prazos críticos e tarefas bloqueadas</p>
        </div>
      </div>
      <ul class="task-list">
        <li
          v-for="(item, i) in attention"
          :key="item.task.id"
          class="animate-in"
          :style="{ animationDelay: 420 + i * 60 + 'ms' }"
        >
          <TaskCard :task="item.task" />
        </li>
        <li v-if="attention.length === 0" class="task-row empty animate-in" style="animation-delay: 420ms">
          <div class="empty-state" style="padding: 24px 14px;">
            <div class="icon">✓</div>
            <h3>Sem tarefas críticas</h3>
            <p>Está em dia com os prazos.</p>
          </div>
        </li>
      </ul>
    </div>

    <div class="section-header section-actions" style="margin-top: 28px;">
        <div>
            <h2>Projetos ativos</h2>
              <p>{{ activeProjects?.length ?? 0 }} projeto{{ activeProjects?.length !== 1 ? 's' : '' }} em curso</p>
        </div>
    </div>
    <div class="projects-grid">
      <ProjectCard
        v-for="(p, i) in projectsWithProgress"
        :key="p.id"
        :project="p"
        :progress="p.progress"
        :members="p.members"
        class="animate-in"
        :style="{ animationDelay: 500 + i * 60 + 'ms' }"
      />
    </div>
  </main>
</template>


<style scoped>
.dashboard {
  --tf-bg: #f1f5fc;
  --tf-border: #e2e9f5;
  --tf-text: #172b4d;
  --tf-muted: #71819b;

  min-height: 100vh;
  padding: 28px;
  color: var(--tf-text);
  background: var(--tf-bg);
  border-radius: 18px;
  box-sizing: border-box;
}

/* .page-hero {
  padding: 10px 4px 28px;
}

.page-hero h1 {
  margin: 0 0 10px;
  color: #172b4d;
  font-size: clamp(26px, 3vw, 36px);
  font-weight: 800;
  letter-spacing: -0.04em;
} */

.page-hero > p {
  max-width: 650px;
  color: var(--tf-muted);
  font-size: 14px;
  line-height: 1.8;
}

.hero-kicker {
  display: flex;
  align-items: center;
  gap: 9px;
  margin-bottom: 12px;
  color: #4568c7;
  font-size: 13px;
  font-weight: 700;
}

.hero-kicker .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #5278f5;
  box-shadow: 0 0 0 4px #dce6ff;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 20px;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 42px;
  padding: 0 18px;
  border: 1px solid #dce5f5;
  border-radius: 11px;
  font-size: 13px;
  font-weight: 700;
  text-decoration: none;
}

.btn-primary {
  color: #fff;
  background: #4169ed;
  border-color: #4169ed;
}

.btn-ghost {
  color: #3454a4;
  background: #fff;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.kpi-card {
  min-width: 0;
  padding: 22px;
  background: #fff;
  border: 1px solid #e2e9f5;
  border-radius: 17px;
  box-shadow: 0 5px 18px rgb(36 59 99 / 5%);
  animation: tf-appear .4s ease both;
  transition: transform .2s, box-shadow .2s;
}

.kpi-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 12px 26px rgb(36 59 99 / 9%);
}

.kpi-top {
  display: flex;
  align-items: center;
  gap: 12px;
}

.kpi-icon {
  display: grid;
  flex: 0 0 44px;
  width: 44px;
  height: 44px;
  place-items: center;
  border-radius: 14px;
}

.kpi-icon svg {
  width: 23px;
  height: 23px;
}

.kpi-label {
  color: #5b6c86;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.5;
}

.kpi-value {
  margin: 20px 0 10px;
  color: #1c3155;
  font-size: 36px;
  font-weight: 800;
  letter-spacing: -0.04em;
}

.kpi-bottom {
  min-height: 18px;
  color: #7d8ba2;
  font-size: 11px;
  line-height: 1.5;
}

.kpi-progress {
  height: 5px;
  margin-top: 17px;
  overflow: hidden;
  background: #e7edf5;
  border-radius: 99px;
}

.kpi-progress span {
  display: block;
  height: 100%;
  background: #19a879;
  border-radius: inherit;
  transition: width .4s ease;
}

.kpi-indigo {
  background: linear-gradient(145deg, #fff 55%, #f0f2ff);
  border-color: #dce3ff;
}
.kpi-indigo .kpi-icon {
  color: #6254df;
  background: #e9e7ff;
}

.kpi-blue {
  background: linear-gradient(145deg, #fff 55%, #edf7ff);
  border-color: #d8eaff;
}
.kpi-blue .kpi-icon {
  color: #2378e8;
  background: #dceeff;
}

.kpi-green {
  background: linear-gradient(145deg, #fff 55%, #edfbf4);
  border-color: #d6f1e3;
}
.kpi-green .kpi-icon {
  color: #11996b;
  background: #d8f6e7;
}

.kpi-red {
  background: linear-gradient(145deg, #fff 55%, #fff0f0);
  border-color: #f5dddd;
}
.kpi-red .kpi-icon {
  color: #e34452;
  background: #ffe0e2;
}

.grid-2 {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.content-card {
  min-width: 0;
  padding: 24px;
  overflow: hidden;
  background: #fff;
  border: 1px solid var(--tf-border);
  border-radius: 17px;
  box-shadow: 0 5px 18px rgb(36 59 99 / 4%);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 22px;
}

.section-header h2 {
  margin: 0;
  color: #203557;
  font-size: 16px;
  font-weight: 750;
}

.section-header p {
  margin-top: 7px;
  color: var(--tf-muted);
  font-size: 12px;
  line-height: 1.6;
}

.section-actions {
  margin-bottom: 16px;
}

.task-list {
  display: grid;
  gap: 10px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.task-list > li {
  min-width: 0;
}

.projects-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.error-message {
  margin-bottom: 18px;
  padding: 14px 16px;
  color: #b42332;
  background: #fff0f0;
  border: 1px solid #f6d1d5;
  border-radius: 12px;
}

@keyframes tf-appear {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 1100px) {
  .dashboard { padding: 22px; }
  .kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .projects-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (max-width: 700px) {
  .dashboard { padding: 15px; }
  .grid-2, .projects-grid { grid-template-columns: minmax(0, 1fr); }
  .kpi-card { padding: 16px; }
  .content-card { padding: 18px; }
  .page-hero { padding-top: 8px; }
}

@media (max-width: 390px) {
  .kpi-grid { grid-template-columns: minmax(0, 1fr); }
  .kpi-top { align-items: center; }
}

@media (prefers-reduced-motion: reduce) {
  .kpi-card, .btn { animation: none; transition: none; }
}
.page-hero {
  padding: 12px 4px 30px;
}

.page-hero h1 {
  margin: 0 0 12px;
  color: #172b4d;
  font-size: clamp(28px, 3vw, 36px);
  font-weight: 800;
  line-height: 1.2;
  letter-spacing: -0.04em;
}

.hero-kicker {
  display: flex;
  align-items: center;
  gap: 9px;
  margin-bottom: 14px;
  color: #4568c7;
  font-size: 13px;
  font-weight: 700;
}

.hero-separator {
  color: #a2aec2;
}

.hero-description {
  max-width: 620px;
  margin: 0;
  color: #71819b;
  font-size: 14px;
  line-height: 1.8;
}

.hero-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
  margin-top: 22px;
}

.hero-date-group {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 18px;
}

.hero-date,
.hero-time {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  color: #526580;
  font-size: 13px;
  font-weight: 600;
}

.hero-date svg,
.hero-time svg {
  width: 18px;
  height: 18px;
  fill: none;
  stroke: #5278f5;
  stroke-width: 1.7;
  stroke-linecap: round;
  stroke-linejoin: round;
  flex-shrink: 0;
}

@media (max-width: 600px) {
  .hero-meta {
    align-items: flex-start;
    flex-direction: column;
  }

  .hero-date-group {
    align-items: flex-start;
    flex-direction: column;
    gap: 10px;
  }

  .hero-description {
    font-size: 13px;
  }
}

.hero-separator {
  color: #a2aec2;
}

.hero-description {
  max-width: 620px;
  margin: 0;
  color: #71819b;
  font-size: 14px;
  line-height: 1.8;
}

.hero-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
  margin-top: 22px;
}

.hero-date {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  color: #526580;
  font-size: 13px;
  font-weight: 600;
}

.hero-date svg {
  width: 18px;
  height: 18px;
  fill: none;
  stroke: #5278f5;
  stroke-width: 1.7;
  stroke-linecap: round;
  stroke-linejoin: round;
  flex-shrink: 0;
}

@media (max-width: 600px) {
  .hero-meta {
    align-items: flex-start;
    flex-direction: column;
  }

  .hero-description {
    font-size: 13px;
  }
}


/* Cabeçalho: fundo claro e contraste consistente com o restante do dashboard. */
.page-hero {
  padding: 24px 26px;
  margin-bottom: 24px;
  color: #172b4d;
  background: #ffffff;
  border: 1px solid #e2e9f5;
  border-radius: 18px;
  box-shadow: 0 5px 18px rgb(36 59 99 / 4%);
}

.page-hero h1 {
  margin: 0 0 10px;
  color: #172b4d;
  font-size: clamp(28px, 3vw, 36px);
  font-weight: 800;
  line-height: 1.2;
  letter-spacing: -0.04em;
}

.page-hero .hero-description {
  max-width: 650px;
  margin: 0;
  color: #71819b;
  font-size: 14px;
  line-height: 1.8;
}

.page-hero .hero-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
  margin-top: 22px;
}

.page-hero .hero-date-group {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 18px;
}

.page-hero .hero-date,
.page-hero .hero-time {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  color: #526580;
  font-size: 13px;
  font-weight: 600;
}

.page-hero .hero-date svg,
.page-hero .hero-time svg {
  width: 18px;
  height: 18px;
  fill: none;
  stroke: #5278f5;
  stroke-width: 1.7;
  stroke-linecap: round;
  stroke-linejoin: round;
  flex-shrink: 0;
}

@media (max-width: 600px) {
  .page-hero {
    padding: 20px 16px;
  }

  .page-hero .hero-meta,
  .page-hero .hero-date-group {
    align-items: flex-start;
    flex-direction: column;
    gap: 10px;
  }
}

</style>
