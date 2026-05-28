<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import StatusBar from '@/components/StatusBar.vue'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const form = reactive({ username: '', password: '', captcha: '' })
const loading = ref(false)

async function submit() {
  if (!form.username || !form.password) {
    ElMessage.warning('USERNAME & PASSWORD REQUIRED')
    return
  }
  loading.value = true
  try {
    await new Promise((r) => setTimeout(r, 800))
    await auth.login(form.username, form.password, form.captcha)
    ElMessage.success('AUTHENTICATED')
    const redirect = (route.query.redirect as string) || '/console'
    router.push(redirect)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-shell">
    <StatusBar />

    <div class="brand-bar" @click="router.push('/')">
      COPY<span class="slash">//</span>TRADER<span class="ver">AUTH MODULE</span>
    </div>

    <div class="auth-content">
      <div class="auth-card">
        <div class="card-head">
          <span>// AUTHENTICATE</span>
          <span class="cursor">▌</span>
        </div>

        <div class="card-body">
          <div class="field">
            <label>USERNAME / EMAIL</label>
            <input v-model="form.username" class="under-inp" autocomplete="username" />
          </div>
          <div class="field">
            <label>PASSWORD</label>
            <input v-model="form.password" type="password" class="under-inp" autocomplete="current-password" />
          </div>
          <div class="field captcha-field">
            <label>CAPTCHA</label>
            <div class="captcha-row">
              <input v-model="form.captcha" class="under-inp" style="flex:1" />
              <div class="captcha-mock">A4XK</div>
            </div>
          </div>

          <button class="btn-cta" :disabled="loading" @click="submit">
            <span v-if="loading">▌ AUTHENTICATING…</span>
            <span v-else>LOGIN →</span>
          </button>

          <div class="links">
            <router-link to="/register">CREATE ACCOUNT</router-link>
            <router-link to="/forgot">FORGOT PASSWORD?</router-link>
          </div>
        </div>

        <div class="card-foot">
          TLS 1.3 · TOKEN ROTATION · NO PASSWORD LOGS
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-shell {
  min-height: 100vh;
  background: var(--ct-bg);
  color: var(--ct-text);
  padding-top: 22px;
  display: flex;
  flex-direction: column;
}
.brand-bar {
  height: 52px;
  display: flex;
  align-items: center;
  padding: 0 18px;
  border-bottom: 1px solid var(--ct-divider);
  cursor: pointer;
  font-family: var(--ct-font-mono);
  font-size: 16px;
  font-weight: 700;
  color: var(--ct-text);
  letter-spacing: 0.02em;
}
.brand-bar .slash { color: var(--ct-amber); }
.brand-bar .ver {
  font-size: 10px;
  color: var(--ct-text-3);
  margin-left: 12px;
  letter-spacing: 0.12em;
}

.auth-content {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 18px;
}
.auth-card {
  width: 100%;
  max-width: 420px;
  border: 1px solid var(--ct-divider);
  background: var(--ct-bg-2);
}
.card-head {
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  border-bottom: 1px solid var(--ct-divider);
  font-family: var(--ct-font-mono);
  font-size: 11px;
  letter-spacing: 0.12em;
  color: var(--ct-amber);
  text-transform: uppercase;
}
.cursor {
  color: var(--ct-amber);
  animation: blink 1s steps(2, start) infinite;
}
@keyframes blink { to { visibility: hidden; } }

.card-body {
  padding: 20px 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.field { display: flex; flex-direction: column; gap: 6px; }
.field label {
  font-size: 10px;
  color: var(--ct-text-3);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  font-family: var(--ct-font-mono);
}
.under-inp {
  background: transparent;
  border: 0;
  border-bottom: 1px solid var(--ct-divider-strong);
  color: var(--ct-text);
  font-family: var(--ct-font-mono);
  font-size: 14px;
  padding: 4px 0;
  outline: 0;
}
.under-inp:focus { border-bottom-color: var(--ct-amber); }
.captcha-row { display: flex; gap: 10px; align-items: center; }
.captcha-mock {
  background: repeating-linear-gradient(45deg, #11171F 0 4px, #1A2230 4px 8px);
  color: var(--ct-amber);
  font-family: var(--ct-font-mono);
  font-weight: 700;
  letter-spacing: 0.3em;
  font-size: 14px;
  padding: 8px 16px;
  border: 1px solid var(--ct-divider-strong);
}

.btn-cta {
  height: 40px;
  background: var(--ct-amber);
  border: 1px solid var(--ct-amber);
  color: #0A0E14;
  font-family: var(--ct-font-mono);
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  font-weight: 600;
  cursor: pointer;
  margin-top: 6px;
}
.btn-cta:hover:not(:disabled) { filter: brightness(1.08); }
.btn-cta:disabled { opacity: 0.6; cursor: not-allowed; }

.links {
  display: flex;
  justify-content: space-between;
  font-family: var(--ct-font-mono);
  font-size: 10px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}
.links a { color: var(--ct-amber); }
.links a:hover { filter: brightness(1.2); }

.card-foot {
  padding: 8px 16px;
  border-top: 1px solid var(--ct-divider);
  font-family: var(--ct-font-mono);
  font-size: 10px;
  color: var(--ct-text-3);
  letter-spacing: 0.1em;
  text-transform: uppercase;
}
</style>
