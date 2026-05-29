import { createI18n } from 'vue-i18n'
import zh from './zh-CN.json'
import en from './en.json'

/* ── marketing-site message modules (per-page; deep-merged below) ── */
import layout from './marketing/layout'
import home from './marketing/home'
import features from './marketing/features'
import pricing from './marketing/pricing'

export const i18n = createI18n({
  legacy: false,
  locale: localStorage.getItem('locale') || 'zh-CN',
  fallbackLocale: 'zh-CN',
  messages: {
    'zh-CN': {
      ...zh,
      marketing: {
        layout: layout['zh-CN'],
        home: home['zh-CN'],
        features: features['zh-CN'],
        pricing: pricing['zh-CN'],
      },
    },
    en: {
      ...en,
      marketing: {
        layout: layout.en,
        home: home.en,
        features: features.en,
        pricing: pricing.en,
      },
    },
  },
})

// keep <html lang> in sync with the active locale (SEO / screen readers / translation tools)
document.documentElement.lang = i18n.global.locale.value

export function setLocale(locale: 'zh-CN' | 'en') {
  i18n.global.locale.value = locale
  localStorage.setItem('locale', locale)
  document.documentElement.lang = locale
}
