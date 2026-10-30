
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
  users,
  carregando,
  erro,
  atualizar,
} = useDashboardData(today.value)

// Cores e ordem dos estados das tarefas.
const STATUS_COLORS: Record<TaskStatus, string> = {
  'Por fazer': '#94a3b8',
  'Em curso': '#3b82f6',
  'Concluída': '#22c55e',
  'Bloqueada': '#ef4444',
}

const STATUS_ORDER: TaskStatus[] = [
  'Em curso',
  'Por fazer',
  'Bloqueada',
  'Concluída',
]

const PRIORITY_WEIGHT: Record<TaskPriority, number> = {
  Alta: 0,
  Média: 1,
  Baixa: 2,
}

// Data apresentada no cabeçalho.
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

// Contagem de tarefas por estado.
const countByStatus = (status: TaskStatus) =>
  tasks.filter((t) => t.status === status).length

// Indicadores de projetos.
const activeProjects = computed(() =>
  projects.filter((p) => p.status === 'Ativo'),
)

const finishedProjects = computed(() =>
  projects.filter((p) => p.status === 'Concluído').length,
)

const archivedProjects = computed(() =>
  projects.filter((p) => p.status === 'Arquivado').length,
)

const totalProjects = computed(() => projects.length)

// Indicadores de utilizadores.
const totalUsers = computed(() => users.length)

const activeUsers = computed(() =>
  users.filter((user) => user.isActive).length,
)

const inactiveUsers = computed(() =>
  users.filter((user) => !user.isActive).length,
)

// Indicadores de tarefas.
const totalTasks = computed(() => tasks.length)

const inProgress = computed(() => countByStatus('Em curso'))
const todo = computed(() => countByStatus('Por fazer'))
const done = computed(() => countByStatus('Concluída'))
const blocked = computed(() => countByStatus('Bloqueada'))

// Percentagem global de tarefas concluídas.
const completionRate = computed(() =>
  tasks.length
    ? Math.round((done.value / tasks.length) * 100)
    : 0,
)

// Cartões de indicadores globais.
const kpiCards = computed(() => [
  {
    label: 'Total de projetos',
    value: totalProjects.value,
    hint: `${activeProjects.value.length} ativos · ${finishedProjects.value} concluídos · ${archivedProjects.value} arquivados`,
    tone: 'indigo',
    icon: 'folder',
  },
  {
    label: 'Utilizadores',
    value: totalUsers.value,
    hint: `${activeUsers.value} ativos · ${inactiveUsers.value} inativos`,
    tone: 'blue',
    icon: 'users',
  },
  {
    label: 'Total de tarefas',
    value: totalTasks.value,
    hint: `${todo.value} por fazer · ${inProgress.value} em curso`,
    tone: 'green',
    icon: 'check',
  },
  {
    label: 'Tarefas bloqueadas',
    value: blocked.value,
    hint: blocked.value > 0
      ? 'Requer atenção'
      : 'Sem tarefas bloqueadas',
    tone: 'red',
    icon: 'alert',
  },
])

// Tarefas concluídas nos últimos sete dias.
const weekly = computed(() =>
  Array.from({ length: 7 }, (_, i) => {
    const date = addDays(today.value, i - 6)
    const iso = toISODay(date)

    return {
      label: date
        .toLocaleDateString('pt-PT', { weekday: 'short' })
        .replace('.', ''),

      value: tasks.filter((t) => {
        if (!t.completedAt) return false

        return t.completedAt.slice(0, 10) === iso
      }).length,
    }
  }),
)

const weeklyTotal = computed(() =>
  weekly.value.reduce((sum, item) => sum + item.value, 0),
)

// Distribuição das tarefas por estado.
const statusSegments = computed(() =>
  STATUS_ORDER.map((status) => ({
    label: status,
    value: countByStatus(status),
    color: STATUS_COLORS[status],
  })),
)

// Tarefas que ainda não estão concluídas.
const openTasks = computed(() =>
  tasks.filter((t) => t.status !== 'Concluída'),
)

// Calcula os dias até ao prazo de uma tarefa.
function daysUntil(task: DashboardTask): number {
  if (!task.dueDate) return Number.POSITIVE_INFINITY

  return diffInDays(
    today.value,
    parseISODay(task.dueDate),
  )
}

