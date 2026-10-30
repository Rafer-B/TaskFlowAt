
<script setup lang="ts">
import { computed } from 'vue'

interface BarItem {
  label: string
  value: number
}

const props = defineProps<{
  data: BarItem[]
  highlight?: number
  unit?: string
}>()

const activeIndex = computed(
  () => props.highlight ?? props.data.length - 1
)

// Calcula uma escala arredondada, sempre iniciada em zero.
const scaleMax = computed(() => {
  const maxValue = Math.max(
    0,
    ...props.data.map(item => item.value)
  )

  const step = Math.max(1, Math.ceil(maxValue / 4))

  return step * 4
})

// Cinco níveis: máximo, 3/4, metade, 1/4 e zero.
const yLabels = computed(() => {
  const step = scaleMax.value / 4

  return Array.from(
    { length: 5 },
    (_, index) => scaleMax.value - index * step
  )
})

function barHeight(value: number): string {
  if (value <= 0) return '4px'

  return `${Math.min((value / scaleMax.value) * 100, 100)}%`
}

const ariaLabel = computed(() =>
  props.data
    .map(item => `${item.label}: ${item.value}`)
    .join(', ')
)
</script>

<template>
  <div
    v-if="data.length"
    class="bar-chart"
    role="img"
    :aria-label="ariaLabel"
  >
    <div class="chart-body">
      <div class="y-axis" aria-hidden="true">
        <span v-for="label in yLabels" :key="label">
          {{ label }}
        </span>
      </div>

      <div class="grid-lines" aria-hidden="true">
        <span v-for="n in 5" :key="n"></span>
      </div>

      <div
        class="columns"
        :style="{
          gridTemplateColumns: `repeat(${data.length}, minmax(0, 1fr))`
        }"
      >
        <div
          v-for="(item, index) in data"
          :key="`${item.label}-${index}`"
          class="column"
          :title="`${item.label}: ${item.value}${unit ? ' ' + unit : ''}`"
        >
          <div
            class="bar"
            :class="{
              active: index === activeIndex,
              empty: item.value <= 0
            }"
            :style="{
              height: barHeight(item.value),
              animationDelay: `${index * 70}ms`
            }"
          >
            <span v-if="item.value > 0" class="bar-value">
              {{ item.value }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <div
      class="axis"
      :style="{
        gridTemplateColumns: `repeat(${data.length}, minmax(0, 1fr))`
      }"
    >
      <span
        v-for="(item, index) in data"
        :key="`${item.label}-axis-${index}`"
        :class="{ active: index === activeIndex }"
      >
        {{ item.label }}
      </span>
    </div>
  </div>

  <div v-else class="chart-empty">
    <span class="empty-icon">▥</span>
    <strong>Sem dados disponíveis</strong>
    <p>As conclusões das tarefas serão apresentadas aqui.</p>
  </div>
</template>

<style scoped>
.bar-chart {
  width: 100%;
}

.chart-body {
  position: relative;
  height: 220px;
  padding: 12px 0 0 30px;
  box-sizing: border-box;
}

.y-axis {
  position: absolute;
  left: 0;
  top: 12px;
  bottom: 0;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding-right: 7px;
  color: var(--tf-text-light, #94a3b8);
  font-size: 11px;
  font-variant-numeric: tabular-nums;
  text-align: right;
}

.grid-lines {
  position: absolute;
  inset: 12px 0 0 30px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  pointer-events: none;
}

.grid-lines span {
  display: block;
  height: 1px;
  background: repeating-linear-gradient(
    90deg,
    #e5eaf3 0 4px,
    transparent 4px 8px
  );
}

.columns {
  position: relative;
  z-index: 1;
  display: grid;
  height: 100%;
  gap: 14px;
}

.column {
  display: flex;
  align-items: flex-end;
  justify-content: center;
  height: 100%;
}

.bar {
  position: relative;
  width: min(100%, 46px);
  min-height: 4px;
  border-radius: 9px 9px 4px 4px;
  background: linear-gradient(180deg, #bfdbfe, #93c5fd);
  transform-origin: bottom;
  animation: grow-y 0.8s cubic-bezier(0.22, 1, 0.36, 1) both;
  transition: filter 0.2s ease, background 0.2s ease;
}

.bar:hover {
  filter: brightness(0.94);
}

.bar.active {
  background: linear-gradient(180deg, #60a5fa, #2563eb);
  box-shadow: 0 8px 18px -8px rgb(37 99 235 / 45%);
}

.bar.empty {
  border-radius: 4px;
  background: #e8edf5;
  box-shadow: none;
}

.bar-value {
  position: absolute;
  bottom: calc(100% + 7px);
  left: 50%;
  color: #64748b;
  font-size: 11px;
  font-weight: 700;
  transform: translateX(-50%);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.bar.active .bar-value {
  color: #2563eb;
}

.axis {
  display: grid;
  gap: 14px;
  margin-top: 12px;
  text-align: center;
}

.axis span {
  overflow: hidden;
  color: #8290a5;
  font-size: 11px;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.axis span.active {
  color: #2563eb;
  font-weight: 700;
}

.chart-empty {
  display: flex;
  min-height: 220px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 9px;
  text-align: center;
}

.empty-icon {
  color: #94a3b8;
  font-size: 28px;
}

.chart-empty strong {
  color: #334155;
  font-size: 14px;
}

.chart-empty p {
  margin: 0;
  color: #94a3b8;
  font-size: 12px;
}

@keyframes grow-y {
  from {
    transform: scaleY(0);
  }
}

@media (max-width: 520px) {
  .columns,
  .axis {
    gap: 6px;
  }

  .chart-body {
    padding-left: 24px;
  }

  .grid-lines {
    left: 24px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .bar {
    animation: none;
    transition: none;
  }
}
</style>
