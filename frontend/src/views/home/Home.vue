<script setup lang="ts">
import { onMounted, ref } from 'vue'
import * as echarts from 'echarts'

const chartEl = ref<HTMLDivElement>()

onMounted(() => {
  if (!chartEl.value) return
  const chart = echarts.init(chartEl.value)
  const data = Array.from({ length: 60 }, (_, i) =>
    [`${i + 1}`, 1000 + i * 80 + Math.sin(i / 3) * 240 + Math.random() * 80]
  )
  chart.setOption({
    grid: { left: 40, right: 16, top: 20, bottom: 30 },
    xAxis: {
      type: 'category',
      data: data.map((d) => d[0]),
      axisLabel: { color: '#6B7280' },
      axisLine: { lineStyle: { color: '#1F2937' } }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#6B7280' },
      splitLine: { lineStyle: { color: '#1F2937' } }
    },
    tooltip: { trigger: 'axis' },
    series: [
      {
        type: 'line',
        smooth: true,
        data: data.map((d) => d[1]),
        symbol: 'none',
        lineStyle: { width: 2, color: '#10B981' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(16,185,129,0.35)' },
            { offset: 1, color: 'rgba(16,185,129,0.01)' }
          ])
        }
      }
    ]
  })
  window.addEventListener('resize', () => chart.resize())
})
</script>

<template>
  <section class="hero">
    <h1>
      Welcome to <span class="grad">Copy Trader</span>,<br />
      where precision meets performance
    </h1>
    <p class="lead">
      跨交易所 · 跨数据源 · 智能合约跟单系统 —— 用工程师的方法解决跟单延迟、风控与归因问题
    </p>
    <div class="cta-row">
      <router-link to="/console" class="cta primary">立即体验</router-link>
      <router-link to="/tutorial" class="cta ghost">使用教程</router-link>
    </div>

    <div class="orbits" aria-hidden="true">
      <div class="planet center">CT</div>
      <div class="planet p1">BTC</div>
      <div class="planet p2">ETH</div>
      <div class="planet p3">SOL</div>
      <div class="planet p4">HYPE</div>
      <div class="ring r1"></div>
      <div class="ring r2"></div>
      <div class="ring r3"></div>
    </div>
  </section>

  <section class="features">
    <h2 class="section-title">智能跟单系统 · 四大卖点</h2>
    <div class="feature-grid">
      <div class="feature-card">
        <div class="feature-num">01</div>
        <h3>极致低延迟</h3>
        <p>毫秒级响应速度，即使交易员执行 100 单，我们仍能在 2 秒内完成所有跟单操作，体验极速交易。</p>
      </div>
      <div class="feature-card">
        <div class="feature-num">02</div>
        <h3>跨交易所无缝跟单</h3>
        <p>无论是币安还是欧易，均可无缝跟踪顶尖交易员；跨平台操作，让每一笔机会都尽在掌握。</p>
      </div>
      <div class="feature-card">
        <div class="feature-num">03</div>
        <h3>全方位跟踪支持</h3>
        <p>满员状态、私域带单、隐藏仓位及非带单员，无论市场如何变化，您都能随时跟踪确保每一笔交易的精准执行。</p>
      </div>
      <div class="feature-card">
        <div class="feature-num">04</div>
        <h3>科学仓位管理</h3>
        <p>合理分配仓位、优化风险与回报；系统智能调整每一笔交易的仓位，确保资金利用效率最大化。</p>
      </div>
    </div>
  </section>

  <section class="chart-section">
    <div class="chart-wrap">
      <div class="chart-meta">
        <h2 class="section-title">资金效益最大化 · 收益示例</h2>
        <p class="muted">示意数据，仅作 UI 展示，不代表实际收益。</p>
      </div>
      <div ref="chartEl" class="chart"></div>
    </div>
  </section>

  <footer class="public-footer">
    <div class="footer-cols">
      <div>
        <h4>产品</h4>
        <a>交易员广场</a>
        <a>自选跟单</a>
        <a>Hyperliquid Vault</a>
      </div>
      <div>
        <h4>资源</h4>
        <a>使用教程</a>
        <a>API 文档</a>
        <a>更新日志</a>
      </div>
      <div>
        <h4>友情链接</h4>
        <a href="https://www.binance.com" target="_blank">Binance</a>
        <a href="https://www.okx.com" target="_blank">OKX</a>
        <a href="https://hyperliquid.xyz" target="_blank">Hyperliquid</a>
        <a href="https://www.bicoin.com.cn" target="_blank">币Coin</a>
      </div>
    </div>
    <div class="copyright">© 2026 Copy Trader · 跨交易所智能跟单系统</div>
  </footer>
