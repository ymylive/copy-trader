<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref } from 'vue'
import { formatUTC } from '@/utils/format'

interface Props {
  uid?: string | number
  service?: string
}
withDefaults(defineProps<Props>(), {
  uid: '52494073',
  service: '220D 13H'
})

const utc = ref(formatUTC())
let timer: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  utc.value = formatUTC()
  timer = setInterval(() => { utc.value = formatUTC() }, 1000)
})
onBeforeUnmount(() => { if (timer) clearInterval(timer) })
</script>

<template>
  <div class="statusbar">
    <span><span class="dot"></span>HOST ONLINE</span>
    <span class="sep">|</span>
    <span>REDIS 3.2K OPS/S</span>
    <span class="sep">|</span>
    <span>WS 1247 SUB</span>
    <span class="sep">|</span>
    <span>CPU 12%</span>
    <span class="sep">|</span>
    <span class="hide-sm">MEM 4.1G / 16G</span>
    <span class="sep hide-sm">|</span>
    <span><span class="dot amber"></span>LATENCY 1.8MS</span>
    <span class="right">
      <span>{{ utc }}</span>
      <span class="sep">|</span>
      <span>UID {{ uid }}</span>
      <span class="sep hide-sm">|</span>
      <span class="hide-sm">SVC {{ service }}</span>
    </span>
  </div>
</template>
