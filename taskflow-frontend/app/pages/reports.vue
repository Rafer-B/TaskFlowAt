<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import type {
  DashboardProject,
  DashboardTask,
  TaskStatus,
} from '~/composables/useDashboardData'

import { formatarData, parseISODay, toISODay } from '~/utils/dates'

definePageMeta({
  layout: 'admin',
})

const todayISO = useState('dashboard-today', () => toISODay(new Date()))
const today = computed(() => parseISODay(todayISO.value))
const { projects, tasks, carregando, erro, atualizar } = useDashboardData(today.value)

const statusInfo: Array<{ label: TaskStatus; color: string }> = [
  { label: 'Por fazer', color: '#94a3b8' },
  { label: 'Em curso', color: '#3b82f6' },
  { label: 'Bloqueada', color: '#ef4444' },
  { label: 'Concluída', color: '#22c55e' },
]

const countByStatus = (status: TaskStatus) =>
  tasks.filter((task) => task.status === status).length

const completedTasks = computed(() => countByStatus('Concluída'))
const completionRate = computed(() =>
  tasks.length ? Math.round((completedTasks.value / tasks.length) * 100) : 0,
)

const overdueTasks = computed(() =>
  tasks.filter((task) =>
    task.status !== 'Concluída' &&
    task.dueDate !== null &&
    task.dueDate < todayISO.value,
  ).length,
)

const statusSegments = computed(() =>
  statusInfo.map((status) => ({
    ...status,
    value: countByStatus(status.label),
  })),
)

const projectReports = computed(() =>
  projects.map((project: DashboardProject) => {
    const projectTasks = tasks.filter((task) => task.project === project.name)
    const total = projectTasks.length
    const completed = projectTasks.filter(
      (task) => task.status === 'Concluída',
    ).length

    return {
      ...project,
      total,
      completed,
      blocked: projectTasks.filter((task) => task.status === 'Bloqueada').length,
      overdue: projectTasks.filter(isOverdue).length,
      progress: total ? Math.round((completed / total) * 100) : 0,
    }
  }).sort((a, b) => b.total - a.total || a.name.localeCompare(b.name, 'pt-PT')),
)

const generatedAt = ref('')
const activeProjectCount = computed(() =>
  projects.filter((project) => project.status === 'Ativo').length,
)

watch([carregando, erro], ([isLoading, loadError]) => {
  if (!isLoading && !loadError) {
    generatedAt.value = new Intl.DateTimeFormat('pt-PT', {
    dateStyle: 'long',
    timeStyle: 'short',
    }).format(new Date())
  }
})

function printReport(): void {
  window.print()
}

function isOverdue(task: DashboardTask): boolean {
  return task.status !== 'Concluída' &&
    task.dueDate !== null &&
    task.dueDate < todayISO.value
}

function csvCell(value: string | number): string {
  const text = String(value)
  const safeText = /^[=+\-@\t\r]/.test(text) ? `'${text}` : text
  return `"${safeText.replace(/"/g, '""')}"`
}

function exportCsv(): void {
  const headers = [
    'Projeto',
    'Tarefa',
    'Responsável',
    'Estado',
    'Prioridade',
    'Prazo',
    'Concluída em',
  ]
  const rows = tasks.map((task) => [
    task.project,
    task.title,
    task.responsible,
    task.status,
    task.priority,
    task.dueDate ? formatarData(task.dueDate) : 'Sem prazo',
    task.completedAt ? formatarData(task.completedAt) : '—',
  ])
  const content = [headers, ...rows]
    .map((row) => row.map(csvCell).join(';'))
    .join('\r\n')
  const blob = new Blob(['\uFEFF', content], {
    type: 'text/csv;charset=utf-8',
  })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `relatorio-taskflow-${todayISO.value}.csv`
  link.click()
  window.setTimeout(() => URL.revokeObjectURL(url), 1000)
}
</script>