</template>

<style scoped>
.hero {
  position: relative;
  min-height: 70vh;
  padding: 80px 32px 60px;
  text-align: center;
}
.hero h1 {
  font-size: 56px;
  font-weight: 700;
  line-height: 1.15;
  margin: 0 0 24px;
  color: #fff;
  letter-spacing: -0.02em;
}
.grad {
  background: linear-gradient(135deg, #10B981 0%, #A3E635 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}
.lead { color: #9CA3AF; font-size: 18px; max-width: 720px; margin: 0 auto 40px; }
.cta-row { display: flex; gap: 14px; justify-content: center; }
.cta {
  padding: 13px 36px;
  border-radius: 999px;
  font-weight: 600;
  font-size: 15px;
}
.cta.primary { background: var(--ct-space-accent); color: #062013; }
.cta.ghost { color: #e5e7eb; border: 1px solid rgba(255,255,255,0.18); }

.orbits {
  position: relative;
  margin: 80px auto 0;
  width: 520px;
  height: 360px;
  max-width: 90vw;
}
.planet {
  position: absolute;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 700;
  font-size: 14px;
  box-shadow: 0 10px 30px rgba(16, 185, 129, 0.3);
}
.planet.center {
  left: 50%; top: 50%; transform: translate(-50%, -50%);
  width: 96px; height: 96px;
  background: radial-gradient(circle at 30% 30%, #34D399, #047857);
  font-size: 24px;
}
.planet.p1 { left: 15%; top: 30%; width: 40px; height: 40px; background: linear-gradient(135deg, #F59E0B, #D97706); font-size: 11px; }
.planet.p2 { right: 12%; top: 18%; width: 46px; height: 46px; background: linear-gradient(135deg, #6366F1, #4338CA); font-size: 11px; }
.planet.p3 { right: 18%; bottom: 14%; width: 38px; height: 38px; background: linear-gradient(135deg, #A78BFA, #7C3AED); font-size: 11px; }
.planet.p4 { left: 22%; bottom: 22%; width: 42px; height: 42px; background: linear-gradient(135deg, #14B8A6, #0F766E); font-size: 11px; }
.ring {
  position: absolute;
  border: 1px dashed rgba(255, 255, 255, 0.12);
  border-radius: 50%;
  left: 50%; top: 50%;
  transform: translate(-50%, -50%);
}
.ring.r1 { width: 200px; height: 200px; }
.ring.r2 { width: 320px; height: 320px; }
.ring.r3 { width: 460px; height: 460px; }

.features { padding: 80px 32px; max-width: 1180px; margin: 0 auto; }
.section-title { font-size: 26px; color: #fff; margin: 0 0 28px; }
.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 18px;
}
.feature-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 16px;
  padding: 26px;
  transition: transform 0.18s, border-color 0.18s;
}
.feature-card:hover { transform: translateY(-3px); border-color: rgba(16, 185, 129, 0.4); }
.feature-num { color: var(--ct-space-accent); font-weight: 700; font-size: 13px; letter-spacing: 0.15em; }
.feature-card h3 { color: #fff; font-size: 18px; margin: 12px 0 10px; }
.feature-card p { color: #9CA3AF; font-size: 13px; line-height: 1.7; margin: 0; }

.chart-section { padding: 40px 32px 100px; max-width: 1180px; margin: 0 auto; }
.chart-wrap {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 18px;
  padding: 24px;
}
.chart { width: 100%; height: 320px; }
.muted { color: #6B7280; margin: 0; font-size: 13px; }

.public-footer { padding: 60px 32px 30px; border-top: 1px solid rgba(255, 255, 255, 0.05); }
.footer-cols {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 32px;
  max-width: 1180px;
  margin: 0 auto;
}
.footer-cols h4 { color: #d1d5db; font-size: 14px; margin: 0 0 14px; }
.footer-cols a { display: block; color: #6B7280; font-size: 13px; padding: 4px 0; cursor: pointer; }
.footer-cols a:hover { color: var(--ct-space-accent); }
.copyright { text-align: center; color: #4B5563; font-size: 12px; margin-top: 40px; }

@media (max-width: 768px) {
  .hero h1 { font-size: 36px; }
  .lead { font-size: 15px; }
  .orbits { display: none; }
}
</style>
