<script setup>
import { ref } from 'vue';
import api from '../api';

const emit = defineEmits(['authenticated']);

const isRegister = ref(false);
const username = ref('');
const password = ref('');
const error = ref('');
const loading = ref(false);

async function submit() {
  error.value = '';
  loading.value = true;
  try {
    const endpoint = isRegister.value ? '/auth/register/' : '/auth/login/';
    const res = await api.post(endpoint, {
      username: username.value,
      password: password.value,
    });
    emit('authenticated', res.data);
  } catch (err) {
    error.value = err.response?.data?.error || 'Помилка авторизації';
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="card auth-card">
    <h2>{{ isRegister ? 'Реєстрація' : 'Вхід у систему' }}</h2>

    <form @submit.prevent="submit" class="form-stack">
      <label>
        Логін
        <input v-model="username" type="text" required placeholder="Введіть логін" />
      </label>

      <label>
        Пароль
        <input v-model="password" type="password" required placeholder="Мінімум 6 символів" />
      </label>

      <p v-if="error" class="error-msg">{{ error }}</p>

      <button type="submit" class="btn-primary" :disabled="loading">
        {{ loading ? 'Зачекайте...' : (isRegister ? 'Зареєструватися' : 'Увійти') }}
      </button>
    </form>

    <button class="btn-link" @click="isRegister = !isRegister; error = ''">
      {{ isRegister ? 'Вже є акаунт? Увійти' : 'Немає акаунту? Зареєструватися' }}
    </button>
  </div>
</template>