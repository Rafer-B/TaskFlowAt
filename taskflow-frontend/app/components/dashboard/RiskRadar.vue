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
const riscoSelecionado = ref<Risco | null>(null)

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

async function abrirRisco(risk: Risco): Promise<void> {
  riscoSelecionado.value = risk
}

async function abrirDestinoRisco(): Promise<void> {
  if (!riscoSelecionado.value) return
  await navigateTo(riscoSelecionado.value.destination)
}
</script>

<template>
  <!-- Só apresenta a lista quando a análise terminou sem erro; estados alternativos são anunciados. -->
  <section
    class="risk-radar content-card"
    :class="{ 'has-risks': risks.length > 0 && !loading && !error }"
    aria-labelledby="risk-radar-heading"
  >
    <div class="radar-heading">
      <div class="radar-title">
        <span class="radar-symbol" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none">
            <path d="M12 3 20 6v5c0 5-3.4 8.5-8 10-4.6-1.5-8-5-8-10V6l8-3Z" />
            <path d="M12 8v4m0 3h.01" />
          </svg>
        </span>
        <div>
          <span class="radar-eyebrow">MONITORIZAÇÃO PROATIVA</span>
          <h2 id="risk-radar-heading">Radar de risco</h2>
          <p>Alertas prioritários para manter os projetos em movimento.</p>
        </div>
      </div>
      <div
        v-if="!loading && !error"
        class="radar-summary"
        :class="{ 'summary-healthy': risks.length === 0 }"
        aria-label="Resumo de riscos"
      >
        <span class="summary-total">
          <strong>{{ risks.length }}</strong>
          <small>{{ risks.length === 1 ? 'alerta ativo' : 'alertas ativos' }}</small>
        </span>
        <span v-if="blockedCount" class="summary-chip summary-blocked">
          <span class="summary-dot" aria-hidden="true"></span>{{ blockedCount }} bloqueios
        </span>
        <span v-if="overdueCount" class="summary-chip summary-overdue">
          <span class="summary-dot" aria-hidden="true"></span>{{ overdueCount }} atrasos
        </span>
        <span v-if="inactiveCount" class="summary-chip summary-inactive">
          <span class="summary-dot" aria-hidden="true"></span>{{ inactiveCount }} sem atividade
        </span>
        <span v-if="risks.length === 0" class="summary-chip summary-clear">
          <span class="summary-dot" aria-hidden="true"></span>Tudo em dia
        </span>
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
        <button
          type="button"
          @click="abrirRisco(risk)"
          class="risk-item"
          :class="`risk-${risk.type}`"
          :aria-label="`Ver detalhes do risco: ${risk.title}`"
        >
          <span class="risk-icon" :class="`icon-${risk.type}`" aria-hidden="true">
            {{ riskIcon(risk.type) }}
          </span>
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
        </button>
      </li>
    </ul>
    <div v-if="riscoSelecionado" class="risk-detail" aria-live="polite">
      <div>
        <span>{{ riskLabel(riscoSelecionado.type) }} · {{ riscoSelecionado.project }}</span>
        <strong>{{ riscoSelecionado.title }}</strong>
        <p>{{ riscoSelecionado.description }}</p>
      </div>
      <div class="risk-detail-actions">
        <button type="button" class="risk-detail-link" @click="abrirDestinoRisco">
          {{ riscoSelecionado.type === 'inactive' ? 'Ver tarefas do projeto' : 'Abrir tarefa' }}
          <span aria-hidden="true">→</span>
        </button>
        <button type="button" class="risk-detail-close" @click="riscoSelecionado = null">
          Fechar
        </button>
      </div>
    </div>
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
  position: relative;
  overflow: hidden;
  padding: 24px;
  border-color: #e4e9f2;
  background:
    radial-gradient(ellipse at 100% 0, rgb(99 102 241 / 6%), transparent 34%),
    #fff;
  box-shadow: 0 8px 26px rgb(26 39 74 / 5%);
}

.risk-radar.has-risks {
  border-color: #f0dfc9;
  background:
    radial-gradient(ellipse at 100% 0, rgb(245 158 11 / 8%), transparent 36%),
    #fff;
}

.radar-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.radar-title {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 13px;
}

