<script setup lang="ts">
import { computed } from 'vue'

interface Segment {
  label: string
  value: number
  color: string
}

const props = defineProps<{
  segments: Segment[]
  centerValue: string | number
  centerLabel: string
}>()

const RADIUS = 42
const CIRCUMFERENCE = 2 * Math.PI * RADIUS

const total = computed(() => props.segments.reduce((sum, segment) => sum + segment.value, 0))

const arcs = computed(() => {
  const visible = props.segments.filter((segment) => segment.value > 0).length
  // Pequeno espaço entre segmentos, só quando há mais do que um.
  const gap = visible > 1 ? 2.5 : 0
  let accumulated = 0

  return props.segments.map((segment) => {
    const fraction = total.value ? segment.value / total.value : 0
    const full = fraction * CIRCUMFERENCE
    const length = Math.max(full - gap, 0)
    const arc = {
      ...segment,
      dasharray: `${length} ${CIRCUMFERENCE - length}`,
      dashoffset: -accumulated,
      percent: Math.round(fraction * 100)
    }

    accumulated += full
    return arc
  })
})

const ariaLabel = computed(() =>
  props.segments.map((segment) => `${segment.label}: ${segment.value}`).join(', ')
)
</script>

<template>
  <div class="donut">
    <div class="donut-figure">
      <svg viewBox="0 0 100 100" role="img" :aria-label="ariaLabel">
        <circle class="donut-track" cx="50" cy="50" :r="RADIUS" fill="none" stroke-width="11" />
        <g transform="rotate(-90 50 50)">
          <circle
            v-for="(arc, index) in arcs"
            v-show="arc.value > 0"
            :key="arc.label"
            class="donut-arc"
            cx="50"
            cy="50"
            :r="RADIUS"
            fill="none"
            :stroke="arc.color"
            stroke-width="11"
            :stroke-dasharray="arc.dasharray"
            :stroke-dashoffset="arc.dashoffset"
            :style="{ animationDelay: `${index * 120}ms` }"
          />
        </g>
      </svg>

      <div class="donut-center">
        <strong>{{ centerValue }}</strong>
        <span>{{ centerLabel }}</span>
      </div>
    </div>

    <ul class="donut-legend">
      <li v-for="arc in arcs" :key="arc.label">
        <span class="dot" :style="{ background: arc.color }"></span>
        <span class="legend-label">{{ arc.label }}</span>
        <span class="legend-value">{{ arc.value }}</span>
        <span class="legend-percent">{{ arc.percent }}%</span>
      </li>
    </ul>
  </div>
</template>

<style scoped>

.donut {
  display: grid;
  grid-template-columns: minmax(150px, 210px) 1fr;
  align-items: center;
  gap: 30px;
  width: 100%;
}

.donut-figure {
  position: relative;
  width: 100%;
  max-width: 210px;
  aspect-ratio: 1;
  margin: auto;
}

.donut-figure svg {
  display: block;
  width: 100%;
  height: 100%;
}

.donut-track {
  stroke: #edf1f7;
}

.donut-arc {
  animation: donut-in 0.8s ease both;
  transition: stroke-width 0.2s ease;
}

.donut-arc:hover {
  stroke-width: 13;
}

.donut-center {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.donut-center strong {
  color: #172b4d;
  font-size: 36px;
  font-weight: 800;
  line-height: 1;
}

.donut-center span {
  margin-top: 7px;
  color: #8290a5;
  font-size: 12px;
}

.donut-legend {
  display: grid;
  gap: 15px;
  width: 100%;
  margin: 0;
  padding: 0;
  list-style: none;
}

.donut-legend li {
  display: grid;
  grid-template-columns: 10px 1fr auto 42px;
  align-items: center;
  gap: 10px;
  font-size: 13px;
}

.dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
}

.legend-label {
  color: #526580;
}

.legend-value {
  color: #172b4d;
  font-weight: 700;
}

.legend-percent {
  color: #94a3b8;
  text-align: right;
}

@keyframes donut-in {
  from {
    opacity: 0;
  }
}

@media (max-width: 600px) {
  .donut {
    grid-template-columns: 1fr;
    gap: 22px;
  }

  .donut-figure {
    width: 180px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .donut-arc {
    animation: none;
    transition: none;
  }
}

</style>
