<script setup lang="ts">
import { computed } from 'vue'

interface BarItem {
  label: string
  value: number
}

const props = defineProps<{
  data: BarItem[]
  // Índice da barra em destaque. Por defeito, a última.
  highlight?: number
  unit?: string
}>()

const activeIndex = computed(() => props.highlight ?? props.data.length - 1)

// Escala mínima de 4 para o gráfico não ficar "cheio" com valores pequenos.
const scaleMax = computed(() => Math.max(4, ...props.data.map((item) => item.value)))

function barHeight(value: number): string {
  return value === 0 ? '4px' : `${(value / scaleMax.value) * 100}%`
}

// Labels do eixo Y (5 níveis).
const yLabels = computed(() => {
  const max = scaleMax.value
  const step = Math.ceil(max / 4)
  return Array.from({ length: 5 }, (_, i) => (max - i * step).toFixed(0))
})

const ariaLabel = computed(() =>
  props.data.map((item) => `${item.label}: ${item.value}`).join(', ')
)
</script>

<template>
  <div class="bar-chart" role="img" :aria-label="ariaLabel">
    <div class="chart-body">
      <div class="y-axis" aria-hidden="true">
        <span v-for="label in yLabels" :key="label">{{ label }}</span>
      </div>

      <div class="grid-lines" aria-hidden="true">
        <span v-for="n in 4" :key="n" />
      </div>

      <div
        class="columns"
        :style="{ gridTemplateColumns: `repeat(${data.length}, minmax(0, 1fr))` }"
      >
        <div
          v-for="(item, index) in data"
          :key="`${item.label}-${index}`"
          class="column"
          :title="`${item.label}: ${item.value}${unit ? ' ' + unit : ''}`"
        >
          <div
            class="bar"
            :class="{ active: index === activeIndex, empty: item.value === 0 }"
            :style="{ height: barHeight(item.value), animationDelay: `${index * 70}ms` }"
          >
            <span class="bar-value" v-if="item.value > 0">{{ item.value }}</span>
          </div>
        </div>
      </div>
    </div>

    <div
      class="axis"
      :style="{ gridTemplateColumns: `repeat(${data.length}, minmax(0, 1fr))` }"
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
</template>

<style scoped>
.bar-chart {
  width: 100%;
}

.chart-body {
  position: relative;
  height: 220px;
  padding-top: 36px;
  padding-left: 26px;
}

.y-axis {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  font-size: 11px;
  color: var(--tf-text-light);
  text-align: right;
  padding-right: 6px;
}

.y-axis span {
  white-space: nowrap;
}

.grid-lines {
  position: absolute;
  inset: 0 0 0 26px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.grid-lines span {
  display: block;
  height: 1px;
  background: repeating-linear-gradient(90deg, #e5e9f2 0 4px, transparent 4px 8px);
}

.columns {
  position: relative;
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
  border-radius: 10px 10px 4px 4px;
  background: linear-gradient(180deg, #c7d2fe, #a5b4fc);
  transform-origin: bottom;
  animation: grow-y 0.8s cubic-bezier(0.22, 1, 0.36, 1) both;
  transition: filter 0.2s ease;
}

.bar:hover {
  filter: brightness(0.94);
}

.bar.active {
  background: linear-gradient(180deg, #6366f1, #4338ca);
  box-shadow: 0 10px 20px -8px rgb(79 70 229 / 55%);
}

.bar.empty {
  border-radius: 4px;
  background: var(--tf-border-soft);
  box-shadow: none;
}

.bar-value {
  position: absolute;
  bottom: calc(100% + 6px);
  left: 50%;
  color: var(--tf-text-muted);
  font-size: 11px;
  font-weight: 700;
  transform: translateX(-50%);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.bar.active .bar-value {
  color: var(--tf-primary);
}

.axis {
  display: grid;
  gap: 14px;
  margin-top: 12px;
  text-align: center;
}

.axis span {
  color: var(--tf-text-muted);
  font-size: 12px;
  font-weight: 600;
  text-transform: capitalize;
}

.axis span.active {
  color: var(--tf-primary);
  font-weight: 700;
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
    padding-left: 20px;
  }
  .grid-lines {
    inset: 0 0 0 20px;
  }
  .y-axis {
    left: 0;
    padding-right: 4px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .bar {
    animation: none;
    transition: none;
  }
}
</style>
