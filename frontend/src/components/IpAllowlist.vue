<script setup lang="ts">
import { ElMessage } from 'element-plus'

defineProps<{ ips: string[] }>()

async function copyAll(ips: string[]) {
  await navigator.clipboard.writeText(ips.join(', '))
  ElMessage.success('EGRESS IPS COPIED')
}
</script>

<template>
  <div class="ip-list">
    <span class="lbl">EGRESS:</span>
    <span v-for="(ip, i) in ips" :key="ip" class="ip">
      {{ ip }}<span v-if="i < ips.length - 1" class="sep"> · </span>
    </span>
    <button class="copy-btn" @click="copyAll(ips)">COPY</button>
  </div>
</template>

<style scoped>
.ip-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
  font-size: 11px;
  font-family: var(--ct-font-mono);
  font-variant-numeric: tabular-nums;
}
.lbl {
  color: var(--ct-text-3);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  margin-right: 4px;
}
.ip {
  color: var(--ct-amber);
}
.sep { color: var(--ct-text-dim); }
.copy-btn {
  margin-left: 8px;
  background: transparent;
  border: 1px solid var(--ct-divider-strong);
  color: var(--ct-text-2);
  font-family: var(--ct-font-mono);
  font-size: 10px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  padding: 2px 8px;
  cursor: pointer;
}
.copy-btn:hover {
  color: var(--ct-amber);
  border-color: var(--ct-amber);
}
</style>
