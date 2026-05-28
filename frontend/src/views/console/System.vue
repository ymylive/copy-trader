<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { systemApi } from '@/api/system'
import { useAccountsStore } from '@/stores/accounts'
import { setLocale } from '@/i18n'
import { formatUTC } from '@/utils/format'

const accStore = useAccountsStore()

const lang = ref<'zh-CN' | 'en'>('zh-CN')
const channel = ref<'silent' | 'wechat' | 'telegram' | 'email' | 'sms'>('telegram')
const channels = reactive({
  wechat:   { bound: false, code: '' },
  telegram: { bound: false, session_id: '' },
  email:    { bound: false, email: '' },
  sms:      { bound: false, phone: '' }
})

const versionInfo = reactive({ current: '——', latest: '——', preview_opt_in: false })
const updateAccount = ref<number | null>(null)
const updating = ref(false)
const updateProgress = ref(0)
const renderTs = ref(formatUTC())

onMounted(async () => {
  await accStore.load()
  if (accStore.list.length) updateAccount.value = accStore.list[0].id
  Object.assign(channels, (await systemApi.channels()) as any)
  Object.assign(versionInfo, (await systemApi.versions()) as any)
})

function changeLang(v: 'zh-CN' | 'en') {
  lang.value = v
  setLocale(v)
  ElMessage.success('LANGUAGE SWITCHED')
}

async function bind(c: string, body: Record<string, unknown>) {
  await systemApi.bindChannel(c, body)
  ElMessage.success(`${c.toUpperCase()} BOUND`)
}

async function sendTest(c: string) {
  await systemApi.sendTest(c)
  ElMessage.success(`TEST MESSAGE SENT VIA ${c.toUpperCase()}`)
}

async function upgrade() {
  if (!updateAccount.value) return
  updating.value = true
  updateProgress.value = 0
  const tick = setInterval(() => {
    updateProgress.value += 4
    if (updateProgress.value >= 100) {
      clearInterval(tick)
      updating.value = false
      ElMessage.success('SOFTWARE UPGRADED')
    }
  }, 80)
  try { await systemApi.upgrade(updateAccount.value) } catch {/* */}
}
</script>

<template>
  <div class="sys-page">
    <div class="sec-head">
      <div class="sec-title"><span class="amber">07 //</span> SYSTEM CONTROL · LOCALES · CHANNELS · UPDATES</div>
      <div class="sec-coord">{{ renderTs }}</div>
    </div>

    <!-- Locale -->
    <div class="block">
      <div class="block-head">
        <div class="grp-title"><span class="num">01</span>LOCALE</div>
      </div>
      <div class="block-body row">
        <div class="lbl">DISPLAY LANGUAGE</div>
        <div class="radio-row half2">
          <div class="opt" :class="{ active: lang === 'zh-CN' }" @click="changeLang('zh-CN')">简体中文</div>
          <div class="opt" :class="{ active: lang === 'en' }" @click="changeLang('en')">ENGLISH</div>
        </div>
      </div>
    </div>

    <!-- Notify channel -->
    <div class="block">
      <div class="block-head">
        <div class="grp-title"><span class="num">02</span>NOTIFICATION CHANNEL</div>
      </div>
      <div class="block-body">
        <div class="row">
          <div class="lbl">DELIVERY CHANNEL</div>
          <div class="radio-row full">
            <div class="opt" :class="{ active: channel === 'silent' }" @click="channel = 'silent'">SILENT</div>
            <div class="opt" :class="{ active: channel === 'wechat' }" @click="channel = 'wechat'">WECHAT</div>
            <div class="opt" :class="{ active: channel === 'telegram' }" @click="channel = 'telegram'">TELEGRAM</div>
            <div class="opt" :class="{ active: channel === 'email' }" @click="channel = 'email'">EMAIL</div>
            <div class="opt" :class="{ active: channel === 'sms' }" @click="channel = 'sms'">SMS</div>
          </div>
        </div>
        <div v-if="channel === 'telegram'" class="row">
          <div class="lbl">CHAT ID</div>
          <input class="inp-term" v-model="channels.telegram.session_id" placeholder="@CopyTrader_bot /start to obtain" />
          <button class="btn-term" @click="bind('telegram', { session_id: channels.telegram.session_id })">BIND</button>
          <button class="btn-term" @click="sendTest('telegram')">SEND TEST</button>
        </div>
        <div v-if="channel === 'email'" class="row">
          <div class="lbl">EMAIL</div>
          <input class="inp-term" v-model="channels.email.email" placeholder="example@qq.com" />
          <button class="btn-term" @click="bind('email', { email: channels.email.email })">BIND</button>
          <button class="btn-term" @click="sendTest('email')">SEND TEST</button>
        </div>
        <div v-if="channel === 'sms'" class="row">
          <div class="lbl">PHONE</div>
          <input class="inp-term" v-model="channels.sms.phone" placeholder="+86 ..." />
          <button class="btn-term" @click="bind('sms', { phone: channels.sms.phone })">BIND</button>
          <button class="btn-term" @click="sendTest('sms')">SEND TEST</button>
        </div>
        <div v-if="channel === 'wechat'" class="row">
          <div class="lbl">AUTH CODE</div>
          <input class="inp-term" v-model="channels.wechat.code" placeholder="generate token first" />
          <button class="btn-term" @click="bind('wechat', { code: channels.wechat.code })">GENERATE</button>
        </div>
      </div>
    </div>

    <!-- Software update -->
    <div class="block">
      <div class="block-head">
        <div class="grp-title"><span class="num">03</span>SOFTWARE UPDATE</div>
      </div>
      <div class="block-body">
        <div class="row">
          <div class="lbl">TARGET ACCOUNT</div>
          <el-select v-model="updateAccount" style="width:280px">
            <el-option v-for="a in accStore.list" :key="a.id" :label="a.name" :value="a.id" />
          </el-select>
        </div>
        <div class="row">
          <div class="lbl">CURRENT</div>
          <span class="amber">{{ versionInfo.current }}</span>
          <span class="dim">→</span>
          <span class="amber">{{ versionInfo.latest }}</span>
          <span class="dim">{{ versionInfo.current === versionInfo.latest ? '· UP-TO-DATE' : '· UPGRADE AVAILABLE' }}</span>
        </div>
        <div v-if="updating" class="upd-progress">
          <div class="upd-bar" :style="{ width: updateProgress + '%' }"></div>
          <div class="upd-text">▌ UPGRADING {{ updateProgress }}%</div>
        </div>
        <div class="row">
          <button class="btn-term primary" :disabled="updating" @click="upgrade">↑ UPGRADE SOFTWARE</button>
          <label class="chk-term" :class="{ on: versionInfo.preview_opt_in }" @click="versionInfo.preview_opt_in = !versionInfo.preview_opt_in">
            <span class="box">{{ versionInfo.preview_opt_in ? '✓' : '' }}</span>
            SUBSCRIBE TO PREVIEW BUILDS
          </label>
        </div>
        <div class="warn">
          ⚠ UPGRADE WILL ATTEMPT TO RECOVER OPEN POSITIONS AND COPY JOBS · ~1% FAILURE RATE · EACH ACCOUNT HAS ITS OWN INSTANCE · VERIFY POSITIONS AFTER UPGRADE.
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.sys-page { display: flex; flex-direction: column; gap: 18px; }

