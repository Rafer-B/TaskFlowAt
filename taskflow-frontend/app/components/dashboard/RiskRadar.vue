<script setup lang="ts">
import { computed } from 'vue'

import { diffInDays, parseISODay, toISODay } from '~/utils/dates'

// Recebe os registos já autorizados pelo chamador e apresenta causas concretas de risco.
type EstadoTarefa = 'Por fazer' | 'Em curso' | 'Concluída' | 'Bloqueada'
type EstadoProjeto = 'Ativo' | 'Concluído' | 'Arquivado'

interface ProjetoRadar {
  id: number
  name: string
  status: EstadoProjeto
  createdAt: string
  updatedAt: string | null
}

interface TarefaRadar {
  id: number
  projectId: number
  title: string
  project: string
  responsible: string
  status: EstadoTarefa
  dueDate: string | null
  responsible?: string
  createdAt: string
  updatedAt: string | null
}

interface Risco {
  id: string
  type: 'blocked' | 'overdue' | 'inactive'
  severity: number
  projectId: number
  title: string
  project: string
  description: string
  destination: string
}

const props = withDefaults(defineProps<{
  projects: ProjetoRadar[]
  tasks: TarefaRadar[]
  loading?: boolean
  error?: string
}>(), {
  loading: false,
  error: '',
})

const todayISO = computed(() => toISODay(new Date()))
const activeProjects = computed(() =>
  props.projects.filter((project) => project.status === 'Ativo'),
)
const activeProjectIds = computed(() =>
  new Set(activeProjects.value.map((project) => project.id)),
)

function day(value: string | null): string | null {
  if (!value) return null
  const parsed = value.slice(0, 10)
  return /^\d{4}-\d{2}-\d{2}$/.test(parsed) ? parsed : null
}

function elapsedDays(value: string | null): number | null {
  const date = day(value)
  return date ? diffInDays(parseISODay(date), parseISODay(todayISO.value)) : null
}

function lastActivity(project: ProjetoRadar): string | null {
  // Considera atividade do projeto e das respetivas tarefas para evitar falsos períodos de inatividade.
  const activityDates = [
    project.createdAt,
    project.updatedAt,
    ...props.tasks
      .filter((task) => task.projectId === project.id)
      .flatMap((task) => [task.createdAt, task.updatedAt]),
  ]
    .map(day)
    .filter((date): date is string => date !== null)
    .sort()

  return activityDates.at(-1) ?? null
}

const risks = computed<Risco[]>(() => {
  const items: Risco[] = []

  for (const task of props.tasks) {
    if (!activeProjectIds.value.has(task.projectId)) continue
    const project = props.projects.find((item) => item.id === task.projectId)
    if (!project) continue

    const overdueDays = task.status === 'Concluída' || !task.dueDate
      ? null
      : elapsedDays(task.dueDate)
    const isOverdue = overdueDays !== null && overdueDays > 0

    if (task.status === 'Bloqueada') {
      const responsibleLabel = task.responsible
        ? ` Responsável: ${task.responsible}.`
        : ''
      items.push({
        id: `blocked-${task.id}`,
        type: 'blocked',
        severity: 0,
        projectId: project.id,
        title: task.title,
        project: project.name,
        description: isOverdue
          ? `Bloqueada e atrasada há ${overdueDays} ${overdueDays === 1 ? 'dia' : 'dias'}.${responsibleLabel}`
          : `Tarefa bloqueada.${responsibleLabel}`,
        destination: `/tasks?taskId=${task.id}`,
      })
    } else if (isOverdue) {
      const responsibleLabel = task.responsible
        ? ` Responsável: ${task.responsible}.`
        : ''
      items.push({
        id: `overdue-${task.id}`,
        type: 'overdue',
        severity: 1,
        projectId: project.id,
        title: task.title,
        project: project.name,
        description: `Prazo ultrapassado há ${overdueDays} ${overdueDays === 1 ? 'dia' : 'dias'}.${responsibleLabel}`,
        destination: `/tasks?taskId=${task.id}`,
      })
    }
  }

  // Um projeto ativo sem registos recentes é sinalizado após sete dias sem atividade.
  for (const project of activeProjects.value) {
    const lastActivityDate = lastActivity(project)
    const inactiveDays = elapsedDays(lastActivityDate)
    if (inactiveDays === null || inactiveDays < 7) continue

    items.push({
      id: `inactive-${project.id}`,
      type: 'inactive',
      severity: 2,
      projectId: project.id,
      title: project.name,
      project: project.name,
      description: `Sem atividade registada há ${inactiveDays} dias.`,
      destination: `/tasks?projectId=${project.id}`,
    })
  }

  return items.sort((a, b) =>
    a.severity - b.severity ||
    a.project.localeCompare(b.project, 'pt-PT') ||
    a.title.localeCompare(b.title, 'pt-PT'),
  )
})