<template>
  <main class="reports-page">
    <p v-if="carregando" class="loading-message" role="status">
      A carregar os dados do relatório...
    </p>

    <div v-if="erro" class="error-message" role="alert">
      <p>{{ erro }}</p>
      <button type="button" class="btn btn-ghost" @click="atualizar">
        Tentar novamente
      </button>
    </div>

    <header class="page-hero report-hero">
      <div class="hero-layout">
        <div class="hero-copy">
          <div class="hero-kicker">
            <span class="dot" aria-hidden="true"></span>
            TaskFlow <span class="hero-separator">/</span> Relatórios
          </div>
          <h1>Relatório geral</h1>
          <p>
            Consulte o estado dos projetos e tarefas e acompanhe o progresso
            do espaço de trabalho.
          </p>
          <p class="report-date">Dados atualizados em {{ generatedAt }}</p>
        </div>

        <div class="report-actions">
          <button type="button" class="btn btn-ghost" @click="atualizar">
            Atualizar dados
          </button>
          <button
            type="button"
            class="btn btn-ghost"
            :disabled="carregando"
            @click="exportCsv"
          >
            Exportar CSV
          </button>
          <button type="button" class="btn btn-ghost" @click="printReport">
            Imprimir
          </button>
        </div>
      </div>
    </header>

    <section class="report-kpis" aria-label="Indicadores do relatório">
      <article class="report-kpi">
        <span>Projetos</span>
        <strong>{{ projects.length }}</strong>
        <small>{{ activeProjectCount }} ativos</small>
      </article>
      <article class="report-kpi">
        <span>Tarefas</span>
        <strong>{{ tasks.length }}</strong>
        <small>{{ completedTasks }} concluídas</small>
      </article>
      <article class="report-kpi">
        <span>Conclusão</span>
        <strong>{{ completionRate }}%</strong>
        <small>das tarefas concluídas</small>
      </article>
      <article class="report-kpi" :class="{ 'report-kpi-alert': overdueTasks > 0 }">
        <span>Tarefas em atraso</span>
        <strong>{{ overdueTasks }}</strong>
        <small>com prazo ultrapassado e não concluídas</small>
      </article>
    </section>

    <section class="report-grid">
      <article class="content-card report-card">
        <div class="section-header">
          <div>
            <h2>Tarefas por estado</h2>
            <p>Distribuição atual das tarefas registadas.</p>
          </div>
        </div>
        <DonutChart
          :segments="statusSegments"
          :center-value="tasks.length"
          center-label="tarefas"
        />
      </article>

      <article class="content-card report-card">
        <div class="section-header">
          <div>
            <h2>Resumo dos projetos</h2>
            <p>Progresso, bloqueios e prazos por projeto.</p>
          </div>
        </div>

        <div v-if="projectReports.length" class="project-report-list">
          <div
            v-for="project in projectReports"
            :key="project.id"
            class="project-report"
          >
            <div class="project-report-heading">
              <strong>{{ project.name }}</strong>
              <span>{{ project.progress }}%</span>
            </div>
            <div
              class="project-progress-track"
              role="progressbar"
              :aria-label="`Progresso de ${project.name}`"
              :aria-valuenow="project.progress"
              aria-valuemin="0"
              aria-valuemax="100"
            >
              <span :style="{ width: `${project.progress}%` }"></span>
            </div>
            <small>
              {{ project.completed }} / {{ project.total }} concluídas
              <template v-if="project.blocked"> · {{ project.blocked }} bloqueadas</template>
              <template v-if="project.overdue"> · {{ project.overdue }} em atraso</template>
            </small>
          </div>
        </div>
        <p v-else class="report-empty">Ainda não existem projetos para apresentar.</p>
      </article>
    </section>

    <section class="content-card report-card task-report-card">
      <div class="section-header">
        <div>
          <h2>Detalhe das tarefas</h2>
          <p>Lista completa incluída no ficheiro CSV exportado.</p>
        </div>
        <span class="task-count">{{ tasks.length }} tarefas</span>
      </div>

      <div v-if="tasks.length" class="report-table-wrap">
        <table class="report-table">
          <thead>
            <tr>
              <th>Projeto</th>
              <th>Tarefa</th>
              <th>Responsável</th>
              <th>Estado</th>
              <th>Prioridade</th>
              <th>Prazo</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="task in tasks" :key="task.id">
              <td>{{ task.project }}</td>
              <td class="task-name">{{ task.title }}</td>
              <td>{{ task.responsible }}</td>
              <td>
                <span class="task-status" :class="`status-${task.status.replaceAll(' ', '-').toLowerCase()}`">
                  {{ task.status }}
                </span>
              </td>
              <td>{{ task.priority }}</td>
              <td :class="{ 'overdue-date': isOverdue(task) }">
                {{ task.dueDate ? formatarData(task.dueDate) : 'Sem prazo' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-else class="report-empty">Ainda não existem tarefas para apresentar.</p>
    </section>
  </main>
</template>

<style scoped>
.reports-page {
  width: min(1280px, 100%);
  margin: 0 auto;
  padding: 16px 4px 40px;
}

.report-hero {
  margin-bottom: 20px;
}

.report-hero .hero-layout {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
}

.report-date {
  margin-top: 14px !important;
  font-size: 12px !important;
}

.report-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.report-kpis {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 18px;
}

.report-kpi {
  display: grid;
  gap: 7px;
  padding: 19px 20px;
  background: var(--tf-surface);
  border: 1px solid var(--tf-border);
  border-radius: var(--tf-radius);
  box-shadow: var(--tf-shadow);
}

.report-kpi > span,
.report-kpi small {
  color: var(--tf-text-muted);
  font-size: 12px;
}

.report-kpi > strong {
  color: var(--tf-text);
  font-size: 30px;
  line-height: 1;
  font-variant-numeric: tabular-nums;
}

.report-kpi-alert > strong {
  color: var(--tf-danger);
}

.report-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1.15fr);
  gap: 18px;
  margin-bottom: 18px;
}

