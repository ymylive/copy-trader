<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authApi } from '@/api/auth'
import StatusBar from '@/components/StatusBar.vue'

const router = useRouter()
const email = ref('')
const loading = ref(false)

async function submit() {
  if (!email.value) {
    ElMessage.warning('EMAIL REQUIRED')
    return
  }
  loading.value = true
  try {
    await new Promise((r) => setTimeout(r, 700))
    await authApi.forgot(email.value)
    ElMessage.success('RESET LINK DISPATCHED')
    router.push('/login')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-shell">
    <StatusBar />
    <div class="brand-bar" @click="router.push('/')">
      COPY<span class="slash">//</span>TRADER<span class="ver">PASSWORD RESET</span>
    </div>

    <div class="auth-content">
      <div class="auth-card">
        <div class="card-head">
          <span>// RESET_PASSWORD</span>
          <span class="cursor">▌</span>
        </div>

        <div class="card-body">
          <p class="hint">SEND RESET LINK TO REGISTERED EMAIL · LINK VALID FOR 30 MINUTES.</p>
          <div class="field">
            <label>REGISTERED EMAIL</label>
            <input v-model="email" class="under-inp" />
          </div>
          <button class="btn-cta" :disabled="loading" @click="submit">
            <span v-if="loading">▌ DISPATCHING…</span>
            <span v-else>SEND RESET LINK →</span>
          </button>
          <div class="links">
            <router-link to="/login">BACK TO LOGIN</router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-shell { min-height: 100vh; background: var(--ct-bg); color: var(--ct-text); padding-top: 22px; display: flex; flex-direction: column; }
.brand-bar {
  height: 52px; display: flex; align-items: center; padding: 0 18px;
  border-bottom: 1px solid var(--ct-divider); cursor: pointer;
  font-family: var(--ct-font-mono); font-size: 16px; font-weight: 700;
  color: var(--ct-text); letter-spacing: 0.02em;
}
.brand-bar .slash { color: var(--ct-amber); }
.brand-bar .ver { font-size: 10px; color: var(--ct-text-3); margin-left: 12px; letter-spacing: 0.12em; }

.auth-content { flex: 1; display: flex; align-items: center; justify-content: center; padding: 40px 18px; }
.auth-card { width: 100%; max-width: 420px; border: 1px solid var(--ct-divider); background: var(--ct-bg-2); }
.card-head {
  height: 36px; display: flex; align-items: center; justify-content: space-between;
  padding: 0 16px; border-bottom: 1px solid var(--ct-divider);
  font-family: var(--ct-font-mono); font-size: 11px;
  letter-spacing: 0.12em; color: var(--ct-amber); text-transform: uppercase;
}
.cursor { color: var(--ct-amber); animation: blink 1s steps(2, start) infinite; }
@keyframes blink { to { visibility: hidden; } }

.card-body { padding: 20px 16px; display: flex; flex-direction: column; gap: 16px; }
.hint {
  color: var(--ct-text-2); font-family: var(--ct-font-mono); font-size: 11px;
  letter-spacing: 0.08em; line-height: 1.6;
}
.field { display: flex; flex-direction: column; gap: 6px; }
.field label {
  font-size: 10px; color: var(--ct-text-3); letter-spacing: 0.12em;
  text-transform: uppercase; font-family: var(--ct-font-mono);
}
.under-inp {
  background: transparent; border: 0;
  border-bottom: 1px solid var(--ct-divider-strong);
  color: var(--ct-text); font-family: var(--ct-font-mono);
  font-size: 14px; padding: 4px 0; outline: 0;
}
.under-inp:focus { border-bottom-color: var(--ct-amber); }

.btn-cta {
  height: 40px; background: var(--ct-amber); border: 1px solid var(--ct-amber);
  color: #0A0E14; font-family: var(--ct-font-mono);
  font-size: 12px; letter-spacing: 0.12em; text-transform: uppercase;
  font-weight: 600; cursor: pointer; margin-top: 6px;
}
.btn-cta:hover:not(:disabled) { filter: brightness(1.08); }
.btn-cta:disabled { opacity: 0.6; cursor: not-allowed; }

.links {
  text-align: center; font-family: var(--ct-font-mono);
  font-size: 10px; letter-spacing: 0.12em; text-transform: uppercase;
}
.links a { color: var(--ct-amber); }
</style>