// Texto apresentado relativamente ao prazo.
function dueLabel(task: DashboardTask): string {
  if (!task.dueDate) return 'Sem prazo'

  const days = daysUntil(task)

  if (days < 0) {
    return `Atrasada há ${Math.abs(days)} ${
      Math.abs(days) === 1 ? 'dia' : 'dias'
    }`
  }

  if (days === 0) return 'Hoje'
  if (days === 1) return 'Amanhã'

  return `Em ${days} dias`
}

// Cor do prazo.
function dueTone(task: DashboardTask): 'late' | 'soon' | 'ok' {
  if (!task.dueDate) return 'ok'

  const days = daysUntil(task)

  if (days < 0) return 'late'
  if (days <= 3) return 'soon'

  return 'ok'
}

// Lista de tarefas que precisam de atenção.
const attention = computed(() =>
  openTasks.value
    .map((task) => ({
      task,
      tone: dueTone(task),
      days: daysUntil(task),
    }))
    .sort((a, b) => {
      const wa = PRIORITY_WEIGHT[a.task.priority]
      const wb = PRIORITY_WEIGHT[b.task.priority]

      if (wa !== wb) return wa - wb

      return a.days - b.days
    })
    .slice(0, 6),
)

// Projetos ativos com progresso calculado.
const projectsWithProgress = computed(() =>
  activeProjects.value.map((project) => {
    const projectTasks = tasks.filter(
      (task) => task.project === project.name,
    )

    const completedTasks = projectTasks.filter(
      (task) => task.status === 'Concluída',
    ).length

    const progress = projectTasks.length
      ? Math.round((completedTasks / projectTasks.length) * 100)
      : 0

    const members = Array.from(
      new Set(projectTasks.map((task) => task.responsible)),
    )

    return {
      ...project,
      progress,
      members,
    }
  }),
)
</script>

