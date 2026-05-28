<script setup lang="ts">
import { ElMessage } from 'element-plus'

defineProps<{ ips: string[] }>()

async function copyAll(ips: string[]) {
  await navigator.clipboard.writeText(ips.join(','))
  ElMessage.success('已复制全部 IP')
}
</script>

<template>
  <div class="ip-list">
    <span class="lbl">IP 地址：</span>
    <a v-for="ip in ips" :key="ip" class="ip mono">{{ ip }}</a>
    <el-button text type="primary" size="small" @click="copyAll(ips)">复制</el-button>
  </div>
</template>

<style scoped>
.ip-list { display: flex; flex-wrap: wrap; gap: 12px; align-items: center; font-size: 13px; }
.lbl { color: var(--ct-text-2); }
.ip { color: var(--ct-primary); cursor: pointer; text-decoration: underline; }
</style>
