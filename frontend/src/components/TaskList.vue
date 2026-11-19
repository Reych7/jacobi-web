<script setup>
import api from '../api';

defineProps({
  tasks: {
    type: Array,
    required: true,
  },
});

const emit = defineEmits(['cancelled']);

const statusLabels = {
  queued: 'У черзі',
  running: 'Виконується',
  completed: 'Завершено',
  cancelled: 'Скасовано',
  failed: 'Помилка',
};

async function cancelTask(id) {
  try {
    await api.post(`/tasks/${id}/cancel/`);
    emit('cancelled');
  } catch (err) {
    alert(err.response?.data?.error || 'Не вдалося скасувати задачу');
  }
}
</script>

<template>
  <div class="card">
    <h3>Історія та поточні задачі</h3>
    <p v-if="tasks.length === 0" class="muted">Задач поки немає. Запустіть першу вище!</p>

    <div v-else class="task-list">
      <div v-for="t in tasks" :key="t.id" class="task-item">
        <div class="task-top">
          <div>
            <strong>Задача #{{ t.id }}</strong> · Матриця {{ t.matrix_size }}×{{ t.matrix_size }}
            <span v-if="t.server_id" class="badge server">{{ t.server_id }}</span>
          </div>
          <span class="badge" :class="t.status">{{ statusLabels[t.status] || t.status }}</span>
        </div>

        <!-- Прогрес-бар (пункт 2 ТЗ) -->
        <div class="progress-wrap">
          <div class="progress-bar" :style="{ width: t.progress + '%' }"></div>
        </div>
        <div class="task-meta">
          <span>Прогрес: {{ t.progress }}% (ітерація {{ t.current_iteration }} / {{ t.max_iterations }})</span>
          <button
            v-if="t.status === 'queued' || t.status === 'running'"
            class="btn-danger"
            @click="cancelTask(t.id)"
          >
            Скасувати
          </button>
        </div>

        <!-- Повідомлення про чергу та очікування (пункт 6 ТЗ) -->
        <p v-if="t.status === 'queued' && t.queue_position" class="queue-info">
          Позиція в черзі: #{{ t.queue_position }} · Орієнтовний час очікування: ~{{ t.estimated_wait_sec }} сек
        </p>

        <!-- Результат після завершення -->
        <div v-if="t.status === 'completed' && t.result_preview" class="result-box">
          Час: <b>{{ t.result_preview.execution_time_sec }} сек</b> ·
          Ітерацій: <b>{{ t.result_preview.iterations_used }}</b> ·
          Похибка: <b>{{ t.result_preview.final_error.toExponential(2) }}</b>
          <div class="x-sample">x[:10] = [{{ t.result_preview.x_sample.join(', ') }}]</div>
        </div>

        <p v-if="t.status === 'failed' && t.error_message" class="error-msg">{{ t.error_message }}</p>
      </div>
    </div>
  </div>
</template>