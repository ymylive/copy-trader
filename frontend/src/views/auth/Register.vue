<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import StatusBar from '@/components/StatusBar.vue'

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
    ElMessage.warning('USERNAME & PASSWORD REQUIRED')
    return
  }
  if (form.password !== form.confirm) {
    ElMessage.warning('PASSWORD MISMATCH')
    return
  }
  loading.value = true
  try {
    await new Promise((r) => setTimeout(r, 800))
    await auth.register(form.username, form.password, form.email, form.invite_code)
    ElMessage.success('ACCOUNT PROVISIONED')
    router.push('/console')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-shell">
    <StatusBar />
    <div class="brand-bar" @click="router.push('/')">
      COPY<span class="slash">//</span>TRADER<span class="ver">ACCOUNT PROVISIONING</span>
    </div>

    <div class="auth-content">
      <div class="auth-card">
        <div class="card-head">
          <span>// CREATE_ACCOUNT</span>
          <span class="cursor">▌</span>
        </div>

        <div class="card-body">
          <div class="field">
            <label>USERNAME</label>
            <input v-model="form.username" class="under-inp" />
          </div>
          <div class="field">
            <label>EMAIL (OPTIONAL)</label>
            <input v-model="form.email" class="under-inp" />
          </div>
          <div class="field">
            <label>PASSWORD</label>
            <input v-model="form.password" type="password" class="under-inp" />
          </div>
          <div class="field">
            <label>CONFIRM PASSWORD</label>
            <input v-model="form.confirm" type="password" class="under-inp" />
          </div>
          <div class="field">
            <label>INVITE CODE (OPTIONAL)</label>
            <input v-model="form.invite_code" class="under-inp" />
          </div>

          <button class="btn-cta" :disabled="loading" @click="submit">
            <span v-if="loading">▌ PROVISIONING…</span>
            <span v-else>REGISTER →</span>
          </button>

          <div class="links">
            <span class="dim">HAS ACCOUNT?</span>
            <router-link to="/login">LOGIN</router-link>
          </div>
        </div>

        <div class="card-foot">
          7-DAY FREE TRIAL · NO PAYMENT INFO REQUIRED
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
.brand-bar .ver {
  font-size: 10px; color: var(--ct-text-3); margin-left: 12px; letter-spacing: 0.12em;
}

.auth-content { flex: 1; display: flex; align-items: center; justify-content: center; padding: 40px 18px; }
.auth-card { width: 100%; max-width: 440px; border: 1px solid var(--ct-divider); background: var(--ct-bg-2); }
.card-head {
  height: 36px; display: flex; align-items: center; justify-content: space-between;
  padding: 0 16px; border-bottom: 1px solid var(--ct-divider);
  font-family: var(--ct-font-mono); font-size: 11px;
  letter-spacing: 0.12em; color: var(--ct-amber); text-transform: uppercase;
}
.cursor { color: var(--ct-amber); animation: blink 1s steps(2, start) infinite; }
@keyframes blink { to { visibility: hidden; } }

.card-body { padding: 20px 16px; display: flex; flex-direction: column; gap: 14px; }
.field { display: flex; flex-direction: column; gap: 6px; }
.field label {
  font-size: 10px; color: var(--ct-text-3);
  letter-spacing: 0.12em; text-transform: uppercase;
  font-family: var(--ct-font-mono);
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
  display: flex; gap: 10px; justify-content: center;
  font-family: var(--ct-font-mono); font-size: 10px;
  letter-spacing: 0.1em; text-transform: uppercase;
}
.links .dim { color: var(--ct-text-3); }
.links a { color: var(--ct-amber); }

.card-foot {
  padding: 8px 16px; border-top: 1px solid var(--ct-divider);
  font-family: var(--ct-font-mono); font-size: 10px;
  color: var(--ct-text-3); letter-spacing: 0.1em; text-transform: uppercase;
}
</style>
