import { createI18n } from 'vue-i18n'
import zh from './zh-CN.json'
import en from './en.json'

export const i18n = createI18n({
  legacy: false,
  locale: localStorage.getItem('locale') || 'zh-CN',
  fallbackLocale: 'zh-CN',
  messages: {
    'zh-CN': zh,
    en
  }
})

export function setLocale(locale: 'zh-CN' | 'en') {
  i18n.global.locale.value = locale
  localStorage.setItem('locale', locale)
}
