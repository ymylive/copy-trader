<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { Trader } from '@/api/traders'
import { copyConfigsApi, type CopyConfig } from '@/api/copyConfigs'

interface Props {
  modelValue: boolean
  trader: Trader | null
  accountId?: number
  reverse?: boolean
}

const props = withDefaults(defineProps<Props>(), { reverse: false, accountId: undefined })
const emit = defineEmits<{
  (e: 'update:modelValue', v: boolean): void
  (e: 'submitted', cfg: CopyConfig): void
}>()

const open = computed({
  get: () => props.modelValue,
  set: (v: boolean) => emit('update:modelValue', v)
})

function defaultForm(): CopyConfig {
  return {
    account_id: props.accountId ?? 0,
    trader_id: props.trader?.id ?? '',
    reverse: !!props.reverse,
    capital_mode: 'fixed',
    fixed_amount: 200,
    multiplier: 1,
    start_mode: 'none',
    direction: 'both',
    open_trigger: 'market',
    open_price_better_pct: 0,
    add_trigger: 'market',
    add_price_better_pct: 0,
    tp_mode: 'off',
    tp_close_pct: 100,
    sl_mode: 'off',
    sl_close_pct: 100,
    loss_threshold_usdt: 500,
    safety_floor: 1,
    refill_on_tp: false,
    refill_allow_retp: false,
    blacklist: [],
    whitelist: [],
    notify_channels: ['none'],
    notify_types: ['order_success', 'order_fail', 'risk_trigger', 'tp_sl']
  }
}

const form = reactive<CopyConfig>(defaultForm())
const blacklistInput = ref('')
const whitelistInput = ref('')
const activeCollapse = ref(['capital', 'basic', 'risk', 'symbols', 'notify'])

watch(
  () => props.modelValue,
  (v) => {
    if (v) {
      Object.assign(form, defaultForm())
      blacklistInput.value = ''
      whitelistInput.value = ''
    }
  }
)

const submitting = ref(false)

async function submit() {
  if (form.capital_mode === 'fixed' && (!form.fixed_amount || form.fixed_amount <= 0)) {
    ElMessage.warning('请填写固定金额')
    return
  }
  form.blacklist = blacklistInput.value
    .split(/[,，\s]+/)
    .map((s) => s.trim().toUpperCase())
    .filter(Boolean)
  form.whitelist = whitelistInput.value
    .split(/[,，\s]+/)
    .map((s) => s.trim().toUpperCase())
    .filter(Boolean)

  submitting.value = true
  try {
    await copyConfigsApi.create(form)
    ElMessage.success('跟单已启动')
    emit('submitted', { ...form })
    open.value = false
  } finally {
    submitting.value = false
  }
}

const titleStyle = computed(() => (props.reverse ? 'reverse' : 'normal'))
</script>

