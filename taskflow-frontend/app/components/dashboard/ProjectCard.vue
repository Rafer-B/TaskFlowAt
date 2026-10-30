
<script setup lang="ts">
import { computed } from 'vue'
import type { DashboardProject } from '~/composables/useDashboardData'
import { diffInDays, parseISODay, toISODay } from '~/utils/dates'

const props = withDefaults(defineProps<{
  project: DashboardProject
  progress?: number
  members?: string[]
}>(), {
  progress: 0,
  members: () => []
})

const today = computed(() => parseISODay(toISODay(new Date())))

const validDueDate = computed(() => {
  const value = props.project.dueDate

  if (!value) return null

  const parsed = parseISODay(value.slice(0, 10))

  return Number.isNaN(parsed.getTime()) ? null : parsed
})

const daysLeft = computed(() => {
  if (!validDueDate.value) return null

  return diffInDays(today.value, validDueDate.value)
})

const dueTone = computed(() => {
  if (daysLeft.value === null) return 'none'
  if (daysLeft.value < 0) return 'late'
  if (daysLeft.value <= 3) return 'soon'

  return 'ok'
})

const dueLabel = computed(() => {
  const days = daysLeft.value

  if (days === null) return 'Sem prazo definido'

  if (days < 0) {
    const overdueDays = Math.abs(days)
    return `Atrasado há ${overdueDays} dia${overdueDays === 1 ? '' : 's'}`
  }

  if (days === 0) return 'Termina hoje'
  if (days === 1) return 'Termina amanhã'

  return `Termina em ${days} dias`
})

const statusClass = computed(() => {
  switch (props.project.status) {
    case 'Ativo':
      return 'active'
    case 'Concluído':
      return 'completed'
    case 'Arquivado':
      return 'archived'
    default:
      return 'unknown'
  }
})

const safeProgress = computed(() =>
  Math.min(
    100,
    Math.max(0, Number.isFinite(props.progress) ? props.progress : 0)
  )
)

function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean)

  if (parts.length === 0) return '?'

  if (parts.length === 1) {
    return (parts[0] ?? '').slice(0, 2).toUpperCase()
  }

  const first = parts[0] ?? ''
  const last = parts[parts.length - 1] ?? ''

  return `${first.charAt(0)}${last.charAt(0)}`.toUpperCase()
}

function colorFor(value: string): string {
  const colors = [
    '#4f46e5',
    '#2563eb',
    '#0f766e',
    '#b45309',
    '#7c3aed',
    '#be185d',
    '#475569'
  ]

  let hash = 0

  for (const char of value) {
    hash = (hash * 31 + char.charCodeAt(0)) | 0
  }

  const index = Math.abs(hash) % colors.length

  return colors[index] ?? colors[0]!
}
</script>

<template>
  <article class="project-card">
    <header class="project-header">
      <div class="project-identity">
        <div
          class="project-avatar"
          :style="{ background: colorFor(project.name) }"
          aria-hidden="true"
        >
          {{ initials(project.name) }}
        </div>

        <div class="project-heading">
          <strong class="project-name">
            {{ project.name }}
          </strong>

          <span class="project-meta">
            Projeto #{{ project.id }}
          </span>
        </div>
      </div>

      <span class="status-badge" :class="`status-${statusClass}`">
        {{ project.status }}
      </span>
    </header>

    <section class="project-progress" aria-label="Progresso do projeto">
      <div class="progress-heading">
        <span>Progresso</span>
        <strong>{{ Math.round(safeProgress) }}%</strong>
      </div>

      <div
        class="progress-track"
        role="progressbar"
        :aria-valuenow="Math.round(safeProgress)"
        aria-valuemin="0"
        aria-valuemax="100"
        :aria-label="`Progresso de ${project.name}`"
      >
        <span
          class="progress-fill"
          :style="{ width: `${safeProgress}%` }"
        />
      </div>
    </section>

    <footer class="project-footer">
      <span class="due" :class="`due-${dueTone}`">
        <span class="due-indicator" aria-hidden="true" />
        {{ dueLabel }}
      </span>

      <div
        v-if="members.length"
        class="project-members"
        :aria-label="`${members.length} membros`"
      >
        <span
          v-for="(member, index) in members.slice(0, 3)"
          :key="`${member}-${index}`"
          class="member-avatar"
          :style="{ background: colorFor(member) }"
          :title="member"
        >
          {{ initials(member) }}
        </span>

        <span v-if="members.length > 3" class="member-more">
          +{{ members.length - 3 }}
        </span>
      </div>

      <span v-else class="no-members">
        Sem membros
      </span>
    </footer>
  </article>
</template>

<style scoped>
.project-card {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 18px;
  padding: 20px;
  border: 1px solid #e5eaf2;
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 4px 16px rgb(15 23 42 / 4%);
  transition: transform .2s ease, box-shadow .2s ease, border-color .2s ease;
}

.project-card:hover {
  transform: translateY(-2px);
  border-color: #cbd5e1;
  box-shadow: 0 10px 26px rgb(15 23 42 / 8%);
}

.project-header,
.project-identity,
.project-footer,
.progress-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.project-identity {
  justify-content: flex-start;
  min-width: 0;
}

.project-avatar,
.member-avatar {
  display: grid;
  flex: 0 0 auto;
  place-items: center;
  color: #fff;
  font-weight: 700;
}

.project-avatar {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  font-size: 13px;
}

.project-heading {
  min-width: 0;
}

.project-name {
  display: block;
  overflow: hidden;
  color: #172b4d;
  font-size: 14px;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.project-meta {
  display: block;
  margin-top: 4px;
  color: #94a3b8;
  font-size: 11px;
}

.status-badge {
  flex: 0 0 auto;
  padding: 5px 9px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 700;
}

.status-active {
  background: #eaf2ff;
  color: #2563eb;
}

.status-completed {
  background: #e8f8ef;
  color: #15803d;
}

.status-archived,
.status-unknown {
  background: #f1f5f9;
  color: #64748b;
}

.project-progress {
  display: grid;
  gap: 9px;
}

.progress-heading {
  color: #64748b;
  font-size: 12px;
}

.progress-heading strong {
  color: #334155;
  font-variant-numeric: tabular-nums;
}

.progress-track {
  height: 8px;
  overflow: hidden;
  border-radius: 999px;
  background: #edf1f7;
}

.progress-fill {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #3b82f6, #6366f1);
  transition: width .45s ease;
}

.project-footer {
  min-height: 30px;
  padding-top: 13px;
  border-top: 1px solid #eef1f6;
}

.due,
.no-members {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-size: 11px;
  font-weight: 600;
}

.due-ok {
  color: #15803d;
}

.due-soon {
  color: #b45309;
}

.due-late {
  color: #dc2626;
}

.due-none,
.no-members {
  color: #94a3b8;
}

.due-indicator {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: currentColor;
}

.project-members {
  display: flex;
  align-items: center;
  padding-left: 6px;
}

.member-avatar {
  width: 27px;
  height: 27px;
  margin-left: -6px;
  border: 2px solid #fff;
  border-radius: 50%;
  font-size: 9px;
}

.member-more {
  margin-left: 5px;
  color: #64748b;
  font-size: 11px;
  font-weight: 700;
}

@media (prefers-reduced-motion: reduce) {
  .project-card,
  .progress-fill {
    transition: none;
  }
}
</style>
