<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  data: number[]
  width?: number
  height?: number
  color?: string
  strokeWidth?: number
}
const props = withDefaults(defineProps<Props>(), {
  width: 80,
  height: 16,
  color: '#FFB400',
  strokeWidth: 1
})

const path = computed(() => {
  if (!props.data || props.data.length < 2) return ''
  const data = props.data
  const min = Math.min(...data)
  const max = Math.max(...data)
  const range = max - min || 1
  const w = props.width
  const h = props.height
  const pad = 1
  const stepX = (w - pad * 2) / (data.length - 1)
  return data
    .map((v, i) => {
      const x = pad + i * stepX
      const y = h - pad - ((v - min) / range) * (h - pad * 2)
      return `${i === 0 ? 'M' : 'L'}${x.toFixed(2)},${y.toFixed(2)}`
    })
    .join(' ')
})
</script>

<template>
  <svg
    :width="width"
    :height="height"
    :viewBox="`0 0 ${width} ${height}`"
    preserveAspectRatio="none"
    class="ct-sparkline"
  >
    <path
      :d="path"
      fill="none"
      :stroke="color"
      :stroke-width="strokeWidth"
      stroke-linejoin="round"
      stroke-linecap="round"
    />
  </svg>
</template>

<style scoped>
.ct-sparkline {
  display: block;
}
</style>