.report-card {
  min-width: 0;
  padding: 22px;
}

.project-report-list {
  display: grid;
  gap: 20px;
}

.project-report {
  display: grid;
  gap: 8px;
}

.project-report-heading {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: var(--tf-text);
  font-size: 13px;
}

.project-report-heading span {
  color: var(--tf-primary);
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.project-progress-track {
  height: 7px;
  overflow: hidden;
  background: var(--tf-border-soft);
  border-radius: 999px;
}

.project-progress-track span {
  display: block;
  height: 100%;
  background: var(--tf-primary);
  border-radius: inherit;
}

.project-report small {
  color: var(--tf-text-muted);
  font-size: 11px;
}

.task-report-card {
  margin-bottom: 10px;
}

.task-count {
  color: var(--tf-text-muted);
  font-size: 12px;
  white-space: nowrap;
}

.report-table-wrap {
  overflow-x: auto;
}

.report-table {
  width: 100%;
  min-width: 720px;
  border-collapse: collapse;
  text-align: left;
}

.report-table th,
.report-table td {
  padding: 12px 10px;
  border-bottom: 1px solid var(--tf-border-soft);
  font-size: 12px;
}

.report-table th {
  color: var(--tf-text-muted);
  font-weight: 650;
  white-space: nowrap;
}

.report-table td {
  color: var(--tf-text-muted);
}

.report-table .task-name {
  max-width: 260px;
  color: var(--tf-text);
  font-weight: 600;
}

.task-status {
  display: inline-flex;
  padding: 4px 8px;
  background: var(--tf-border-soft);
  border-radius: 999px;
  color: var(--tf-text-muted);
  font-size: 11px;
  white-space: nowrap;
}

.status-em-curso {
  color: var(--tf-info);
  background: var(--tf-info-soft);
}

.status-concluída {
  color: var(--tf-success);
  background: var(--tf-success-soft);
}

.status-bloqueada {
  color: var(--tf-danger);
  background: var(--tf-danger-soft);
}

.overdue-date {
  color: var(--tf-danger) !important;
  font-weight: 650;
}

.report-empty {
  margin: 0;
  padding: 18px 0;
  color: var(--tf-text-muted);
  font-size: 13px;
}

@media (max-width: 900px) {
  .report-kpis {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .report-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 620px) {
  .reports-page {
    padding: 8px 0 24px;
  }

  .report-hero .hero-layout {
    align-items: flex-start;
    flex-direction: column;
  }

  .report-actions {
    width: 100%;
  }

  .report-actions .btn {
    flex: 1;
    padding: 9px 10px;
    font-size: 12px;
  }

  .report-kpis {
    gap: 9px;
  }

  .report-kpi {
    padding: 14px;
  }

  .report-kpi > strong {
    font-size: 25px;
  }

  .report-card {
    padding: 16px;
  }
}

@media print {
  :global(.app-sidebar),
  :global(.app-header),
  :global(.admin-footer) {
    display: none !important;
  }

  :global(.admin-content) {
    padding: 0 !important;
  }

  .reports-page {
    width: 100%;
    padding: 0;
  }

  .report-actions {
    display: none;
  }

  .report-grid {
    grid-template-columns: 1fr 1fr;
  }

  .report-card,
  .report-kpi {
    break-inside: avoid;
    box-shadow: none;
  }

  .task-report-card {
    break-before: page;
  }
}
</style>
