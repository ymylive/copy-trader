<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { mockLoginHistory } from '@/mock/data'

const ipHistory = ref(mockLoginHistory())
const pwdOpen = ref(false)
const phoneOpen = ref(false)
const emailOpen = ref(false)

const pwdForm = ref({ old: '', n1: '', n2: '' })
const phoneForm = ref({ phone: '', code: '' })
const emailForm = ref({ email: '', code: '' })

function changePwd() {
  if (!pwdForm.value.n1 || pwdForm.value.n1 !== pwdForm.value.n2) {
    ElMessage.warning('两次密码不一致')
    return
  }
  pwdOpen.value = false
  ElMessage.success('密码已修改（mock）')
}

function bindPhone() {
  if (!phoneForm.value.phone) return
  phoneOpen.value = false
  ElMessage.success('手机已绑定（mock）')
}

function bindEmail() {
  if (!emailForm.value.email) return
  emailOpen.value = false
  ElMessage.success('邮箱已绑定（mock）')
}
</script>

<template>
  <div class="security-page">
    <h2 class="section-title">安全中心</h2>

    <div class="cards-row">
      <div class="sec-card">
        <div class="row">
          <div>
            <div class="title">修改密码</div>
            <div class="muted">定期更换为复杂度较高的密码以保护您的账号</div>
          </div>
          <el-button type="success" @click="pwdOpen = true">立即修改</el-button>
        </div>
      </div>
      <div class="sec-card">
        <div class="row">
          <div>
            <div class="title">修改绑定手机号</div>
            <div class="muted">绑定日常使用的手机号以确保随时接收账户动态</div>
          </div>
          <el-button type="success" @click="phoneOpen = true">立即修改</el-button>
        </div>
      </div>
      <div class="sec-card">
        <div class="row">
          <div>
            <div class="title">修改绑定邮箱</div>
            <div class="muted">绑定日常使用的邮箱账号以确保随时接收账户动态</div>
          </div>
          <el-button type="success" @click="emailOpen = true">立即修改</el-button>
        </div>
      </div>
    </div>

    <h2 class="section-title" style="margin-top:32px">最近十次登录 IP</h2>
    <el-table :data="ipHistory" empty-text="暂无登录记录">
      <el-table-column label="IP" prop="ip" />
      <el-table-column label="地点" prop="region" />
      <el-table-column label="登录时间" prop="time" />
    </el-table>

    <el-dialog v-model="pwdOpen" title="修改密码" width="420px">
      <el-form label-width="90px">
        <el-form-item label="旧密码"><el-input v-model="pwdForm.old" type="password" show-password /></el-form-item>
        <el-form-item label="新密码"><el-input v-model="pwdForm.n1" type="password" show-password /></el-form-item>
        <el-form-item label="再次输入"><el-input v-model="pwdForm.n2" type="password" show-password /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pwdOpen = false">取消</el-button>
        <el-button type="primary" @click="changePwd">确认</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="phoneOpen" title="绑定手机号" width="420px">
      <el-form label-width="90px">
        <el-form-item label="手机号"><el-input v-model="phoneForm.phone" /></el-form-item>
        <el-form-item label="验证码"><el-input v-model="phoneForm.code" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="phoneOpen = false">取消</el-button>
        <el-button type="primary" @click="bindPhone">绑定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="emailOpen" title="绑定邮箱" width="420px">
      <el-form label-width="90px">
        <el-form-item label="邮箱"><el-input v-model="emailForm.email" /></el-form-item>
        <el-form-item label="验证码"><el-input v-model="emailForm.code" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="emailOpen = false">取消</el-button>
        <el-button type="primary" @click="bindEmail">绑定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.security-page {
  max-width: 1180px;
  margin: 0 auto;
  padding: 40px 32px 80px;
  color: #e5e7eb;
}
.section-title { font-size: 22px; color: #fff; margin: 0 0 16px; }
.cards-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 18px;
}
.sec-card {
  background: rgba(14, 20, 27, 0.78);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 16px;
  padding: 20px;
}
.row { display: flex; justify-content: space-between; align-items: center; gap: 14px; }
.title { font-size: 15px; color: #fff; font-weight: 600; margin-bottom: 6px; }
.muted { color: #9CA3AF; font-size: 12px; line-height: 1.6; max-width: 220px; }
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
