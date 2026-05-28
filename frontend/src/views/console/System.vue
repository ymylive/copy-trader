<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { systemApi } from '@/api/system'
import { useAccountsStore } from '@/stores/accounts'
import { setLocale } from '@/i18n'

const accStore = useAccountsStore()

const lang = ref<'zh-CN' | 'en'>('zh-CN')
const channels = reactive({
  wechat: { bound: false, code: '' },
  telegram: { bound: false, session_id: '' },
  email: { bound: false, email: '' },
  sms: { bound: false, phone: '' }
})

const versionInfo = reactive({ current: '——', latest: '——', preview_opt_in: false })
const updateAccount = ref<number | null>(null)
const updating = ref(false)

onMounted(async () => {
  await accStore.load()
  if (accStore.list.length) updateAccount.value = accStore.list[0].id
  const ch = (await systemApi.channels()) as any
  Object.assign(channels, ch)
  const v = (await systemApi.versions()) as any
  Object.assign(versionInfo, v)
})

function changeLang(v: 'zh-CN' | 'en') {
  lang.value = v
  setLocale(v)
  ElMessage.success('语言已切换')
}

async function bind(channel: string, body: Record<string, unknown>) {
  await systemApi.bindChannel(channel, body)
  ElMessage.success('绑定成功')
}

async function sendTest(channel: string) {
  await systemApi.sendTest(channel)
  ElMessage.success('测试消息已发送')
}

async function upgrade() {
  if (!updateAccount.value) return
  updating.value = true
  try {
    await systemApi.upgrade(updateAccount.value)
    ElMessage.success('已触发软件更新，请稍候...')
  } finally {
    updating.value = false
  }
}
</script>