const blockedCount = computed(() =>
  risks.value.filter((risk) => risk.type === 'blocked').length,
)
const overdueCount = computed(() =>
  risks.value.filter((risk) => risk.type === 'overdue').length,
)
const inactiveCount = computed(() =>
  risks.value.filter((risk) => risk.type === 'inactive').length,
)

function riskLabel(type: Risco['type']): string {
  const labels: Record<Risco['type'], string> = {
    blocked: 'Bloqueio',
    overdue: 'Atraso',
    inactive: 'Sem atividade',
  }

  return labels[type]
}

function riskIcon(type: Risco['type']): string {
  const icons: Record<Risco['type'], string> = {
    blocked: '!',
    overdue: '◷',
    inactive: '…',
  }

  return icons[type]
}
</script>

<template>
  <!-- Só apresenta a lista quando a análise terminou sem erro; estados alternativos são anunciados. -->
  <section class="risk-radar content-card" aria-labelledby="risk-radar-heading">
    <div class="radar-heading">
      <div>
        <span class="radar-eyebrow">PREVENÇÃO</span>
        <h2 id="risk-radar-heading">Radar de risco</h2>
        <p>Atrasos, bloqueios e projetos sem atividade recente.</p>
      </div>
      <div v-if="!loading && !error" class="radar-summary" aria-label="Resumo de riscos">
        <span v-if="blockedCount" class="summary-blocked">{{ blockedCount }} bloqueios</span>
        <span v-if="overdueCount" class="summary-overdue">{{ overdueCount }} atrasos</span>
        <span v-if="inactiveCount" class="summary-inactive">{{ inactiveCount }} sem atividade</span>
        <span v-if="risks.length === 0" class="summary-clear">Tudo em dia</span>
      </div>
    </div>

    <p v-if="loading" class="radar-state" role="status">
      A analisar projetos e tarefas...
    </p>
    <p v-else-if="error" class="radar-state radar-error" role="alert">
      {{ error }}
    </p>
    <ul v-else-if="risks.length" class="risk-list">
      <li v-for="risk in risks" :key="risk.id">
        <NuxtLink
          :to="risk.destination"
          class="risk-item"
          :class="`risk-${risk.type}`"
          :aria-label="`Ver ${risk.title} em ${risk.type === 'inactive' ? 'tarefas do projeto' : 'detalhes da tarefa'}`"
        >
          <span class="risk-icon" aria-hidden="true">{{ riskIcon(risk.type) }}</span>
          <div class="risk-copy">
            <div class="risk-title-row">
              <strong>{{ risk.title }}</strong>
              <span class="risk-type">{{ riskLabel(risk.type) }}</span>
            </div>
            <span class="risk-project">{{ risk.project }}</span>
            <p>{{ risk.description }}</p>
          </div>
          <span class="risk-link" aria-hidden="true">
            Ver <span>→</span>
          </span>
        </NuxtLink>
      </li>
    </ul>
    <div v-else class="radar-clear">
      <span aria-hidden="true">✓</span>
      <div>
        <strong>Sem riscos detetados</strong>
        <p>Não há tarefas bloqueadas ou atrasadas nem projetos inativos há 7 ou mais dias.</p>
      </div>
    </div>
  </section>
</template>

<style scoped>
.risk-radar {
  padding: 22px 24px;
}

.radar-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.radar-eyebrow {
  color: var(--tf-primary);
  font-size: 9px;
  font-weight: 800;
  letter-spacing: 0.12em;
}

.radar-heading h2 {
  margin: 5px 0;
  color: var(--tf-text);
  font-size: 17px;
}

