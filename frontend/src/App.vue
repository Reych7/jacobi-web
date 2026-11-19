<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import api from './api';
import AuthForm from './components/AuthForm.vue';
import TaskForm from './components/TaskForm.vue';
import TaskList from './components/TaskList.vue';
import AdminMonitor from './components/AdminMonitor.vue';

const user = ref(null);
const tasks = ref([]);
const monitorData = ref({ servers: [], active_tasks: [] });
const activeTab = ref('tasks');
const checkingAuth = ref(true);

let pollTimer = null;

async function fetchTasks() {
  if (!user.value) return;
  try {
    const res = await api.get('/tasks/');
    tasks.value = res.data;
  } catch (e) {
    // Ігноруємо тимчасові збої опитування
  }
}

async function fetchMonitor() {
  if (!user.value?.is_staff) return;
  try {
    const res = await api.get('/monitor/');
    monitorData.value = res.data;
  } catch (e) {
    // Ігноруємо
  }
}

function startPolling() {
  stopPolling();
  fetchTasks();
  if (user.value?.is_staff) fetchMonitor();
  pollTimer = setInterval(() => {
    fetchTasks();
    if (user.value?.is_staff && activeTab.value === 'monitor') {
      fetchMonitor();
    }
  }, 1000);
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
}

function onAuthenticated(userData) {
  user.value = userData;
  activeTab.value = 'tasks';
  startPolling();
}

async function logout() {
  await api.post('/auth/logout/');
  stopPolling();
  user.value = null;
  tasks.value = [];
}

onMounted(async () => {
  try {
    const res = await api.get('/auth/me/');
    user.value = res.data;
    startPolling();
  } catch {
    user.value = null;
  } finally {
    checkingAuth.value = false;
  }
});

onUnmounted(stopPolling);
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <div class="brand">Jacobi SLAE Solver · Distributed</div>
      <div v-if="user" class="nav-right">
        <button
          v-if="user.is_staff"
          class="tab-btn"
          :class="{ active: activeTab === 'tasks' }"
          @click="activeTab = 'tasks'"
        >
          Мої задачі
        </button>
        <button
          v-if="user.is_staff"
          class="tab-btn"
          :class="{ active: activeTab === 'monitor' }"
          @click="activeTab = 'monitor'; fetchMonitor()"
        >
          Моніторинг серверів
        </button>
        <span class="user-pill">{{ user.username }}</span>
        <button class="btn-secondary" @click="logout">Вийти</button>
      </div>
    </header>

    <main class="container">
      <p v-if="checkingAuth" class="muted">Завантаження...</p>

      <AuthForm v-else-if="!user" @authenticated="onAuthenticated" />

      <div v-else-if="activeTab === 'tasks'" class="stack">
        <TaskForm @created="fetchTasks" />
        <TaskList :tasks="tasks" @cancelled="fetchTasks" />
      </div>

      <AdminMonitor v-else-if="activeTab === 'monitor' && user.is_staff" :monitor-data="monitorData" />
    </main>
  </div>
</template>