<template>
  <div class="system-page">
    <section class="block ct-card">
      <h3 class="title">语言设置</h3>
      <div class="row">
        <div class="row-left">
          <div class="lbl">显示语言</div>
          <div class="muted">切换控制台显示语言，保存后立即生效。</div>
        </div>
        <el-select :model-value="lang" style="width:200px" @update:model-value="changeLang">
          <el-option label="简体中文" value="zh-CN" />
          <el-option label="English" value="en" />
        </el-select>
      </div>
    </section>

    <section class="block">
      <h3 class="title">通知渠道设置</h3>

      <div class="ch-card ct-card">
        <div class="ch-head">
          <div class="ch-icon wechat">微</div>
          <div>
            <div class="ch-name">微信服务号</div>
            <div class="muted">关注 Copy Trader 跟单系统公众号并输入授权码完成账户关联</div>
          </div>
        </div>
        <div class="ch-form">
          <span class="lbl">授权码</span>
          <el-input v-model="channels.wechat.code" placeholder="开发中..." style="width:280px" />
          <el-button type="primary" @click="bind('wechat', { code: channels.wechat.code })">生成授权码</el-button>
        </div>
      </div>

      <div class="ch-card ct-card">
        <div class="ch-head">
          <div class="ch-icon tg">TG</div>
          <div>
            <div class="ch-name">Telegram 机器人</div>
            <div class="muted">关注 @CopyTrader_bot 并发送 /start 以获得会话 ID</div>
          </div>
        </div>
        <div class="ch-form">
          <span class="lbl">会话 ID</span>
          <el-input v-model="channels.telegram.session_id" placeholder="输入 chat ID" style="width:280px" />
          <el-button type="primary" @click="bind('telegram', { session_id: channels.telegram.session_id })">确认绑定</el-button>
          <el-button @click="sendTest('telegram')">发送测试消息</el-button>
        </div>
      </div>

      <div class="ch-card ct-card">
        <div class="ch-head">
          <div class="ch-icon mail">@</div>
          <div>
            <div class="ch-name">QQ 邮箱</div>
            <div class="muted">收信率高，信息更全面。</div>
          </div>
        </div>
        <div class="ch-form">
          <span class="lbl">收信邮箱</span>
          <el-input v-model="channels.email.email" placeholder="example@qq.com" style="width:280px" />
          <el-button type="primary" @click="bind('email', { email: channels.email.email })">确认绑定</el-button>
          <el-button @click="sendTest('email')">发送测试邮件</el-button>
        </div>
      </div>

      <div class="ch-card ct-card">
        <div class="ch-head">
          <div class="ch-icon sms">SMS</div>
          <div>
            <div class="ch-name">手机短信</div>
            <div class="muted">通知更及时，但成本较高，使用将扣除相应积分。</div>
          </div>
        </div>
        <div class="ch-form">
          <span class="lbl">授权码</span>
          <el-input v-model="channels.sms.phone" placeholder="开发中..." style="width:280px" />
          <el-button type="primary" @click="bind('sms', { phone: channels.sms.phone })">确认绑定</el-button>
          <el-button @click="sendTest('sms')">发送测试手机号</el-button>
        </div>
      </div>
    </section>

    <section class="block ct-card">
      <h3 class="title">软件更新</h3>
      <div class="up-row">
        <div class="lbl">选择更新账户：</div>
        <el-select v-model="updateAccount" style="width:260px">
          <el-option v-for="a in accStore.list" :key="a.id" :label="`${a.name}【${a.exchange.toUpperCase()}】`" :value="a.id" />
        </el-select>
      </div>
      <div class="up-row">
        <span class="lbl">当前版本：</span>
        <span class="muted">({{ versionInfo.current === versionInfo.latest ? '软件已是最新版本!' : `可升级至 ${versionInfo.latest}` }})</span>
      </div>
      <el-button type="primary" :loading="updating" :disabled="versionInfo.current === versionInfo.latest" @click="upgrade">
        ↑ 更新软件
      </el-button>
      <div class="up-row">
        <el-checkbox v-model="versionInfo.preview_opt_in">是否订阅预览版更新</el-checkbox>
      </div>

      <div class="risk-block">
        <div class="risk-title">注意 (必读)：</div>
        <ul>
          <li>更新软件会自动尝试恢复持仓与跟单任务，但存在 ~1% 失败概率。</li>
          <li>每个账户拥有独立的跟单服务实例，更新仅作用于选择的账户。</li>
          <li>升级后建议立即检查持仓详情，确认无孤立订单。</li>
        </ul>
      </div>
    </section>
  </div>
</template>

<style scoped>
.system-page { display: flex; flex-direction: column; gap: 18px; }
.block { padding: 22px; }
.title { font-size: 16px; font-weight: 600; margin: 0 0 16px; color: var(--ct-text-1); }
.row { display: flex; justify-content: space-between; align-items: center; gap: 14px; padding: 12px 14px; background: var(--ct-bg-elev); border-radius: 10px; }
.row-left { flex: 1; }
.lbl { color: var(--ct-text-1); font-weight: 600; }
.muted { color: var(--ct-text-3); font-size: 12px; margin-top: 4px; }
.ch-card { padding: 16px 20px; margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
.ch-head { display: flex; gap: 12px; align-items: flex-start; flex: 1; min-width: 240px; }
.ch-icon {
  width: 40px; height: 40px;
  border-radius: 8px;
  color: #fff;
  font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.ch-icon.wechat { background: #07C160; }
.ch-icon.tg { background: #229ED9; }
.ch-icon.mail { background: #EAB308; }
.ch-icon.sms { background: #6366F1; font-size: 11px; }
.ch-name { color: var(--ct-text-1); font-weight: 600; }
.ch-form { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.up-row { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.risk-block { margin-top: 18px; background: rgba(239,68,68,0.06); border-radius: 10px; padding: 12px 16px; }
.risk-title { color: var(--ct-danger); font-weight: 600; margin-bottom: 6px; }
.risk-block ul { color: var(--ct-text-2); font-size: 12px; padding-left: 18px; line-height: 1.7; margin: 0; }
</style>
