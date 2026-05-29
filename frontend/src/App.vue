<script setup lang="ts">
// Root layout — pages render their own chrome (public site vs console).
// Element Plus locale follows the active i18n locale so EP-internal strings
// (pagination, datepicker, table empty-text, etc.) match the UI language.
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElConfigProvider } from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import en from 'element-plus/es/locale/lang/en'

const { locale } = useI18n()
const elLocale = computed(() => (locale.value === 'en' ? en : zhCn))
</script>

<template>
  <el-config-provider :locale="elLocale">
    <router-view />
  </el-config-provider>
</template>
