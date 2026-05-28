<script setup lang="ts">
interface LogRow {
  ts: string
  kind: 'FILL' | 'SIGNAL' | 'SUBSCR' | 'WARN' | 'REJECT'
  body: string
  meta: string
}
interface Props {
  rows: LogRow[]
  maxHeight?: string
}
withDefaults(defineProps<Props>(), { maxHeight: '240px' })

function kindClass(k: LogRow['kind']) {
  return {
    FILL:   'ev-fill',
    SIGNAL: 'ev-sig',
    SUBSCR: 'ev-sub',
    WARN:   'ev-warn',
    REJECT: 'ev-err'
  }[k]
}
function kindLabel(k: LogRow['kind']) {
  return k.padEnd(7, ' ')
}
</script>

<template>
  <div class="term-log" :style="{ maxHeight }">
    <div v-for="(r, i) in rows" :key="i" class="log-row">
      <span class="ts">[{{ r.ts }}]</span>
      <span :class="kindClass(r.kind)">{{ kindLabel(r.kind) }}</span>
      <b>{{ r.body }}</b>
      <span class="meta">{{ r.meta }}</span>
    </div>
  </div>
</template>

<style scoped>
.term-log {
  overflow-y: auto;
  font-family: var(--ct-font-mono);
  font-size: 11px;
  line-height: 1.7;
  color: var(--ct-text-2);
  white-space: nowrap;
}
.log-row {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
}
.log-row .meta {
  color: var(--ct-text-2);
  margin-left: 8px;
  white-space: pre;
}
.ts { color: var(--ct-text-dim); margin-right: 8px; }
.ev-fill { color: var(--ct-pos); margin-right: 8px; white-space: pre; }
.ev-sig  { color: var(--ct-amber); margin-right: 8px; white-space: pre; }
.ev-sub  { color: var(--ct-text-2); margin-right: 8px; white-space: pre; }
.ev-warn { color: var(--ct-warn-soft); margin-right: 8px; white-space: pre; }
.ev-err  { color: var(--ct-neg); margin-right: 8px; white-space: pre; }
.term-log b { color: var(--ct-text); font-weight: 500; margin-right: 8px; }
</style>