<template>
  <main class="dashboard">
    <!-- Estado de carregamento -->
    <p v-if="carregando" class="loading-message" role="status">
      A carregar dados do Dashboard...
    </p>

    <!-- Mensagem de erro -->
    <div v-if="erro" class="error-message" role="alert">
      <p>{{ erro }}</p>

      <button
        type="button"
        class="btn btn-ghost"
        @click="atualizar"
      >
        Tentar novamente
      </button>
    </div>

    <!-- Cabeçalho -->
    <header class="page-hero animate-in" style="animation-delay: 60ms">
      <div class="hero-layout">
        <div class="hero-copy">
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
              <span aria-hidden="true">→</span>
            </NuxtLink>
          </div>
        </div>

        <aside class="hero-completion" aria-label="Progresso geral das tarefas">
          <div class="completion-ring">
            <svg viewBox="0 0 72 72" aria-hidden="true">
              <circle class="ring-track" cx="36" cy="36" r="30" />
              <circle
                class="ring-progress"
                cx="36"
                cy="36"
                r="30"
                :stroke-dasharray="`${completionRate * 1.885} 188.5`"
              />
            </svg>
            <strong>{{ completionRate }}%</strong>
          </div>
          <div>
            <span class="completion-label">Progresso geral</span>
            <strong class="completion-value">
              {{ done }} de {{ totalTasks }} tarefas
            </strong>
            <span class="completion-caption">concluídas até agora</span>
          </div>
        </aside>
      </div>
    </header>

    <!-- Indicadores globais -->
    <section class="kpi-grid" aria-label="Indicadores globais">
      <article
        v-for="(card, i) in kpiCards"
        :key="card.label"
        class="kpi-card"
        :class="`kpi-${card.tone}`"
        :style="{ animationDelay: `${120 + i * 70}ms` }"
      >
        <div class="kpi-top">
          <div class="kpi-icon">
            <!-- Projetos -->
            <svg
              v-if="card.icon === 'folder'"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="1.8"
            >
              <path d="M3 7a2 2 0 0 1 2-2h5l2 2h7a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
              <path d="M3 9h18" />
            </svg>

            <!-- Utilizadores -->
            <svg
              v-else-if="card.icon === 'users'"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="1.8"
            >
              <circle cx="9" cy="8" r="3" />
              <path d="M3 20v-1a6 6 0 0 1 12 0v1" />
              <path d="M16 5.5a3 3 0 0 1 0 5.8" />
              <path d="M18 14a5 5 0 0 1 3 5v1" />
            </svg>

            <!-- Tarefas -->
            <svg
              v-else-if="card.icon === 'check'"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2.5"
            >
              <path d="m5 12 4 4L19 6" />
            </svg>

            <!-- Bloqueadas -->
            <svg
              v-else
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="1.8"
            >
              <circle cx="12" cy="12" r="9" />
              <path d="M12 7v6m0 4h.01" />
            </svg>
          </div>

          <span class="kpi-label">
            {{ card.label }}
          </span>
        </div>

        <div class="kpi-value">
          {{ card.value }}
        </div>

        <div class="kpi-bottom">
          <span>{{ card.hint }}</span>
        </div>

        <div
          v-if="'progress' in card && card.progress !== undefined"
          class="kpi-progress"
          role="progressbar"
          :aria-valuenow="card.progress"
          aria-valuemin="0"
          aria-valuemax="100"
        >
          <span :style="{ width: `${card.progress}%` }"></span>
        </div>
      </article>
    </section>

    <!-- Gráficos -->
    <section class="grid-2">
      <div class="content-card animate-in" style="animation-delay: 240ms">
        <div class="section-header">
          <div>
            <h2>Conclusões da semana</h2>
            <p>
              {{ weeklyTotal }}
              tarefa{{ weeklyTotal !== 1 ? 's' : '' }}
              nos últimos 7 dias
            </p>
          </div>
        </div>

        <DashboardBarChart
          :data="weekly"
          :highlight="6"
          unit="tarefas"
        />
      </div>

      <div class="content-card animate-in" style="animation-delay: 300ms">
        <div class="section-header">
          <div>
            <h2>Estado das tarefas</h2>
            <p>
              {{ tasks.length }}
              tarefa{{ tasks.length !== 1 ? 's' : '' }}
              no total
            </p>
          </div>
        </div>

        <DashboardDonutChart
          :segments="statusSegments"
          :center-value="done"
          center-label="Concluídas"
        />
      </div>
    </section>

    <!-- Tarefas que precisam de atenção -->
    <section
      class="content-card animate-in"
      style="animation-delay: 360ms"
    >
      <div class="section-header section-actions">
        <div>
          <h2>Precisam de atenção</h2>
          <p>Prazos críticos e tarefas bloqueadas</p>
        </div>

        <NuxtLink to="/tasks" class="btn btn-ghost">
          Ver tarefas
        </NuxtLink>
      </div>

      <ul class="task-list">
        <li
          v-for="(item, i) in attention"
          :key="item.task.id"
          class="animate-in"
          :style="{ animationDelay: `${420 + i * 60}ms` }"
        >
          <TaskCard :task="item.task" />
        </li>

        <li
          v-if="attention.length === 0"
          class="task-row empty animate-in"
          style="animation-delay: 420ms"
        >
          <div class="empty-state" style="padding: 24px 14px;">
            <div class="icon">✓</div>
            <h3>Sem tarefas críticas</h3>
            <p>Está em dia com os prazos.</p>
          </div>
        </li>
      </ul>
    </section>

    <!-- Projetos ativos -->
    <section class="projects-section">
      <div class="section-header section-actions">
        <div>
          <h2>Projetos ativos</h2>
          <p>
            {{ activeProjects.length }}
            projeto{{ activeProjects.length !== 1 ? 's' : '' }}
            em curso
          </p>
        </div>

        <NuxtLink to="/projects" class="btn btn-ghost">
          Ver projetos
        </NuxtLink>
      </div>

      <div class="projects-grid">
        <ProjectCard
          v-for="(project, i) in projectsWithProgress"
          :key="project.id"
          :project="project"
          :progress="project.progress"
          :members="project.members"
          class="animate-in"
          :style="{ animationDelay: `${500 + i * 60}ms` }"
        />

        <div
          v-if="projectsWithProgress.length === 0"
          class="content-card empty-projects"
        >
          <div class="empty-state">
            <div class="icon">📁</div>
            <h3>Sem projetos ativos</h3>
            <p>Quando criares projetos, estes serão apresentados aqui.</p>
            <NuxtLink to="/projects" class="btn btn-ghost">
              Consultar projetos
            </NuxtLink>
          </div>
        </div>
      </div>
    </section>
  </main>
</template>

