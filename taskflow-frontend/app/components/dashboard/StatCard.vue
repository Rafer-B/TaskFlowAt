<script setup lang="ts">
import { computed, useId } from 'vue'

type Tone = 'indigo' | 'blue' | 'green' | 'red'
type IconName = 'folder' | 'bolt' | 'check' | 'alert'
type Trend = 'up' | 'down' | 'none'

const props = withDefaults(
  defineProps<{
    label: string
    value: number | string
    hint?: string
    tone?: Tone
    icon?: IconName
    // Percentagem (0-100) para mostrar uma barra de progresso.
    progress?: number
    // Série de valores para desenhar uma mini linha de evolução.
    spark?: number[]
    // Tendência: 'up' (melhorou), 'down' (piorou) ou 'none'.
    trend?: Trend
  }>(),
  {
    hint: '',
    tone: 'indigo',
    icon: 'folder',
    progress: undefined,
    spark: () => [],
    trend: 'none'
  }
)

const uid = useId()

const icons: Record<IconName, string[]> = {
  folder: ['M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z'],
  bolt: ['M13 2 4 14h7l-1 8 9-12h-7z'],
  check: ['M22 11.08V12a10 10 0 1 1-5.93-9.14', 'M22 4 12 14.01l-3-3'],
  alert: [
    'M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z',
    'M12 9v4',
    'M12 17h.01'
  ]
}

const iconPaths = computed(() => icons[props.icon])

const clampedProgress = computed(() =>
  props.progress === undefined ? undefined : Math.min(100, Math.max(0, props.progress))
)

// Converte a série em pontos de um SVG de 100 x 32.
const sparkPoints = computed(() => {
  if (props.spark.length < 2) return []

  const min = Math.min(...props.spark)
  const max = Math.max(...props.spark)
  const range = max - min || 1
  const step = 100 / (props.spark.length - 1)

  return props.spark.map((value, index) => ({
    x: Number((index * step).toFixed(2)),
    y: Number((28 - ((value - min) / range) * 24).toFixed(2))
  }))
})

const sparkLine = computed(() => sparkPoints.value.map((p) => `${p.x},${p.y}`).join(' '))
const sparkArea = computed(() =>
  sparkPoints.value.length ? `0,32 ${sparkLine.value} 100,32` : ''
)

const trendMark = computed(() => (props.trend === 'up' ? '▲' : '▼'))
</script>

<template>
  <article class="stat-card" :class="`tone-${tone}`">
    <div class="stat-top">
      <div class="stat-lead">
        <span class="stat-label">{{ label }}</span>
        <span
          v-if="trend !== 'none'"
          class="trend"
          :class="`trend-${trend}`"
          :aria-label="`Tendência ${trend === 'up' ? 'positiva' : 'negativa'}`"
        >
          <span class="trend-mark" aria-hidden="true">{{ trendMark }}</span>
          <span v-if="hint" class="trend-value">{{ hint }}</span>
        </span>
      </div>
      <span class="stat-icon" aria-hidden="true">
        <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path v-for="path in iconPaths" :key="path" :d="path" />
        </svg>
      </span>
    </div>

    <strong class="stat-value">{{ value }}</strong>

    <div
      v-if="clampedProgress !== undefined"
      class="stat-progress"
      role="progressbar"
      :aria-valuenow="clampedProgress"
      aria-valuemin="0"
      aria-valuemax="100"
      :aria-label="label"
    >
      <span :style="{ width: `${clampedProgress}%` }" />
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
          <stop offset="0%" stop-color="currentColor" stop-opacity="0.28" />
          <stop offset="100%" stop-color="currentColor" stop-opacity="0" />
        </linearGradient>
      </defs>
      <polygon :points="sparkArea" :fill="`url(#spark-${uid})`" />
      <polyline
        :points="sparkLine"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
        vector-effect="non-scaling-stroke"
      />
    </svg>
  </article>
</template>

<style scoped>
.stat-card {
  --accent: #4f46e5;
  --accent-soft: #eef2ff;

  position: relative;
  display: flex;
  flex-direction: column;
  gap: 6px;
  overflow: hidden;
  padding: 20px 22px 22px;
  border: 1px solid var(--tf-border);
  border-radius: var(--tf-radius);
  background: var(--tf-surface);
  box-shadow: var(--tf-shadow);
  transition: transform var(--tf-transition), box-shadow var(--tf-transition);
}

.stat-card::before {
  content: '';
  position: absolute;
  inset: 0 0 auto;
  height: 3px;
  background: var(--accent);
  opacity: 0.85;
}

.stat-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--tf-shadow-lg);
}

.tone-blue {
  --accent: #3b82f6;
  --accent-soft: #eff6ff;
}

.tone-green {
  --accent: #15803d;
  --accent-soft: #ecfdf5;
}

.tone-red {
  --accent: #b91c1c;
  --accent-soft: #fef2f2;
}

.stat-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.stat-lead {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.stat-label {
  color: var(--tf-text-muted);
  font-size: 13px;
  font-weight: 500;
}

.trend {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 999px;
}

.trend.up { background: var(--tf-success-soft); color: var(--tf-success); }
.trend.down { background: var(--tf-danger-soft); color: var(--tf-danger); }

.trend-mark {
  line-height: 1;
}

.trend-value {
  font-size: 11px;
  opacity: 0.9;
}

.stat-icon {
  display: grid;
  width: 38px;
  height: 38px;
  place-items: center;
  border-radius: 12px;
  background: var(--accent-soft);
  color: var(--accent);
}

.stat-value {
  margin-top: 8px;
  color: var(--tf-text);
  font-size: 36px;
  font-weight: 700;
  line-height: 1.1;
  letter-spacing: -0.5px;
  font-variant-numeric: tabular-nums;
}

.stat-progress {
  height: 6px;
  margin-top: 10px;
  overflow: hidden;
  border-radius: 999px;
  background: var(--accent-soft);
}

.stat-progress span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--accent);
  transform-origin: left;
  animation: grow-x 0.9s cubic-bezier(0.22, 1, 0.36, 1) both;
}

.stat-spark {
  width: 100%;
  height: 34px;
  margin-top: 10px;
  color: var(--accent);
}

@keyframes grow-x {
  from {
    transform: scaleX(0);
  }
}

@media (prefers-reduced-motion: reduce) {
  .stat-card,
  .stat-progress span {
    animation: none;
    transition: none;
  }
}
</style>
