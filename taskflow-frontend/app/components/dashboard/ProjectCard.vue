<script setup lang="ts">
import type { DashboardProject } from '~/composables/useDashboardData'
import { diffInDays, toISODay, addDays, parseISODay } from '~/utils/dates'
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    project: DashboardProject
    progress?: number // 0-100
    members?: string[]
  }>(),
  {
    progress: 0,
    members: () => []
  }
)

const today = computed(() => parseISODay(toISODay(new Date())))

const daysLeft = computed(() => diffInDays(today.value, parseISODay(props.project.dueDate)))

const dueTone = computed(() => {
  const d = daysLeft.value
  if (d < 0) return 'late'
  if (d <= 3) return 'soon'
  return 'ok'
})

const dueLabel = computed(() => {
  const d = daysLeft.value
  if (d < 0) return `Atrasado há ${Math.abs(d)} dia${Math.abs(d) === 1 ? '' : 's'}`
  if (d === 0) return 'Vence hoje'
  if (d === 1) return 'Vence amanhã'
  return `Vence em ${d} dias`
})

const statusTone = computed(() => {
  switch (props.project.status) {
    case 'Ativo': return 'ok'
    case 'Concluído': return 'ok'
    case 'Arquivado': return 'none'
    default: return 'none'
  }
})
</script>

<template>
  <article class="project-card" :class="`status-${statusTone}`">
    <header class="project-header">
      <div class="project-identity">
        <div class="avatar" :style="{ background: avatarColor }">
          {{ initials }}
        </div>
        <div>
          <strong class="project-name">{{ project.name }}</strong>
          <span class="project-meta">{{ project.id }}</span>
        </div>
      </div>
      <span class="badge badge-status" :class="`badge-${project.status.toLowerCase().replace('ã', 'a').replace('ç', 'c')}`">
        {{ project.status }}
      </span>
    </header>

    <div class="project-body">
      <p class="project-desc" v-if="progress > 0">
        {{ Math.round(progress) }}% concluído
      </p>
      <div class="project-progress" v-if="progress > 0">
        <div class="progress-track">
          <div
            class="progress-fill"
            :style="{ width: `${Math.min(100, Math.max(0, progress))}%` }"
          />
        </div>
      </div>
    </div>

    <footer class="project-footer">
      <span class="due" :class="`due-${dueTone}`">
        {{ dueLabel }}
      </span>
      <div class="project-members">
        <span
          v-for="(member, index) in members.slice(0, 3)"
          :key="index"
          class="avatar member-avatar"
          :style="{ background: memberColor(member) }"
        >
          {{ memberInitials(member) }}
        </span>
        <span v-if="members.length > 3" class="member-more">+{{ members.length - 3 }}</span>
      </div>
    </footer>
  </article>
</template>

<style scoped>
.project-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 18px;
  border-radius: var(--tf-radius);
  background: var(--tf-surface);
  border: 1px solid var(--tf-border);
  box-shadow: var(--tf-shadow);
  transition: transform var(--tf-transition), box-shadow var(--tf-transition);
}

.project-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--tf-shadow-lg);
}

.project-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.project-identity {
  display: flex;
  align-items: center;
  gap: 10px;
}

.avatar {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  font-size: 13px;
  font-weight: 700;
  color: #fff;
  flex-shrink: 0;
}

.project-name {
  display: block;
  font-size: 15px;
  font-weight: 700;
  color: var(--tf-text);
}

.project-meta {
  font-size: 11px;
  color: var(--tf-text-light);
}

.project-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.project-desc {
  margin: 0;
  font-size: 12px;
  color: var(--tf-text-muted);
  font-weight: 600;
}

.project-progress {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.progress-track {
  height: 8px;
  border-radius: 999px;
  background: var(--tf-border-soft);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, var(--tf-primary), var(--tf-info));
  animation: grow-x 0.8s cubic-bezier(0.22, 1, 0.36, 1) both;
}

.project-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding-top: 6px;
  border-top: 1px solid var(--tf-border-soft);
}

.due {
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}

.due.late { color: var(--tf-danger); }
.due.soon { color: var(--tf-warning); }
.due.ok { color: var(--tf-success); }

.project-members {
  display: flex;
  align-items: center;
  gap: -6px;
}

.member-avatar {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  font-size: 11px;
  font-weight: 700;
  color: #fff;
  border: 2px solid var(--tf-surface);
  margin-left: -8px;
}

.member-avatar:first-child {
  margin-left: 0;
}

.member-more {
  font-size: 11px;
  color: var(--tf-text-muted);
  font-weight: 600;
}

@keyframes grow-x {
  from { transform: scaleX(0); }
}

@media (prefers-reduced-motion: reduce) {
  .project-card,
  .progress-fill {
    animation: none;
    transition: none;
  }
}
</style>