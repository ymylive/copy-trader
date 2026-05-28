<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authApi } from '@/api/auth'

const router = useRouter()
const email = ref('')
const loading = ref(false)

async function submit() {
  if (!email.value) {
    ElMessage.warning('请填写邮箱')
    return
  }
  loading.value = true
  try {
    await authApi.forgot(email.value)
    ElMessage.success('密码重置邮件已发送（mock）')
    router.push('/login')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page ct-space ct-space-stars">
    <div class="brand-bar" @click="router.push('/')">
      <img src="/logo.svg" alt="logo" />
      <span>Copy Trader</span>
    </div>
    <div class="card">
      <h1>忘记密码</h1>
      <p class="muted">输入注册邮箱，我们会发送密码重置链接</p>

      <el-form class="form" @submit.prevent="submit">
        <el-input v-model="email" placeholder="注册邮箱" size="large" />
        <el-button type="primary" size="large" :loading="loading" @click="submit">发送重置邮件</el-button>
      </el-form>

      <div class="links">
        <router-link to="/login">返回登录</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  padding: 24px; position: relative;
}
.brand-bar {
  position: absolute; top: 24px; left: 32px;
  display: flex; align-items: center; gap: 10px;
  cursor: pointer; color: #fff; font-weight: 600;
}
.brand-bar img { width: 32px; height: 32px; }
.card {
  width: 100%; max-width: 420px;
  background: rgba(14, 20, 27, 0.85);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 18px; padding: 36px 32px; z-index: 2;
}
h1 { color: #fff; font-size: 26px; margin: 0 0 6px; }
.muted { color: #9CA3AF; margin: 0 0 24px; }
.form { display: flex; flex-direction: column; gap: 14px; }
.links { text-align: center; margin-top: 18px; font-size: 13px; }
.links a { color: var(--ct-primary); }
</style>
