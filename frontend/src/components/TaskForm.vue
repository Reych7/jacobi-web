<script setup>
import { ref } from 'vue';
import api from '../api';

const emit = defineEmits(['created']);

const matrixSize = ref(500);
const maxIterations = ref(1000);
const tolerance = ref(1e-6);
const error = ref('');
const loading = ref(false);

async function submit() {
  error.value = '';

  // Перевірка трудомісткості на клієнті (пункт 1 ТЗ)
  if (matrixSize.value < 10 || matrixSize.value > 1500) {
    error.value = 'Розмірність N має бути від 10 до 1500.';
    return;
  }
  if (maxIterations.value < 10 || maxIterations.value > 5000) {
    error.value = 'Кількість ітерацій має бути від 10 до 5000.';
    return;
  }

  loading.value = true;
  try {
    await api.post('/tasks/', {
      matrix_size: Number(matrixSize.value),
      max_iterations: Number(maxIterations.value),
      tolerance: Number(tolerance.value),
    });
    emit('created');
  } catch (err) {
    error.value = err.response?.data?.error || 'Помилка запуску задачі';
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="card">
    <h3>Нова задача СЛАР (Метод Якобі)</h3>
    <form @submit.prevent="submit" class="task-form-grid">
      <label>
        Розмір матриці N (10 – 1500)
        <input v-model.number="matrixSize" type="number" required />
      </label>

      <label>
        Макс. ітерацій (10 – 5000)
        <input v-model.number="maxIterations" type="number" required />
      </label>

      <label>
        Точність (tolerance)
        <input v-model.number="tolerance" type="number" step="any" required />
      </label>

      <button type="submit" class="btn-primary" :disabled="loading">
        {{ loading ? 'Відправка...' : 'Запустити' }}
      </button>
    </form>
    <p v-if="error" class="error-msg">{{ error }}</p>
  </div>
</template>