<template>
  <el-dialog
    v-model="open"
    :title="''"
    width="780px"
    :close-on-click-modal="false"
    append-to-body
    class="copy-dialog"
  >
    <template #header>
      <div class="dialog-head">
        <div class="head-tags">
          <span class="tag standard">标准</span>
          <span class="trader-name">{{ trader?.nickname }}</span>
          <span class="trader-id mono">ID: {{ trader?.id }}</span>
          <span class="tag" :class="titleStyle">{{ reverse ? '反向跟单' : '正向跟单' }}</span>
          <span class="tag config">配置1</span>
        </div>
        <a class="risk-link">风控设置 ›</a>
      </div>
    </template>

    <el-collapse v-model="activeCollapse" class="cfg-collapse">
      <!-- 资金管理模式 -->
      <el-collapse-item title="① 资金管理模式" name="capital">
        <el-radio-group v-model="form.capital_mode" class="cap-group">
          <el-radio value="fixed">
            <div class="opt-line">
              <b>固定金额</b>
              <span class="desc">按固定 USDT 金额跟单</span>
            </div>
          </el-radio>
          <el-radio value="full">
            <div class="opt-line">
              <b>全仓跟单</b>
              <span class="desc">以账户全部可用资金为基数计算仓位</span>
            </div>
          </el-radio>
          <el-radio value="compound">
            <div class="opt-line">
              <b>复利滚动</b>
              <span class="desc">以当前账户总资产为基数，实时计算仓位</span>
            </div>
          </el-radio>
        </el-radio-group>

        <el-form-item v-if="form.capital_mode === 'fixed'" label="固定金额 (USDT)" class="mt-12">
          <el-input-number v-model="form.fixed_amount" :min="10" :max="1000000" :step="10" />
        </el-form-item>
      </el-collapse-item>

      <!-- 基础设置 -->
      <el-collapse-item title="② 基础设置" name="basic">
        <el-form label-width="160px" label-position="right">
          <el-form-item label="跟单倍率">
            <el-input-number v-model="form.multiplier" :min="0.01" :max="100" :step="0.1" :precision="2" />
            <span class="help-text">与交易员仓位百分比的乘数（1 = 与交易员相同百分比）</span>
          </el-form-item>

          <el-form-item label="启动跟单设置">
            <el-radio-group v-model="form.start_mode">
              <el-radio value="none">不复制</el-radio>
              <el-radio value="only_loss">仅复制浮亏持仓</el-radio>
              <el-radio value="all">复制所有持仓</el-radio>
            </el-radio-group>
          </el-form-item>

          <el-form-item label="持仓方向限制">
            <el-radio-group v-model="form.direction">
              <el-radio value="both">无限制</el-radio>
              <el-radio value="long">只开多单</el-radio>
              <el-radio value="short">只开空单</el-radio>
            </el-radio-group>
          </el-form-item>

          <el-form-item label="开仓触发条件">
            <el-radio-group v-model="form.open_trigger">
              <el-radio value="market">市价</el-radio>
              <el-radio value="avg_price">持仓均价限价</el-radio>
              <el-radio value="add_price">加仓价限价</el-radio>
            </el-radio-group>
            <div class="sub-row" v-if="form.open_trigger !== 'market'">
              <span class="lbl">价格优于交易员：</span>
              <el-input-number v-model="form.open_price_better_pct" :min="0" :max="50" :step="0.1" :precision="2" />
              <span class="lbl">%</span>
            </div>
          </el-form-item>

          <el-form-item label="加仓触发条件">
            <el-radio-group v-model="form.add_trigger">
              <el-radio value="market">市价</el-radio>
              <el-radio value="avg_price">持仓均价限价</el-radio>
              <el-radio value="add_price">加仓价限价</el-radio>
            </el-radio-group>
            <div class="sub-row" v-if="form.add_trigger !== 'market'">
              <span class="lbl">价格优于交易员：</span>
              <el-input-number v-model="form.add_price_better_pct" :min="0" :max="50" :step="0.1" :precision="2" />
              <span class="lbl">%</span>
            </div>
          </el-form-item>
        </el-form>
      </el-collapse-item>

      <!-- 止盈止损 -->
      <el-collapse-item title="③ 止盈止损 / 风控" name="risk">
        <el-form label-width="160px" label-position="right">
          <el-form-item label="持仓止盈">
            <el-radio-group v-model="form.tp_mode">
              <el-radio value="off">不启用</el-radio>
              <el-radio value="cycle">循环触发</el-radio>
            </el-radio-group>
            <div class="sub-row" v-if="form.tp_mode === 'cycle'">
              <span class="lbl">平仓数量：</span>
              <el-input-number v-model="form.tp_close_pct" :min="1" :max="100" :step="5" />
              <span class="lbl">%</span>
            </div>
          </el-form-item>

          <el-form-item label="持仓止损">
            <el-radio-group v-model="form.sl_mode">
              <el-radio value="off">不启用</el-radio>
              <el-radio value="cycle">循环触发</el-radio>
            </el-radio-group>
            <div class="sub-row" v-if="form.sl_mode === 'cycle'">
              <span class="lbl">平仓数量：</span>
              <el-input-number v-model="form.sl_close_pct" :min="1" :max="100" :step="5" />
              <span class="lbl">%</span>
            </div>
          </el-form-item>

          <el-form-item label="跟单亏损阈值">
            <el-input-number v-model="form.loss_threshold_usdt" :min="10" :step="50" />
            <span class="lbl">USDT</span>
            <span class="help-text">达到阈值时暂停此交易员的跟单并全平来自此交易员的持仓</span>
          </el-form-item>

          <el-form-item label="安全垫亏损值">
            <el-input-number v-model="form.safety_floor" :min="0.1" :max="10" :step="0.1" :precision="2" />
            <span class="lbl">×</span>
            <span class="help-text">净值跌破预设值时自动触发倍率降低，防止进一步亏损</span>
          </el-form-item>

          <el-form-item label="止盈回填策略">
            <el-checkbox v-model="form.refill_on_tp">触发止盈后市场价格回到开仓均价时重新补满仓位</el-checkbox>
            <el-checkbox v-model="form.refill_allow_retp">补满仓位后允许再次止盈</el-checkbox>
          </el-form-item>
        </el-form>
      </el-collapse-item>

      <!-- 币种过滤 -->
      <el-collapse-item title="④ 币种过滤" name="symbols">
        <el-form label-width="160px" label-position="right">
          <el-form-item label="币种黑名单">
            <el-input
              v-model="blacklistInput"
              type="textarea"
              :rows="2"
              placeholder="不跟单的币种，逗号分隔（如：DOGE, SHIB, PEPE）"
            />
          </el-form-item>
          <el-form-item label="只跟单的币种">
            <el-input
              v-model="whitelistInput"
              type="textarea"
              :rows="2"
              placeholder="白名单，留空表示不限制（如：BTC, ETH, SOL）"
            />
          </el-form-item>
        </el-form>
      </el-collapse-item>

      <!-- 通知设置 -->
      <el-collapse-item title="⑤ 通知设置" name="notify">
        <el-form label-width="160px" label-position="right">
          <el-form-item label="通知方式">
            <el-radio-group v-model="form.notify_channels[0]">
              <el-radio value="none">不通知</el-radio>
              <el-radio value="email">邮件</el-radio>
              <el-radio value="telegram">TG 机器人</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="通知类型">
            <el-checkbox-group v-model="form.notify_types">
              <el-checkbox value="order_success">下单成功</el-checkbox>
              <el-checkbox value="order_fail">下单失败</el-checkbox>
              <el-checkbox value="risk_trigger">触发风控</el-checkbox>
              <el-checkbox value="tp_sl">止盈止损</el-checkbox>
              <el-checkbox value="margin_change">交易员保证金变动 (仅币安)</el-checkbox>
            </el-checkbox-group>
          </el-form-item>
        </el-form>
      </el-collapse-item>
    </el-collapse>

    <div class="footer-tip">风控设置针对来自此交易员跟单任务下的所有配置生效</div>

    <template #footer>
      <el-button @click="open = false">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="submit">
        {{ reverse ? '启动反向跟单' : '启动跟单' }}
      </el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
