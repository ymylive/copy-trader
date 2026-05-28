<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { shopApi } from '@/api/shop'

const products = ref<any[]>([])
const trialForm = reactive({ exchange: '', uid: '' })
const orderForm = reactive({
  period: '1m',
  exchange: '',
  uid: '',
  coupon: '',
  product_id: 'slot_order'
})

onMounted(async () => {
  products.value = (await shopApi.products()) as any[]
})

const periodLabel: Record<string, string> = {
  '1m': '一个月',
  '3m': '三个月',
  '6m': '半年',
  '1y': '一年',
  perm: '永久',
  contact: '联系管理员'
}

const exchanges = ['Binance', 'OKX', 'Gate.io', 'Bitget']

async function claimTrial() {
  if (!trialForm.exchange || !trialForm.uid) {
    ElMessage.warning('请选择交易所并填写 UID')
    return
  }
  await shopApi.claimTrial(0, trialForm.exchange, trialForm.uid)
  ElMessage.success('试用领取成功')
}

async function buy(productId: string) {
  await shopApi.order({
    product_id: productId,
    period: orderForm.period,
    coupon: orderForm.coupon
  })
  ElMessage.success('下单成功（mock）')
}

function pricingOf(p: any): string {
  if (p.id === 'slot_fast') return '$999999'
  return `$${p.price}`
}
</script>