<style scoped>
.dashboard {
  --tf-border: #e8edf5;
  --tf-text: #172554;
  --tf-muted: #7a879d;
  min-height: 100vh;
  padding: 28px;
  color: var(--tf-text);
  background:
    radial-gradient(ellipse at 12% 0%, rgb(224 231 255 / 54%), transparent 34%),
    #f6f8fc;
  border-radius: 18px;
  box-sizing: border-box;
}

.loading-message {
  margin-bottom: 18px;
  padding: 14px 16px;
  color: #3454a4;
  background: #edf3ff;
  border: 1px solid #dce5f5;
  border-radius: 12px;
}

.error-message {
  margin-bottom: 18px;
  padding: 14px 16px;
  color: #b42332;
  background: #fff0f0;
  border: 1px solid #f6d1d5;
  border-radius: 12px;
}

.error-message p {
  margin: 0 0 12px;
}

.page-hero {
  position: relative;
  isolation: isolate;
  overflow: hidden;
  padding: 30px 34px;
  margin-bottom: 24px;
  color: #fff;
  background:
    radial-gradient(circle at 78% 12%, rgb(129 140 248 / 43%), transparent 29%),
    linear-gradient(118deg, #172554 0%, #312e81 58%, #4338ca 100%);
  border: 1px solid rgb(255 255 255 / 12%);
  border-radius: 22px;
  box-shadow: 0 18px 40px -24px rgb(49 46 129 / 62%);
}

.page-hero::after {
  position: absolute;
  z-index: -1;
  right: -72px;
  bottom: -180px;
  width: 410px;
  height: 410px;
  border: 1px solid rgb(255 255 255 / 9%);
  border-radius: 50%;
  box-shadow: 0 0 0 34px rgb(255 255 255 / 3%), 0 0 0 72px rgb(255 255 255 / 2%);
  content: '';
}

.hero-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 38px;
}

.hero-copy {
  min-width: 0;
}

.page-hero h1 {
  margin: 0 0 9px;
  color: #fff;
  font-size: clamp(28px, 3vw, 36px);
  font-weight: 800;
  line-height: 1.2;
  letter-spacing: -0.04em;
}

.hero-kicker {
  display: flex;
  align-items: center;
  gap: 9px;
  margin-bottom: 15px;
  color: #c7d2fe;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: .1em;
  text-transform: uppercase;
}

.hero-kicker .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #67e8f9;
  box-shadow: 0 0 0 4px rgb(103 232 249 / 15%), 0 0 15px rgb(103 232 249 / 70%);
}

.hero-separator {
  color: #818cf8;
}

.hero-description {
  max-width: 650px;
  margin: 0;
  color: #c7d2fe;
  font-size: 14px;
  line-height: 1.7;
}

.hero-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
  margin-top: 24px;
}