:deep(.copy-dialog .el-dialog__header) { padding: 16px 22px; border-bottom: 1px solid var(--ct-border); }
:deep(.copy-dialog .el-dialog__body) { padding: 18px 22px; max-height: 70vh; overflow-y: auto; }
.dialog-head { display: flex; justify-content: space-between; align-items: center; }
.head-tags { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}
.tag.standard { background: rgba(16,185,129,0.12); color: var(--ct-primary); }
.tag.normal { background: rgba(16,185,129,0.12); color: var(--ct-primary); }
.tag.reverse { background: rgba(56,189,248,0.12); color: var(--ct-accent); }
.tag.config { background: rgba(156,163,175,0.12); color: var(--ct-text-2); }
.trader-name { font-size: 16px; font-weight: 600; color: var(--ct-text-1); }
.trader-id { color: var(--ct-text-3); font-size: 12px; }
.risk-link { color: var(--ct-primary); font-size: 13px; cursor: pointer; }
.cfg-collapse { border: none; }
:deep(.cfg-collapse .el-collapse-item__header) {
  font-weight: 600;
  font-size: 14px;
  background: var(--ct-bg-elev);
  padding: 0 14px;
  border-radius: 8px;
  margin-top: 8px;
}
:deep(.cfg-collapse .el-collapse-item__wrap) { background: transparent; }
:deep(.cfg-collapse .el-collapse-item__content) { padding: 16px 8px 6px; }
.cap-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.cap-group :deep(.el-radio) { margin-right: 0; height: auto; padding: 6px 0; align-items: flex-start; }
.opt-line { display: flex; flex-direction: column; gap: 2px; }
.opt-line b { color: var(--ct-text-1); }
.desc { color: var(--ct-text-3); font-size: 12px; }
.mt-12 { margin-top: 12px; }
.sub-row { display: inline-flex; align-items: center; gap: 8px; margin-left: 14px; }
.lbl { color: var(--ct-text-2); font-size: 13px; }
.help-text { margin-left: 10px; color: var(--ct-text-3); font-size: 12px; }
.footer-tip {
  margin-top: 14px;
  padding: 10px 12px;
  background: rgba(245, 158, 11, 0.08);
  border-radius: 8px;
  color: #B45309;
  font-size: 12px;
}
</style>