<template>
  <div class="shop-page">
    <section class="hero-row">
      <div class="trial-card">
        <h2>活动期间可领取</h2>
        <h1>7 天免费试用！</h1>
        <p class="muted">为避免恶意领用，每一账户仅可领取一次试用。</p>

        <div class="trial-form">
          <div class="form-line">
            <label>交易所：</label>
            <el-select v-model="trialForm.exchange" placeholder="请选择" style="flex:1">
              <el-option v-for="e in exchanges" :key="e" :label="e" :value="e" />
            </el-select>
          </div>
          <div class="form-line">
            <label>UID：</label>
            <el-input v-model="trialForm.uid" placeholder="请输入" />
          </div>
          <el-button type="success" class="cta" @click="claimTrial">即刻领取</el-button>
        </div>
      </div>

      <div class="primary-card">
        <div class="card-head">
          <div class="card-title">商品名称</div>
          <div class="card-value">下单名额</div>
        </div>

        <div class="period-row">
          <div class="period-label">购买时长：</div>
          <el-radio-group v-model="orderForm.period" size="small">
            <el-radio-button label="1m">一个月</el-radio-button>
            <el-radio-button label="3m">三个月</el-radio-button>
            <el-radio-button label="6m">半年</el-radio-button>
            <el-radio-button label="1y">一年</el-radio-button>
          </el-radio-group>
        </div>

        <p class="hint">使用前请填写注册交易所并填入相应 UID 即可享受半价优惠（如使用）</p>

        <div class="form-grid">
          <div class="form-line">
            <label>交易所：</label>
            <el-select v-model="orderForm.exchange" placeholder="请选择" style="flex:1">
              <el-option v-for="e in exchanges" :key="e" :label="e" :value="e" />
            </el-select>
          </div>
          <div class="form-line">
            <label>UID：</label>
            <el-input v-model="orderForm.uid" placeholder="请输入" />
            <el-button text type="primary">验证受邀关系</el-button>
          </div>
        </div>

        <el-divider />

        <div class="card-head">
          <div class="card-title">商品名称</div>
          <div class="card-value">为账户增加下单名额</div>
        </div>
        <div class="form-line">
          <label>优惠券：</label>
          <el-select v-model="orderForm.coupon" placeholder="请选择" style="flex:1">
            <el-option label="不使用" value="" />
            <el-option label="85 折优惠券" value="DISC85" />
          </el-select>
        </div>

        <div class="total-row">
          <div class="total-left">
            <div class="tip">温馨提示：</div>
            <div class="muted-sm">1、此商品是重复购买为账户增加相对应的下单名额持续续费，若取消自动续费可在钱包后台操作。</div>
            <div class="muted-sm">2、享受半价优惠的下单名额仅支持绑定您受邀账户创建的 API-Key。</div>
          </div>
          <div class="total-right">
            <div class="total-line"><span>总金额：</span><b class="amount">$80.00</b></div>
            <el-button type="success" size="large" @click="buy('slot_order')">立即购买</el-button>
          </div>
        </div>
      </div>
    </section>

    <section class="addons">
      <h2 class="section-title">增值服务</h2>
      <div class="addons-grid">
        <div v-for="p in products.filter((x) => x.id !== 'slot_order')" :key="p.id" class="addon-card">
          <div class="row"><span class="lbl">商品名称：</span><span class="val">{{ p.name }}</span></div>
          <div class="row"><span class="lbl">商品说明：</span><span class="val">{{ p.desc }}</span></div>
          <div class="row"><span class="lbl">商品金额：</span><span class="val price">{{ pricingOf(p) }}</span></div>
          <div class="row" v-if="p.id === 'slot_copy'"><span class="lbl">购买数量：</span><el-input-number :min="1" :value="1" size="small" /></div>
          <div class="row" v-if="p.periods?.length > 1">
            <span class="lbl">购买时长：</span>
            <el-radio-group v-model="orderForm.period" size="small">
              <el-radio-button v-for="period in p.periods" :key="period" :label="period">{{ periodLabel[period] }}</el-radio-button>
            </el-radio-group>
          </div>
          <div class="row" v-if="p.periods?.length === 1"><span class="lbl">购买时长：</span><span class="val">{{ periodLabel[p.periods[0]] }}</span></div>
          <el-button v-if="p.id === 'slot_fast'" type="info" class="buy" size="large" disabled>请联系系统管理员开通</el-button>
          <el-button v-else type="success" class="buy" size="large" @click="buy(p.id)">立即购买</el-button>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.shop-page {
  max-width: 1180px;
  margin: 0 auto;
  padding: 40px 32px 80px;
  color: #e5e7eb;
}
.hero-row {
  display: grid;
  grid-template-columns: 1fr 1.6fr;
  gap: 22px;
}
.trial-card,
.primary-card {
  background: rgba(14, 20, 27, 0.75);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 18px;
  padding: 28px;
}
.trial-card h2 { color: #fff; margin: 0 0 6px; font-size: 22px; }
.trial-card h1 { color: #fff; margin: 0 0 8px; font-size: 30px; }
.muted { color: #9CA3AF; font-size: 12px; }
.trial-form { margin-top: 26px; display: flex; flex-direction: column; gap: 14px; }
.form-line { display: flex; align-items: center; gap: 10px; }
.form-line label { color: #9CA3AF; font-size: 13px; width: 70px; text-align: right; }
.cta { width: 100%; }
.primary-card .card-head { display: flex; gap: 16px; margin-bottom: 18px; }
.card-title { color: #9CA3AF; font-size: 13px; min-width: 80px; }
.card-value { color: #fff; font-weight: 600; }
.period-row { display: flex; align-items: center; gap: 14px; margin-bottom: 12px; }
.period-label { color: #9CA3AF; font-size: 13px; }
.hint { color: #6B7280; font-size: 12px; padding: 12px; background: rgba(255, 255, 255, 0.03); border-radius: 8px; margin: 12px 0; }
.form-grid { display: flex; flex-direction: column; gap: 12px; }
.total-row { display: grid; grid-template-columns: 1fr auto; gap: 24px; align-items: end; margin-top: 16px; }
.tip { color: var(--ct-warn); font-size: 13px; margin-bottom: 4px; }
.muted-sm { color: #6B7280; font-size: 12px; line-height: 1.6; }
.total-line { font-size: 14px; margin-bottom: 12px; }
.amount { color: var(--ct-primary); font-size: 22px; }
.section-title { font-size: 24px; color: #fff; margin: 48px 0 22px; }
.addons-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
}
.addon-card {
  background: rgba(14, 20, 27, 0.75);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 18px;
  padding: 24px;
  display: flex; flex-direction: column; gap: 14px;
}
.row { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; font-size: 13px; }
.lbl { color: #9CA3AF; min-width: 80px; }
.val { color: #e5e7eb; }
.price { color: var(--ct-primary); font-weight: 600; }
.buy { margin-top: auto; }
:deep(.el-divider) { border-color: rgba(255, 255, 255, 0.08); }

@media (max-width: 900px) {
  .hero-row { grid-template-columns: 1fr; }
}
</style>