.radar-symbol {
  display: grid;
  width: 44px;
  height: 44px;
  flex: 0 0 44px;
  place-items: center;
  color: #5362cf;
  background: linear-gradient(145deg, #f0f2ff, #e8ebff);
  border: 1px solid #e1e5ff;
  border-radius: 14px;
}

.has-risks .radar-symbol {
  color: #a76b22;
  background: linear-gradient(145deg, #fff8eb, #fff1d7);
  border-color: #f7e7c7;
}

.radar-symbol svg {
  width: 23px;
  height: 23px;
  stroke: currentColor;
  stroke-width: 1.7;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.radar-eyebrow {
  color: #6673cf;
  font-size: 9px;
  font-weight: 800;
  letter-spacing: 0.12em;
}

.has-risks .radar-eyebrow {
  color: #a76b22;
}

.radar-heading h2 {
  margin: 4px 0;
  color: var(--tf-text);
  font-size: 18px;
  letter-spacing: -0.025em;
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
  align-items: center;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.summary-total {
  display: grid;
  min-width: 65px;
  justify-items: center;
  gap: 1px;
  padding: 5px 12px;
  color: #43516c;
  background: #f5f7fb;
  border: 1px solid #e9edf4;
  border-radius: 12px;
}

.summary-healthy .summary-total {
  color: #18764b;
  background: #effaf4;
  border-color: #d7f0e2;
}

.summary-total strong {
  font-size: 19px;
  font-weight: 800;
  line-height: 1.1;
  font-variant-numeric: tabular-nums;
}

.summary-total small {
  color: #7d899d;
  font-size: 9px;
  white-space: nowrap;
}

.summary-chip,
.risk-type {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 9px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 700;
  white-space: nowrap;
}

.summary-dot {
  width: 6px;
  height: 6px;
  flex: 0 0 6px;
  background: currentColor;
  border-radius: 50%;
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
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 300px), 1fr));
  gap: 11px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.risk-detail {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: 12px;
  padding: 14px 16px;
  background: #f7f9fc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
}

.risk-detail > div:first-child {
  display: grid;
  gap: 5px;
}

.risk-detail > div:first-child > span,
.risk-detail p {
  margin: 0;
  color: #74839b;
  font-size: 10px;
}

.risk-detail strong {
  color: #263957;
  font-size: 12px;
}

.risk-detail-actions {
  display: flex;
  flex: 0 0 auto;
  gap: 8px;
}

.risk-detail-actions button {
  min-height: 34px;
  padding: 0 10px;
  color: #4f5fd5;
  background: #fff;
  border: 1px solid #dfe5ef;
  border-radius: 7px;
  font-size: 10px;
  font-weight: 700;
  cursor: pointer;
}

.risk-detail-actions .risk-detail-close {
  color: #64748b;
}

.risk-item {
  width: 100%;
  min-height: 94px;
  display: flex;
  align-items: center;
  gap: 13px;
  min-width: 0;
  padding: 14px;
  border: 1px solid #e8ecf3;
  border-left: 4px solid #94a3b8;
  border-radius: 13px;
  background: linear-gradient(120deg, #fff, #fbfcfe);
  color: inherit;
  text-align: left;
  text-decoration: none;
  cursor: pointer;
  transition: border-color .18s ease, box-shadow .18s ease, transform .18s ease, background .18s ease;
}

.risk-item:hover {
  border-top-color: #d8deee;
  border-right-color: #d8deee;
  border-bottom-color: #d8deee;
  box-shadow: 0 8px 20px rgb(23 43 77 / 9%);
  transform: translateY(-2px);
}

.risk-item:focus-visible {
  outline: 2px solid var(--tf-primary);
  outline-offset: 2px;
}

.risk-item.risk-blocked {
  border-left-color: #d94d5c;
}

.risk-item.risk-blocked:hover {
  background: linear-gradient(120deg, #fff, #fff8f8);
}

.risk-item.risk-overdue {
  border-left-color: #e49a2d;
}

.risk-item.risk-overdue:hover {
  background: linear-gradient(120deg, #fff, #fffbf3);
}

.risk-item.risk-inactive {
  border-left-color: #7889bb;
}

.risk-item.risk-inactive:hover {
  background: linear-gradient(120deg, #fff, #f8f9ff);
}

.risk-icon {
  display: grid;
  width: 38px;
  height: 38px;
  flex: 0 0 38px;
  place-items: center;
  color: var(--tf-text-muted);
  background: var(--tf-border-soft);
  border-radius: 12px;
  font-size: 16px;
  font-weight: 850;
}

.risk-blocked .risk-icon {
  color: var(--tf-danger);
  background: var(--tf-danger-soft);
}

.risk-overdue .risk-icon {
  color: #b45309;
  background: var(--tf-warning-soft);
}

.risk-inactive .risk-icon {
  color: #5666a8;
  background: #eef0ff;
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
  transition: transform .18s ease;
}

.risk-item:hover .risk-link {
  transform: translateX(2px);
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
    padding: 17px 15px;
  }

  .radar-heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .radar-summary {
    justify-content: flex-start;
  }

  .risk-list {
    grid-template-columns: 1fr;
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