.hero-date-group {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.hero-date,
.hero-time {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  color: #e0e7ff;
  font-size: 12px;
  font-weight: 600;
}

.hero-date svg,
.hero-time svg {
  width: 16px;
  height: 16px;
  fill: none;
  stroke: #a5b4fc;
  stroke-width: 1.7;
  stroke-linecap: round;
  stroke-linejoin: round;
  flex-shrink: 0;
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
  cursor: pointer;
  transition: transform .2s ease, background .2s ease, border-color .2s ease;
}

.btn:hover {
  transform: translateY(-1px);
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

.page-hero .btn-ghost {
  gap: 10px;
  min-height: 40px;
  color: #fff;
  background: rgb(255 255 255 / 10%);
  border-color: rgb(255 255 255 / 22%);
  backdrop-filter: blur(8px);
}

.page-hero .btn-ghost:hover {
  background: rgb(255 255 255 / 18%);
}

.hero-completion {
  display: flex;
  align-items: center;
  gap: 16px;
  min-width: 240px;
  padding: 18px 20px;
  border: 1px solid rgb(255 255 255 / 16%);
  border-radius: 18px;
  background: rgb(255 255 255 / 9%);
  box-shadow: inset 0 1px 0 rgb(255 255 255 / 8%);
  backdrop-filter: blur(12px);
}

.completion-ring {
  position: relative;
  display: grid;
  flex: 0 0 68px;
  width: 68px;
  height: 68px;
  place-items: center;
}

.completion-ring svg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.completion-ring circle {
  fill: none;
  stroke-width: 5;
}

.ring-track {
  stroke: rgb(255 255 255 / 17%);
}

.ring-progress {
  stroke: #67e8f9;
  stroke-linecap: round;
  transition: stroke-dasharray .5s ease;
}

.completion-ring strong {
  color: #fff;
  font-size: 16px;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}

.hero-completion > div:last-child {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.completion-label {
  color: #c7d2fe;
  font-size: 11px;
  font-weight: 600;
}

.completion-value {
  color: #fff;
  font-size: 14px;
  font-weight: 750;
}

.completion-caption {
  color: #a5b4fc;
  font-size: 10px;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 24px;
}

.kpi-card {
  position: relative;
  overflow: hidden;
  min-width: 0;
  padding: 20px 21px;
  background: #fff;
  border: 1px solid var(--tf-border);
  border-radius: 18px;
  box-shadow: 0 5px 16px rgb(23 37 84 / 3%);
  animation: tf-appear .4s ease both;
  transition: transform .2s ease, box-shadow .2s ease, border-color .2s ease;
}

.kpi-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 14px 28px -16px rgb(23 37 84 / 28%);
  border-color: #d7def0;
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
  border-radius: 13px;
}

.kpi-icon svg {
  width: 23px;
  height: 23px;
}

.kpi-label {
  color: #697790;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.5;
}

.kpi-value {
  margin: 17px 0 8px;
  color: #1e2b50;
  font-size: 34px;
  font-weight: 800;
  letter-spacing: -0.04em;
  line-height: 1;
  font-variant-numeric: tabular-nums;
}

.kpi-bottom {
  min-height: 32px;
  color: #8490a4;
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
  background: linear-gradient(145deg, #fff 64%, #f3f2ff);
}

.kpi-indigo .kpi-icon {
  color: #6254df;
  background: #e9e7ff;
}

.kpi-blue {
  background: linear-gradient(145deg, #fff 64%, #eff7ff);
}

.kpi-blue .kpi-icon {
  color: #2378e8;
  background: #dceeff;
}

.kpi-green {
  background: linear-gradient(145deg, #fff 64%, #effbf5);
}

.kpi-green .kpi-icon {
  color: #11996b;
  background: #d8f6e7;
}

.kpi-red {
  background: linear-gradient(145deg, #fff 64%, #fff4f3);
}

.kpi-red .kpi-icon {
  color: #e34452;
  background: #ffe0e2;
}

.grid-2 {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.content-card {
  min-width: 0;
  padding: 22px;
  overflow: hidden;
  background: #fff;
  border: 1px solid var(--tf-border);
  border-radius: 19px;
  box-shadow: 0 5px 18px rgb(23 37 84 / 3%);
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
  color: #253354;
  font-size: 15px;
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

.projects-section {
  margin-top: 28px;
}

.projects-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.empty-projects {
  grid-column: 1 / -1;
}

.empty-state {
  padding: 24px 14px;
  text-align: center;
}

.empty-state .icon {
  margin-bottom: 10px;
  font-size: 28px;
}

.empty-state h3 {
  margin: 0 0 8px;
  color: #203557;
  font-size: 15px;
}

.empty-state p {
  margin: 0 0 16px;
  color: var(--tf-muted);
  font-size: 13px;
  line-height: 1.6;
}

@keyframes tf-appear {
  from {
    opacity: 0;
    transform: translateY(8px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 1100px) {
  .dashboard {
    padding: 22px;
  }

  .hero-layout {
    gap: 20px;
  }

  .kpi-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .projects-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 700px) {
  .dashboard {
    padding: 15px;
  }

  .hero-layout {
    grid-template-columns: 1fr;
  }

  .hero-completion {
    width: fit-content;
    min-width: 0;
  }

  .grid-2,
  .projects-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .kpi-card {
    padding: 16px;
  }

  .content-card {
    padding: 18px;
  }
}

@media (max-width: 600px) {
  .page-hero {
    padding: 23px 18px;
  }

  .hero-meta,
  .hero-date-group {
    align-items: flex-start;
    flex-direction: column;
    gap: 10px;
  }

  .hero-description {
    font-size: 13px;
  }

  .hero-meta {
    align-items: flex-start;
  }
}

@media (max-width: 390px) {
  .kpi-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .kpi-top {
    align-items: center;
  }
}

@media (prefers-reduced-motion: reduce) {
  .kpi-card,
  .btn {
    animation: none;
    transition: none;
  }
}
</style>