.radar-heading p,
.risk-copy p,
.radar-clear p {
  margin: 0;
  color: var(--tf-text-muted);
  font-size: 12px;
  line-height: 1.5;
}

.radar-summary {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 6px;
}

.radar-summary span,
.risk-type {
  padding: 5px 8px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 700;
  white-space: nowrap;
}

.summary-blocked,
.risk-blocked .risk-type {
  color: var(--tf-danger);
  background: var(--tf-danger-soft);
}

.summary-overdue,
.risk-overdue .risk-type {
  color: #b45309;
  background: var(--tf-warning-soft);
}

.summary-inactive,
.risk-inactive .risk-type {
  color: var(--tf-text-muted);
  background: var(--tf-border-soft);
}

.summary-clear {
  color: var(--tf-success);
  background: var(--tf-success-soft);
}

.risk-list {
  display: grid;
  gap: 9px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.risk-item {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
  padding: 12px;
  border: 1px solid var(--tf-border);
  border-left: 3px solid #94a3b8;
  border-radius: 10px;
  background: var(--tf-surface);
  color: inherit;
  text-decoration: none;
  transition: border-color .15s ease, box-shadow .15s ease, transform .15s ease;
}

.risk-item:hover {
  border-color: var(--tf-primary);
  box-shadow: 0 4px 12px rgb(23 43 77 / 8%);
  transform: translateY(-1px);
}

.risk-item:focus-visible {
  outline: 2px solid var(--tf-primary);
  outline-offset: 2px;
}

.risk-item.risk-blocked {
  border-left-color: var(--tf-danger);
}

.risk-item.risk-overdue {
  border-left-color: var(--tf-warning);
}

.risk-item.risk-inactive {
  border-left-color: #94a3b8;
}

.risk-icon {
  display: grid;
  width: 30px;
  height: 30px;
  flex: 0 0 30px;
  place-items: center;
  color: var(--tf-text-muted);
  background: var(--tf-border-soft);
  border-radius: 9px;
  font-size: 14px;
  font-weight: 800;
}

.risk-blocked .risk-icon {
  color: var(--tf-danger);
  background: var(--tf-danger-soft);
}

.risk-overdue .risk-icon {
  color: #b45309;
  background: var(--tf-warning-soft);
}

.risk-copy {
  flex: 1;
  min-width: 0;
}

.risk-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.risk-title-row strong {
  overflow: hidden;
  color: var(--tf-text);
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.risk-type {
  padding: 3px 7px;
  font-size: 9px;
}

.risk-project {
  display: block;
  margin: 3px 0;
  color: var(--tf-text-light);
  font-size: 10px;
}

.risk-copy p {
  font-size: 11px;
}

.risk-link {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  flex: 0 0 auto;
  color: var(--tf-primary);
  font-size: 11px;
  font-weight: 700;
}

.risk-link:hover {
  text-decoration: underline;
}

.radar-state {
  margin: 0;
  padding: 14px;
  color: var(--tf-text-muted);
  background: var(--tf-border-soft);
  border-radius: 9px;
  font-size: 12px;
}

.radar-error {
  color: var(--tf-danger);
  background: var(--tf-danger-soft);
}

.radar-clear {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 15px;
  color: var(--tf-success);
  background: var(--tf-success-soft);
  border-radius: 10px;
}

.radar-clear > span {
  display: grid;
  width: 30px;
  height: 30px;
  flex: 0 0 30px;
  place-items: center;
  background: rgb(255 255 255 / 65%);
  border-radius: 50%;
  font-weight: 800;
}

.radar-clear strong {
  display: block;
  margin-bottom: 3px;
  color: var(--tf-success);
  font-size: 12px;
}

.radar-clear p {
  color: #4b7a60;
  font-size: 11px;
}

@media (max-width: 620px) {
  .risk-radar {
    padding: 17px;
  }

  .radar-heading {
    flex-direction: column;
  }

  .radar-summary {
    justify-content: flex-start;
  }

  .risk-item {
    align-items: flex-start;
    gap: 9px;
    padding: 10px;
  }

  .risk-title-row {
    align-items: flex-start;
    flex-direction: column;
    gap: 4px;
  }
}
</style>
