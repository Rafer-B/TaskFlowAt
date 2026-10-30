<script setup lang="ts">
import { computed, useId } from 'vue'

type Tone = 'indigo' | 'blue' | 'green' | 'red'
type IconName = 'folder' | 'bolt' | 'check' | 'alert'
type Trend = 'up' | 'down' | 'none'

const props = withDefaults(defineProps<{
  label: string
  value: number | string
  hint?: string
  tone?: Tone
  icon?: IconName
  progress?: number
  spark?: number[]
  trend?: Trend
}>(), {
  hint: '',
  tone: 'indigo',
  icon: 'folder',
  progress: undefined,
  spark: () => [],
  trend: 'none'
})

const uid = useId()

const icons: Record<IconName, string[]> = {
  folder: ['M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z'],
  bolt: ['M13 2 4 14h7l-1 8 9-12h-7z'],
  check: ['M22 11.08V12a10 10 0 1 1-5.93-9.14', 'M22 4 12 14.01l-3-3'],
  alert: ['M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z', 'M12 9v4', 'M12 17h.01']
}

const iconPaths = computed(() => icons[props.icon])

const clampedProgress = computed(() => {
  if (props.progress === undefined || !Number.isFinite(props.progress)) return undefined
  return Math.min(100, Math.max(0, props.progress))
})

const sparkPoints = computed(() => {
  const values = props.spark.filter(Number.isFinite)
  if (values.length < 2) return []
  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1
  const step = 100 / (values.length - 1)
  return values.map((value, index) => ({
    x: Number((index * step).toFixed(2)),
    y: Number((28 - ((value - min) / range) * 24).toFixed(2))
  }))
})

const sparkLine = computed(() =>
  sparkPoints.value.map(point => `${point.x},${point.y}`).join(' ')
)

const sparkArea = computed(() =>
  sparkPoints.value.length ? `0,32 ${sparkLine.value} 100,32` : ''
)

const trendLabel = computed(() => {
  if (props.trend === 'up') return 'Tendência positiva'
  if (props.trend === 'down') return 'Tendência negativa'
  return ''
})
</script>

<template>
  <article class="stat-card" :class="`tone-${tone}`">
    <div class="stat-top">
      <div class="stat-heading">
        <span class="stat-label">{{ label }}</span>
        <span v-if="trend !== 'none'" class="trend" :class="`trend-${trend}`" :aria-label="trendLabel">
          <span aria-hidden="true">{{ trend === 'up' ? '↑' : '↓' }}</span>
          <span v-if="hint" class="trend-hint">{{ hint }}</span>
        </span>
      </div>

      <span class="stat-icon" aria-hidden="true">
        <svg viewBox="0 0 24 24" width="21" height="21" fill="none" stroke="currentColor"
          stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <path v-for="path in iconPaths" :key="path" :d="path" />
        </svg>
      </span>
    </div>

    <strong class="stat-value">{{ value }}</strong>
    <p v-if="hint && trend === 'none'" class="stat-hint">{{ hint }}</p>

    <div
      v-if="clampedProgress !== undefined"
      class="stat-progress"
      role="progressbar"
      :aria-valuenow="Math.round(clampedProgress)"
      aria-valuemin="0"
      aria-valuemax="100"
      :aria-label="`Progresso: ${label}`"
    >
      <span :style="{ width: `${clampedProgress}%` }"></span>
    </div>

    <svg
      v-else-if="sparkPoints.length"
      class="stat-spark"
      viewBox="0 0 100 32"
      preserveAspectRatio="none"
      aria-hidden="true"
    >
      <defs>
        <linearGradient :id="`spark-${uid}`" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="currentColor" stop-opacity=".22" />
          <stop offset="100%" stop-color="currentColor" stop-opacity="0" />
        </linearGradient>
      </defs>
      <polygon :points="sparkArea" :fill="`url(#spark-${uid})`" />
      <polyline :points="sparkLine" fill="none" stroke="currentColor" stroke-width="2"
        stroke-linecap="round" stroke-linejoin="round" vector-effect="non-scaling-stroke" />
    </svg>
  </article>
</template>

<style scoped>
.stat-card {
  --accent: #4f46e5;
  --accent-soft: #eef2ff;
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 9px;
  padding: 20px;
  border: 1px solid #e5eaf2;
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 4px 16px rgb(15 23 42 / 4%);
  transition: transform .2s ease, box-shadow .2s ease;
}
.stat-card:hover { transform: translateY(-2px); box-shadow: 0 10px 24px rgb(15 23 42 / 8%); }
.tone-blue { --accent: #2563eb; --accent-soft: #eaf2ff; }
.tone-green { --accent: #15803d; --accent-soft: #e8f8ef; }
.tone-red { --accent: #dc2626; --accent-soft: #fef0f0; }
.stat-top, .stat-heading { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
.stat-heading { min-width: 0; justify-content: flex-start; flex-wrap: wrap; }
.stat-label { color: #64748b; font-size: 12px; font-weight: 600; }
.stat-icon {
  display: grid; flex: 0 0 auto; width: 40px; height: 40px; place-items: center;
  border-radius: 12px; background: var(--accent-soft); color: var(--accent);
}
.stat-value {
  margin-top: 5px; color: #1e3355; font-size: clamp(29px, 3vw, 36px);
  font-weight: 800; line-height: 1.1; letter-spacing: -.04em; font-variant-numeric: tabular-nums;
}
.stat-hint { margin: 0; color: #94a3b8; font-size: 11px; line-height: 1.5; }
.trend { display: inline-flex; align-items: center; gap: 4px; padding: 3px 7px; border-radius: 999px; font-size: 10px; font-weight: 700; }
.trend-up { background: #e8f8ef; color: #15803d; }
.trend-down { background: #fef0f0; color: #dc2626; }
.trend-hint { font-size: 10px; }
.stat-progress { height: 7px; margin-top: 9px; overflow: hidden; border-radius: 999px; background: var(--accent-soft); }
.stat-progress span {
  display: block; height: 100%; border-radius: inherit; background: var(--accent);
  transform-origin: left; animation: grow-x .8s cubic-bezier(.22, 1, .36, 1) both;
}
.stat-spark { width: 100%; height: 34px; margin-top: 5px; color: var(--accent); overflow: visible; }
@keyframes grow-x { from { transform: scaleX(0); } }
@media (prefers-reduced-motion: reduce) { .stat-card, .stat-progress span { animation: none; transition: none; } }
</style>
