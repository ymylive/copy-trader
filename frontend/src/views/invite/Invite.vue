<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { inviteApi } from '@/api/invite'

const summary = ref<any>({ uid: 0, level: 0, rebate_pct: 10, total_rebate: 0, invite_link: '' })
const records = ref<any[]>([])

onMounted(async () => {
  summary.value = await inviteApi.summary()
  records.value = (await inviteApi.records()) as any[]
})

async function copyLink() {
  await navigator.clipboard.writeText(summary.value.invite_link)
  ElMessage.success('邀请链接已复制')
}

async function withdraw() {
  await inviteApi.withdraw()
  ElMessage.success('提现申请已提交')
}
</script>

<template>
  <div class="invite-page">
    <div class="card">
      <div class="head">
        <div>
          <div class="title">我的邀请</div>
          <div class="hi">
            Hi，<span class="name">cornna</span>
            <span class="level-tag">level {{ summary.level }} (返佣比例 {{ summary.rebate_pct }}%)</span>
            <a class="link">返佣等级说明</a>
          </div>
        </div>
        <div class="right">
          <div class="rebate">
            <div class="lbl">累计获得返佣金额</div>
            <div class="num mono">${{ summary.total_rebate.toFixed(2) }}</div>
          </div>
          <el-button type="primary" round @click="withdraw">提现</el-button>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="sub-title">当您邀请朋友注册时</div>
      <div class="invite-row">
        <div class="info-block">
          <div class="row-line">
            <span>邀请链接地址：</span>
            <span class="link mono">{{ summary.invite_link }}</span>
          </div>
          <div class="row-line muted">
            每当 TA 购买主套餐中的任意套餐时，您都会获得实付款的 <b>{{ summary.rebate_pct }}%</b> 返利。
          </div>
          <div class="row-line muted">
            此外，当您每邀请个不同的用户购买主套餐时，您还将额外获得 1 张 <b>85 折</b>优惠券。
          </div>
        </div>
        <el-button type="primary" round @click="copyLink">复制邀请链接</el-button>
      </div>
    </div>

    <div class="section-title">邀请 / 返利记录</div>
    <el-table :data="records" empty-text="暂无邀请记录" style="width:100%">
      <el-table-column label="序号" type="index" width="80" />
      <el-table-column label="受邀人 ID" prop="invitee_uid" />
      <el-table-column label="注册时间" prop="created_at" />
      <el-table-column label="获得返利">
        <template #default="{ row }">
          <span class="num mono">${{ row.reward?.toFixed(2) }}</span>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<style scoped>
.invite-page {
  max-width: 1180px;
  margin: 0 auto;
  padding: 40px 32px 80px;
  color: #e5e7eb;
}
.card {
  background: rgba(14, 20, 27, 0.75);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 18px;
  padding: 24px 28px;
  margin-bottom: 22px;
}
.head { display: flex; justify-content: space-between; align-items: center; gap: 16px; flex-wrap: wrap; }
.title { font-size: 18px; font-weight: 600; margin-bottom: 8px; }
.hi { font-size: 14px; color: #d1d5db; }
.name { color: #fff; font-weight: 600; }
.level-tag {
  display: inline-block;
  background: rgba(163, 230, 53, 0.15);
  color: var(--ct-space-accent);
  border-radius: 4px;
  padding: 2px 8px;
  margin-left: 8px;
  font-size: 12px;
}
.link { color: var(--ct-primary); cursor: pointer; margin-left: 8px; }
.right { display: flex; align-items: center; gap: 18px; }
.rebate .lbl { color: #9CA3AF; font-size: 12px; }
.rebate .num { font-size: 24px; font-weight: 700; color: #fff; }
.sub-title { font-size: 15px; margin-bottom: 14px; color: #fff; font-weight: 600; }
.invite-row { display: flex; justify-content: space-between; align-items: center; gap: 16px; flex-wrap: wrap; }
.info-block { flex: 1; min-width: 280px; }
.row-line { padding: 4px 0; }
.muted { color: #9CA3AF; font-size: 13px; }
.section-title { font-size: 17px; font-weight: 600; margin: 22px 0 12px; color: #fff; }
:deep(.el-table) {
  --el-table-bg-color: rgba(14, 20, 27, 0.55);
  --el-table-tr-bg-color: rgba(14, 20, 27, 0.55);
  --el-table-header-bg-color: rgba(14, 20, 27, 0.85);
  --el-table-text-color: #d1d5db;
  --el-table-header-text-color: #9CA3AF;
  --el-table-border-color: rgba(255, 255, 255, 0.05);
  border-radius: 14px;
  overflow: hidden;
}
</style>
