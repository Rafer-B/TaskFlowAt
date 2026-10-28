<script setup lang="ts">
import { computed } from 'vue'
import type { DashboardTask, TaskPriority, TaskStatus } from '~/composables/useDashboardData'
import { toISODay, addDays, parseISODay, diffInDays } from '~/utils/dates'

const todayISO = useState('dashboard-today', () => toISODay(new Date()))
const today = computed(() => parseISODay(todayISO.value))

const { projects, tasks } = useDashboardData(today.value)

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
    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
  })
  return text.charAt(0).toUpperCase() + text.slice(1)
})

const countByStatus = (status: TaskStatus) => tasks.filter((t) => t.status === status).length

const activeProjects = computed(() => projects.filter((p) => p.status === 'Ativo'))
const finishedProjects = computed(() => projects.filter((p) => p.status === 'Concluído').length)
const inProgress = countByStatus('Em curso')
const todo = countByStatus('Por fazer')
const done = countByStatus('Concluída')
const blocked = countByStatus('Bloqueada')

const completionRate = computed(() => tasks.length ? Math.round((done / tasks.length) * 100) : 0)

const kpiCards = computed(() => [
  { label: 'Projetos ativos', value: activeProjects.value.length, hint: '', tone: 'indigo', icon: 'folder', trend: 'up' },
  { label: 'Em curso', value: inProgress, hint: '', tone: 'blue', icon: 'bolt', trend: 'up' },
  { label: 'Concluídas', value: done, hint: completionRate.value + '% de conclusão', tone: 'green', icon: 'check', progress: completionRate.value, trend: 'up' },
  { label: 'Bloqueadas', value: blocked, hint: blocked > 0 ? 'Requer ação' : '', tone: 'red', icon: 'alert', trend: blocked > 0 ? 'down' : 'none' }
])

const weekly = computed(() =>
  Array.from({ length: 7 }, (_, i) => {
    const date = addDays(today.value, i - 6)
    const iso = toISODay(date)
    return {
      label: date.toLocaleDateString('pt-PT', { weekday: 'short' }).replace('.', ''),
      value: tasks.filter((t) => t.completedAt === iso).length
    }
  })
)

const weeklyTotal = computed(() => weekly.value.reduce((s, v) => s + v.value, 0))

const statusSegments = computed(() =>
  STATUS_ORDER.map((status) => ({ label: status, value: countByStatus(status), color: STATUS_COLORS[status] }))
)

const openTasks = computed(() => tasks.filter((t) => t.status !== 'Concluída'))

function daysUntil(task: DashboardTask): number {
  return diffInDays(today.value, parseISODay(task.dueDate))
}

function dueLabel(task: DashboardTask): string {
  const days = daysUntil(task)
  if (days < 0) return 'Atrasada há ' + Math.abs(days) + ' ' + (Math.abs(days) === 1 ? 'dia' : 'dias')
  if (days === 0) return 'Hoje'
  if (days === 1) return 'Amanhã'
  return 'Em ' + days + ' dias'
}

function dueTone(task: DashboardTask): 'late' | 'soon' | 'ok' {
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
  projects.map((p) => {
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
    <header class="page-hero animate-in" style="animation-delay: 60ms">
      <div class="hero-kicker"><span class="dot" aria-hidden="true"></span> TaskFlow · Dashboard</div>
      <h1>{{ dateLabel }}</h1>
      <p>Visão geral dos seus projetos e tarefas. Acompanhe o progresso, os prazos e o que requer a sua atenção.</p>
      <div class="hero-actions">
        <button class="btn btn-primary">Nova tarefa</button>
        <button class="btn btn-ghost">Ver todos os projetos</button>
      </div>
    </header>

    <div class="kpi-grid">
      <DashboardStatCard
        v-for="(card, i) in kpiCards"
        :key="i"
        :label="card.label"
        :value="card.value"
        :hint="card.hint"
        :tone="card.tone"
        :icon="card.icon"
        :progress="card.progress"
        :trend="card.trend"
        class="animate-in"
        :style="{ animationDelay: 120 + i * 70 + 'ms' }"
      />
    </div>

    <div class="grid-2">
      <div class="content-card animate-in" style="animation-delay: 240ms">
        <div class="section-header">
          <div>
            <h2>Conclusões da semana</h2>
            <p>{{ weeklyTotal }} tarefa{{ weeklyTotal !== 1 ? 's' : '' }} nos últimos 7 dias</p>
          </div>
        </div>
        <DashboardBarChart :data="weekly" highlight="6" unit="tarefas" />
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
.grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 28px;
}

.projects-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

@media (max-width: 900px) {
  .grid-2 { grid-template-columns: 1fr; }
  .projects-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (max-width: 600px) {
  .projects-grid { grid-template-columns: 1fr; }
}
</style>