<script setup>
defineProps({
  monitorData: {
    type: Object,
    required: true,
  },
});
</script>

<template>
  <div class="stack">
    <div class="card">
      <h3>Стан серверів застосувань (Load Balancing & Scaling)</h3>
      <table>
        <thead>
          <tr>
            <th>Сервер</th>
            <th>Статус</th>
            <th>Слоти (задачі)</th>
            <th>CPU %</th>
            <th>RAM %</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in monitorData.servers" :key="s.server_id">
            <td><strong>{{ s.server_id }}</strong></td>
            <td>
              <span class="badge" :class="s.is_online ? 'completed' : 'failed'">
                {{ s.is_online ? 'Онлайн' : 'Офлайн' }}
              </span>
            </td>
            <td>{{ s.active_tasks }} / {{ s.max_slots }}</td>
            <td>{{ s.cpu_percent }}%</td>
            <td>{{ s.ram_percent }}%</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="card">
      <h3>Усі активні процеси та черга в системі</h3>
      <p v-if="monitorData.active_tasks.length === 0" class="muted">Активних процесів зараз немає.</p>
      <table v-else>
        <thead>
          <tr>
            <th>ID</th>
            <th>Користувач</th>
            <th>Розмір N</th>
            <th>Статус</th>
            <th>Прогрес</th>
            <th>Сервер</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in monitorData.active_tasks" :key="t.id">
            <td>#{{ t.id }}</td>
            <td>{{ t.username }}</td>
            <td>{{ t.matrix_size }}×{{ t.matrix_size }}</td>
            <td><span class="badge" :class="t.status">{{ t.status }}</span></td>
            <td>{{ t.progress }}%</td>
            <td><strong>{{ t.server_id }}</strong></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>