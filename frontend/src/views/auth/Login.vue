<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const form = reactive({ username: '', password: '', captcha: '' })
const loading = ref(false)

async function submit() {
  if (!form.username || !form.password) {
    ElMessage.warning('请填写用户名和密码')
    return
  }
  loading.value = true
  try {
    await auth.login(form.username, form.password, form.captcha)
    ElMessage.success('登录成功')
    const redirect = (route.query.redirect as string) || '/console'
    router.push(redirect)
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
      <h1>登录</h1>
      <p class="muted">欢迎回来，请输入你的账户信息</p>

      <el-form class="form" @submit.prevent="submit">
        <el-input v-model="form.username" placeholder="用户名 / 邮箱" size="large" />
        <el-input v-model="form.password" type="password" placeholder="密码" size="large" show-password />

        <div class="captcha">
          <el-input v-model="form.captcha" placeholder="验证码" size="large" style="flex:1" />
          <div class="captcha-mock">CAPTCHA</div>
        </div>

        <el-button type="primary" size="large" :loading="loading" class="submit" @click="submit">
          登录
        </el-button>
      </el-form>

      <div class="links">
        <router-link to="/register">注册账号</router-link>
        <router-link to="/forgot">忘记密码？</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px;
  position: relative;
}
.brand-bar {
  position: absolute;
  top: 24px;
  left: 32px;
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  color: #fff;
  font-weight: 600;
}
.brand-bar img { width: 32px; height: 32px; }
.card {
  width: 100%;
  max-width: 420px;
  background: rgba(14, 20, 27, 0.85);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 18px;
  padding: 36px 32px;
  z-index: 2;
}
h1 { color: #fff; font-size: 28px; margin: 0 0 6px; }
.muted { color: #9CA3AF; margin: 0 0 24px; }
.form { display: flex; flex-direction: column; gap: 14px; }
.captcha { display: flex; gap: 10px; align-items: center; }
.captcha-mock {
  width: 110px;
  height: 40px;
  border-radius: 8px;
  background: linear-gradient(135deg, #10B981, #0D9488);
  color: #fff;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  letter-spacing: 2px;
  font-size: 13px;
}
.submit { margin-top: 6px; }
.links {
  display: flex;
  justify-content: space-between;
  margin-top: 18px;
  font-size: 13px;
}
.links a { color: var(--ct-primary); }
</style>
