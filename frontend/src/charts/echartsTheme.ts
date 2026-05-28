import * as echarts from 'echarts'

/**
 * Bloomberg Terminal · ECharts theme (D1).
 * Amber single-line / hairline grid / mono tooltip / no shadow.
 */
const bloombergTheme = {
  color: ['#FFB400', '#22C55E', '#EF4444', '#60A5FA', '#A78BFA', '#1FCCB1'],
  backgroundColor: 'transparent',
  textStyle: {
    fontFamily: 'JetBrains Mono, IBM Plex Mono, ui-monospace, monospace',
    color: '#6B7280',
    fontSize: 10
  },
  title: {
    textStyle: {
      color: '#E6E8EA',
      fontFamily: 'JetBrains Mono, monospace',
      fontWeight: 500,
      fontSize: 12
    }
  },
  grid: {
    left: 50,
    right: 24,
    top: 22,
    bottom: 30,
    containLabel: false
  },
  categoryAxis: {
    axisLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } },
    axisTick: { show: false },
    axisLabel: { color: '#6B7280', fontSize: 9, fontFamily: 'JetBrains Mono, monospace' },
    splitLine: { show: false, lineStyle: { color: 'rgba(255,255,255,0.04)' } }
  },
  valueAxis: {
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { color: '#6B7280', fontSize: 9, fontFamily: 'JetBrains Mono, monospace' },
    splitLine: { lineStyle: { color: 'rgba(255,255,255,0.04)' } }
  },
  legend: {
    textStyle: {
      color: '#A2A8B2',
      fontFamily: 'JetBrains Mono, monospace',
      fontSize: 10
    }
  },
  tooltip: {
    backgroundColor: '#0A0E14',
    borderColor: '#FFB400',
    borderWidth: 1,
    padding: 8,
    textStyle: {
      color: '#E6E8EA',
      fontFamily: 'JetBrains Mono, monospace',
      fontSize: 11
    },
    axisPointer: {
      lineStyle: { color: 'rgba(255,180,0,0.4)', width: 1, type: 'dashed' },
      crossStyle: { color: 'rgba(255,180,0,0.4)' }
    },
    extraCssText: 'border-radius: 0; box-shadow: none;'
  },
  line: {
    itemStyle: { borderWidth: 0 },
    lineStyle: { width: 1.5 },
    symbolSize: 4,
    symbol: 'none',
    smooth: false
  },
  candlestick: {
    itemStyle: {
      color: '#22C55E',
      color0: '#EF4444',
      borderColor: '#22C55E',
      borderColor0: '#EF4444',
      borderWidth: 1
    }
  },
  bar: {
    itemStyle: { barBorderWidth: 0, barBorderColor: 'transparent' }
  }
}

let registered = false
export function registerBloombergTheme() {
  if (registered) return
  echarts.registerTheme('bloomberg', bloombergTheme)
  registered = true
}

export const BLOOMBERG_THEME = 'bloomberg'
