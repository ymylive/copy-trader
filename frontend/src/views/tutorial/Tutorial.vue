<script setup lang="ts">
import { ref } from 'vue'

const active = ref('binance')

const exchanges = [
  {
    key: 'binance',
    name: 'Binance',
    steps: [
      '登录 binance.com → 进入 用户中心 - API 管理',
      '点击「创建 API」并完成 2FA 校验',
      '权限勾选：启用读取、启用合约（USDS-M / COIN-M 期货）',
      '在合约设置里切换为「双向持仓模式」',
      '复制 API Key / Secret Key 到本平台账户管理',
      '如需限制 IP 白名单，将本平台展示的 4 个出口 IP 一并加入'
    ]
  },
  {
    key: 'okx',
    name: 'OKX（欧易）',
    steps: [
      '登录 okx.com → 个人中心 - API',
      '创建 API，用途选「API 交易」',
      '权限勾选：交易（必选）、读取',
      '设置密码短语（passphrase），妥善保存',
      '账户模式切换为「双向持仓」',
      '将 API Key / Secret / Passphrase 三段信息填入本平台'
    ]
  },
  {
    key: 'gate',
    name: 'Gate.io',
    steps: [
      '登录 gate.io → API 管理',
      '为本平台单独创建一组 API Key',
      '权限：永续合约 = 读写；其他选择只读',
      '在合约设置里启用「双向持仓」',
      '将 API Key / Secret 填入本平台'
    ]
  },
  {
    key: 'bitget',
    name: 'Bitget',
    steps: [
      '登录 bitget.com → API 管理',
      '创建两类 Key：合约交易 API-Key、带单账户 API-Key',
      '权限：合约交易、读取；按需开启带单',
      '切换为「双向持仓」',
      '将 API Key / Secret / Passphrase 填入本平台'
    ]
  }
]

const copyModes = [
  {
    name: '交易员广场',
    desc: '直接选择平台已上架的优质带单员，无延迟跟单。适合新手。',
    pros: ['一键启动', '无须任何配置', '官方维护数据']
  },
  {
    name: '自选跟单',
    desc: '搜索任意 ID/链接/昵称，支持公开和隐藏持仓，包含 Cookie 跟单（SVIP）。',
    pros: ['覆盖更广', '可跟未上架交易员', 'SVIP 用户支持 Cookie 实时']
  }
]
</script>

<template>
  <div class="tutorial-page">
    <h1 class="hero-title">使用教程</h1>
    <p class="hero-sub">5 分钟完成 API 创建 + 启动跟单</p>

    <div class="exchange-tabs">
      <el-tabs v-model="active" stretch>
        <el-tab-pane v-for="ex in exchanges" :key="ex.key" :label="ex.name" :name="ex.key">
          <div class="steps">
            <div v-for="(s, idx) in ex.steps" :key="idx" class="step">
              <div class="num-circle">{{ idx + 1 }}</div>
              <div class="step-text">{{ s }}</div>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <h2 class="section-title">跟单方式</h2>
    <div class="modes">
      <div v-for="m in copyModes" :key="m.name" class="mode-card">
        <h3>{{ m.name }}</h3>
        <p>{{ m.desc }}</p>
        <ul>
          <li v-for="p in m.pros" :key="p">{{ p }}</li>
        </ul>
      </div>
    </div>

    <h2 class="section-title">双向持仓模式</h2>
    <div class="note">
      本平台所有交易所均需开启 <b>双向持仓 (Hedge Mode)</b>，否则可能出现"开仓即平仓"现象。
      若交易所默认为单向持仓，请按交易所文档切换。
    </div>
  </div>
</template>

<style scoped>
.tutorial-page {
  max-width: 1080px;
  margin: 0 auto;
  padding: 40px 32px 100px;
  color: #e5e7eb;
}
.hero-title { font-size: 36px; color: #fff; margin: 0 0 8px; }
.hero-sub { color: #9CA3AF; margin: 0 0 32px; }
.exchange-tabs {
  background: rgba(14, 20, 27, 0.75);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 16px;
  padding: 20px 24px;
}
:deep(.el-tabs__nav-wrap::after) { background: rgba(255,255,255,0.08); }
:deep(.el-tabs__item) { color: #9CA3AF; }
:deep(.el-tabs__item.is-active) { color: var(--ct-primary); }
:deep(.el-tabs__active-bar) { background: var(--ct-primary); }
.steps { display: flex; flex-direction: column; gap: 14px; padding: 12px 0; }
.step { display: flex; gap: 14px; align-items: flex-start; }
.num-circle {
  flex-shrink: 0;
  width: 28px; height: 28px;
  background: linear-gradient(135deg, #10B981, #0D9488);
  color: #fff;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 13px;
}
.step-text { color: #d1d5db; font-size: 14px; line-height: 1.7; }
.section-title { font-size: 22px; color: #fff; margin: 36px 0 14px; }
.modes { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
.mode-card {
  background: rgba(14, 20, 27, 0.75);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 16px;
  padding: 22px 24px;
}
.mode-card h3 { color: var(--ct-primary); margin: 0 0 10px; }
.mode-card p { color: #d1d5db; line-height: 1.7; }
.mode-card ul { color: #9CA3AF; padding-left: 18px; margin: 8px 0 0; }
.mode-card li { padding: 2px 0; }
.note {
  background: rgba(245, 158, 11, 0.08);
  border: 1px solid rgba(245, 158, 11, 0.25);
  color: #FCD34D;
  padding: 14px 18px;
  border-radius: 10px;
  font-size: 13px;
  line-height: 1.7;
}

@media (max-width: 768px) {
  .modes { grid-template-columns: 1fr; }
}
</style>
