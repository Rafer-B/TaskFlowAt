
<script setup lang="ts">
import { computed } from 'vue'
import type { DashboardTask } from '~/composables/useDashboardData'
import { diffInDays, parseISODay, toISODay } from '~/utils/dates'

const props = defineProps<{
  task: DashboardTask
}>()

const today = computed(() => parseISODay(toISODay(new Date())))

const validDueDate = computed(() => {
  const value = props.task.dueDate

  if (!value) return null

  const parsed = parseISODay(value.slice(0, 10))

  return Number.isNaN(parsed.getTime()) ? null : parsed
})

const daysLeft = computed(() => {
  if (!validDueDate.value) return null

  return diffInDays(today.value, validDueDate.value)
})

const dueTone = computed(() => {
  const days = daysLeft.value

  if (days === null) return 'none'
  if (days < 0) return 'late'
  if (days <= 3) return 'soon'

  return 'ok'
})

const dueLabel = computed(() => {
  const days = daysLeft.value

  if (days === null) return 'Sem prazo'

  if (days < 0) {
    const overdueDays = Math.abs(days)
    return `Atrasada há ${overdueDays} dia${overdueDays === 1 ? '' : 's'}`
  }

  if (days === 0) return 'Hoje'
  if (days === 1) return 'Amanhã'

  return `Em ${days} dias`
})

const statusClass = computed(() => {
  switch (props.task.status) {
    case 'Por fazer':
      return 'por-fazer'
    case 'Em curso':
      return 'em-curso'
    case 'Concluída':
      return 'concluida'
    case 'Bloqueada':
      return 'bloqueada'
    default:
      return 'por-fazer'
  }
})

const initials = computed(() => {
  const parts = props.task.responsible.trim().split(/\s+/).filter(Boolean)

  if (parts.length === 0) return '?'

  if (parts.length === 1) {
    return (parts[0] ?? '').slice(0, 2).toUpperCase()
  }

  const first = parts[0] ?? ''
  const last = parts[parts.length - 1] ?? ''

  return `${first.charAt(0)}${last.charAt(0)}`.toUpperCase()
})

const avatarColor = computed(() => {
  const colors = [
    '#4f46e5',
    '#3b82f6',
    '#2563eb',
    '#15803d',
    '#d97706',
    '#b91c1c',
    '#0891b2',
    '#7c3aed',
    '#db2777',
    '#ca8a04'
  ]

  let hash = 0

  for (const ch of props.task.responsible) {
    hash = ((hash << 5) - hash) + ch.charCodeAt(0)
    hash |= 0
  }

  const index = Math.abs(hash) % colors.length

  return colors[index] ?? colors[0]!
})
</script>

<template>
  <li class="task-row">
    <div class="task-main">
      <div
        class="avatar"
        :style="{ background: avatarColor }"
        aria-hidden="true"
      >
        {{ initials }}
      </div>

      <div class="task-information">
        <strong class="task-title">
          {{ task.title }}
        </strong>

        <em class="task-project">
          {{ task.project }}
        </em>
      </div>
    </div>

    <div class="task-meta">
      <span
        class="priority"
        :class="`priority-${task.priority.toLowerCase()}`"
      >
        <span class="priority-dot" aria-hidden="true" />
        <span class="priority-text">
          {{ task.priority }}
        </span>
      </span>

      <span class="due" :class="`due-${dueTone}`">
        {{ dueLabel }}
      </span>

      <span
        class="badge badge-status"
        :class="`badge-${statusClass}`"
      >
        {{ task.status }}
      </span>
    </div>
  </li>
</template>

<style scoped>
.task-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 12px;
  background: var(--tf-surface);
  border: 1px solid var(--tf-border);
  transition: border-color var(--tf-transition), box-shadow var(--tf-transition);
}

.task-row:hover {
  border-color: var(--tf-primary);
  box-shadow: 0 2px 8px -4px rgb(79 70 229 / 12%);
}

.task-main {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  font-size: 13px;
  font-weight: 700;
  color: #fff;
  flex-shrink: 0;
}

.task-information {
  min-width: 0;
}

.task-title {
  display: block;
  overflow: hidden;
  font-weight: 600;
  color: var(--tf-text);
  font-size: 14px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-project {
  font-style: normal;
  color: var(--tf-text-muted);
  font-weight: 500;
  font-size: 13px;
  display: block;
  margin-top: 2px;
}

.task-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  color: var(--tf-text-muted);
  flex-shrink: 0;
}

.task-meta .due {
  font-weight: 600;
  white-space: nowrap;
}

.priority {
  display: flex;
  align-items: center;
  gap: 6px;
}

.priority-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}

.priority-alta .priority-dot {
  background: var(--tf-danger);
}

.priority-media .priority-dot {
  background: var(--tf-warning);
}

.priority-baixa .priority-dot {
  background: var(--tf-success);
}

.priority-text {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  white-space: nowrap;
}

.priority-alta .priority-text {
  color: var(--tf-danger);
}

.priority-media .priority-text {
  color: var(--tf-warning);
}

.priority-baixa .priority-text {
  color: var(--tf-success);
}

.badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  flex-shrink: 0;
}

.badge-status {
  padding: 5px 10px;
}

.badge-por-fazer {
  background: #f1f5f9;
  color: #475569;
}

.badge-em-curso {
  background: var(--tf-info-soft);
  color: var(--tf-info);
}

.badge-concluida {
  background: var(--tf-success-soft);
  color: var(--tf-success);
}

.badge-bloqueada {
  background: var(--tf-danger-soft);
  color: var(--tf-danger);
}

.due.late {
  color: var(--tf-danger);
}

.due.soon {
  color: var(--tf-warning);
}

.due.ok {
  color: var(--tf-success);
}

.due.none {
  color: var(--tf-text-muted);
}

@media (max-width: 640px) {
  .task-row {
    align-items: flex-start;
    flex-direction: column;
  }

  .task-meta {
    width: 100%;
    flex-wrap: wrap;
  }
}
</style>