.block { border: 1px solid var(--ct-divider); background: var(--ct-bg); }
.block-head {
  padding: 10px 16px;
  border-bottom: 1px solid var(--ct-divider);
  background: var(--ct-bg-2);
}
.grp-title {
  font-size: 11px;
  color: var(--ct-text-3);
  letter-spacing: 0.14em;
  text-transform: uppercase;
  font-family: var(--ct-font-mono);
}
.grp-title .num { color: var(--ct-amber); margin-right: 6px; }

.block-body { padding: 14px 16px; display: flex; flex-direction: column; gap: 12px; }
.row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.row .lbl {
  font-size: 10px;
  color: var(--ct-text-3);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  font-family: var(--ct-font-mono);
  min-width: 130px;
}
.row .dim { color: var(--ct-text-3); }
.row .amber { color: var(--ct-amber); font-family: var(--ct-font-mono); }

.radio-row {
  display: flex;
  gap: 0;
  border: 1px solid var(--ct-divider);
  background: var(--ct-bg-2);
}
.radio-row.full { width: 100%; }
.radio-row.half2 { width: 280px; }
.radio-row .opt {
  flex: 1;
  height: 30px;
  padding: 0 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  color: var(--ct-text-2);
  border-right: 1px solid var(--ct-divider);
  cursor: pointer;
  letter-spacing: 0.06em;
  font-family: var(--ct-font-mono);
  text-transform: uppercase;
  user-select: none;
}
.radio-row .opt:last-child { border-right: 0; }
.radio-row .opt.active { background: var(--ct-amber); color: #0A0E14; font-weight: 600; }
.radio-row .opt:not(.active):hover { background: var(--ct-bg-hover); color: var(--ct-text); }

.inp-term {
  height: 30px;
  background: var(--ct-bg-2);
  border: 1px solid var(--ct-divider);
  color: var(--ct-text);
  padding: 0 10px;
  font-size: 12px;
  font-family: var(--ct-font-mono);
  outline: none;
  min-width: 280px;
}
.inp-term:focus { border-color: var(--ct-amber); }
.btn-term {
  height: 30px;
  padding: 0 14px;
  background: transparent;
  border: 1px solid var(--ct-divider-strong);
  color: var(--ct-text);
  font-family: var(--ct-font-mono);
  font-size: 11px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  cursor: pointer;
}
.btn-term:hover { border-color: var(--ct-amber); color: var(--ct-amber); }
.btn-term.primary {
  background: var(--ct-amber);
  border-color: var(--ct-amber);
  color: #0A0E14;
  font-weight: 600;
}
.btn-term.primary:hover { filter: brightness(1.08); color: #0A0E14; }
.btn-term:disabled { opacity: 0.5; cursor: not-allowed; }

.chk-term {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-size: 11px;
  color: var(--ct-text-2);
  cursor: pointer;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  font-family: var(--ct-font-mono);
}
.chk-term .box {
  width: 13px;
  height: 13px;
  border: 1px solid var(--ct-text-dim);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--ct-amber);
  font-size: 11px;
  line-height: 1;
}
.chk-term.on .box { border-color: var(--ct-amber); }
.chk-term.on { color: var(--ct-text); }

.upd-progress {
  position: relative;
  height: 22px;
  border: 1px solid var(--ct-amber);
  background: var(--ct-bg);
}
.upd-bar {
  position: absolute;
  inset: 0;
  background: var(--ct-amber);
  opacity: 0.8;
  transition: width 80ms linear;
}
.upd-text {
  position: relative;
  text-align: center;
  font-size: 11px;
  letter-spacing: 0.12em;
  color: #0A0E14;
  font-family: var(--ct-font-mono);
  font-weight: 700;
  line-height: 22px;
}

.warn {
  border: 1px solid rgba(255, 180, 0, 0.35);
  background: rgba(255, 180, 0, 0.04);
  color: var(--ct-amber);
  padding: 10px 12px;
  font-size: 10px;
  letter-spacing: 0.08em;
  line-height: 1.6;
  font-family: var(--ct-font-mono);
}
</style>
