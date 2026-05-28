<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const form = reactive({ username: '', password: '', confirm: '', email: '', invite_code: '' })
const loading = ref(false)

onMounted(() => {
  const code = route.query.code as string | undefined
  if (code) form.invite_code = code
})

async function submit() {
  if (!form.username || !form.password) {
    ElMessage.warning('请填写用户名和密码')
    return
  }
  if (form.password !== form.confirm) {
    ElMessage.warning('两次密码不一致')
    return
  }
  loading.value = true
  try {
    await auth.register(form.username, form.password, form.email, form.invite_code)
    ElMessage.success('注册成功')
    router.push('/console')
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
      <h1>注册账号</h1>
      <p class="muted">7 天免费试用，全网交易员任意跟单</p>

      <el-form class="form" @submit.prevent="submit">
        <el-input v-model="form.username" placeholder="用户名" size="large" />
        <el-input v-model="form.email" placeholder="邮箱（可选）" size="large" />
        <el-input v-model="form.password" type="password" placeholder="设置密码" size="large" show-password />
        <el-input v-model="form.confirm" type="password" placeholder="再次输入密码" size="large" show-password />
        <el-input v-model="form.invite_code" placeholder="邀请码（可选）" size="large" />

        <el-button type="primary" size="large" :loading="loading" @click="submit">注册</el-button>
      </el-form>

      <div class="links">
        <span class="muted">已有账号？</span>
        <router-link to="/login">登录</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  padding: 24px;
  position: relative;
}
.brand-bar {
  position: absolute; top: 24px; left: 32px;
  display: flex; align-items: center; gap: 10px;
  cursor: pointer; color: #fff; font-weight: 600;
}
.brand-bar img { width: 32px; height: 32px; }
.card {
  width: 100%; max-width: 440px;
  background: rgba(14, 20, 27, 0.85);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 18px; padding: 36px 32px; z-index: 2;
}
h1 { color: #fff; font-size: 26px; margin: 0 0 6px; }
.muted { color: #9CA3AF; margin: 0 0 24px; }
.form { display: flex; flex-direction: column; gap: 12px; }
.links { display: flex; gap: 8px; justify-content: center; margin-top: 18px; font-size: 13px; }
.links a { color: var(--ct-primary); }
</style>
