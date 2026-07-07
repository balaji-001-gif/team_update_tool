<template>
  <div>
    <!-- Welcome -->
    <div class="bg-gradient-to-r from-green-600 to-green-700 rounded-2xl p-6 text-white mb-6">
      <h2 class="text-2xl font-bold">Welcome back, {{ userName }} 👋</h2>
      <p class="text-green-100 mt-1">Here's what's happening with your projects today.</p>
    </div>

    <!-- Loading Skeleton -->
    <div v-if="loading" class="space-y-6">
      <div class="grid grid-cols-5 gap-4">
        <div v-for="i in 10" :key="i" class="h-24 bg-gray-200 rounded-xl animate-pulse"></div>
      </div>
      <div class="grid grid-cols-2 gap-4">
        <div v-for="i in 4" :key="i" class="h-64 bg-gray-200 rounded-xl animate-pulse"></div>
      </div>
    </div>

    <!-- Dashboard Content -->
    <div v-else-if="data">
      <!-- Stats Grid -->
      <div class="grid grid-cols-5 gap-4 mb-6">
        <div v-for="card in statCards" :key="card.label" class="stat-card">
          <span class="text-2xl">{{ card.icon }}</span>
          <div>
            <div class="text-xl font-bold text-gray-900">{{ card.value }}</div>
            <div class="text-xs text-gray-500 uppercase tracking-wider">{{ card.label }}</div>
          </div>
        </div>
      </div>

      <!-- Charts -->
      <div class="grid grid-cols-2 gap-6 mb-6">
        <div class="card">
          <div class="card-header"><h3 class="font-semibold text-sm">Project Status</h3></div>
          <div class="card-body h-64" ref="chart1Ref"></div>
        </div>
        <div class="card">
          <div class="card-header"><h3 class="font-semibold text-sm">Monthly Completed</h3></div>
          <div class="card-body h-64" ref="chart2Ref"></div>
        </div>
      </div>

      <!-- Recent Projects -->
      <div class="card mb-6">
        <div class="card-header">
          <h3 class="font-semibold text-sm">Recent Projects</h3>
          <router-link to="/projects" class="text-sm text-green-600 hover:text-green-700">View All</router-link>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr>
                <th class="table-header">Title</th>
                <th class="table-header">Status</th>
                <th class="table-header">Team</th>
                <th class="table-header">Progress</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="p in data.recent_projects?.slice(0, 8)" :key="p.name">
                <td class="table-cell font-medium">{{ p.project_title }}</td>
                <td class="table-cell"><span :class="statusClass(p.status)" class="inline-block px-2 py-0.5 rounded-full text-xs font-medium">{{ p.status }}</span></td>
                <td class="table-cell text-gray-500">{{ p.team || '-' }}</td>
                <td class="table-cell"><div class="flex items-center gap-2"><div class="flex-1 h-1.5 bg-gray-200 rounded-full"><div class="h-1.5 rounded-full" :class="progressColor(p.progress_percent)" :style="{ width: (p.progress_percent || 0) + '%' }"></div></div><span class="text-xs text-gray-500">{{ p.progress_percent || 0 }}%</span></div></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Two-column: Teams + GitHub -->
      <div class="grid grid-cols-2 gap-6 mb-6">
        <div class="card">
          <div class="card-header">
            <h3 class="font-semibold text-sm">Teams</h3>
            <router-link to="/teams" class="text-sm text-green-600 hover:text-green-700">View All</router-link>
          </div>
          <div class="card-body">
            <div v-for="t in data.teams?.slice(0, 5)" :key="t.name" class="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
              <span class="text-sm font-medium">{{ t.team_name || t.name }}</span>
              <span class="text-xs text-gray-500">{{ t.project_count }} projects</span>
            </div>
          </div>
        </div>
        <div class="card">
          <div class="card-header">
            <h3 class="font-semibold text-sm">Recent GitHub Uploads</h3>
            <router-link to="/github" class="text-sm text-green-600 hover:text-green-700">View All</router-link>
          </div>
          <div class="card-body">
            <div v-for="g in data.github_projects?.slice(0, 5)" :key="g.name" class="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
              <span class="text-sm font-medium">{{ g.project_title }}</span>
              <span class="text-xs text-gray-500">{{ g.team || '' }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="card p-8 text-center">
      <p class="text-red-500">{{ error }}</p>
      <button @click="fetchData" class="mt-4 px-4 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700">Retry</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useAuthStore } from '../stores/auth'
import { api } from '../api'

const auth = useAuthStore()
const loading = ref(true)
const data = ref(null)
const error = ref(null)
const chart1Ref = ref(null)
const chart2Ref = ref(null)

const userName = computed(() => auth.user?.full_name || 'User')

const statCards = computed(() => {
  if (!data.value?.stats) return []
  const s = data.value.stats
  return [
    { label: 'Total Projects', value: s.total_projects || 0, icon: '📊' },
    { label: 'Completed', value: s.completed || 0, icon: '✅' },
    { label: 'In Progress', value: s.in_progress || 0, icon: '🔄' },
    { label: 'Pending Review', value: s.pending_review || 0, icon: '📋' },
    { label: 'Active Teams', value: s.active_teams || 0, icon: '👥' },
    { label: 'Team Leaders', value: s.team_leaders || 0, icon: '👤' },
    { label: 'Team Members', value: s.team_members || 0, icon: '👥' },
    { label: 'All Teams', value: s.total_teams || 0, icon: '🏢' },
    { label: 'Assigned', value: s.assigned || 0, icon: '📌' },
    { label: 'Rejected', value: s.rejected || 0, icon: '❌' },
  ]
})

async function fetchData() {
  loading.value = true
  error.value = null
  try {
    const res = await api.getDashboardData()
    data.value = res.message
    await nextTick()
    renderCharts()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

function renderCharts() {
  if (!data.value?.charts) return
  const c = data.value.charts
  if (c.status_counts?.length && chart1Ref.value) {
    const colors = c.status_counts.map(s => getColor(s.status))
    const labels = c.status_counts.map(s => s.status)
    const values = c.status_counts.map(s => s.count)
    drawChart(chart1Ref.value, labels, values, colors, 'donut')
  }
  if (c.monthly_completed?.length && chart2Ref.value) {
    const labels = c.monthly_completed.map(m => m.month)
    const values = c.monthly_completed.map(m => m.count)
    drawChart(chart2Ref.value, labels, values, ['#22c55e', '#16a34a', '#15803d'], 'bar')
  }
}

function drawChart(el, labels, values, colors, type) {
  if (!el || typeof frappe === 'undefined') return
  try {
    new frappe.Chart(el, {
      data: { labels, datasets: [{ name: 'Data', values, chartType: type }] },
      type, height: 200, colors,
    })
  } catch (e) {
    console.warn('Chart rendering:', e.message)
    el.innerHTML = '<div class="flex items-center justify-center h-full text-gray-400 text-sm">Chart unavailable</div>'
  }
}

function getColor(status) {
  const m = { Draft: '#6b7280', Assigned: '#8b5cf6', 'In Progress': '#f59e0b', Completed: '#3b82f6', 'Under Review': '#eab308', Approved: '#22c55e', Rejected: '#ef4444' }
  return m[status] || '#6b7280'
}

function statusClass(status) {
  const m = { Draft: 'bg-gray-100 text-gray-700', Assigned: 'bg-purple-100 text-purple-700', 'In Progress': 'bg-orange-100 text-orange-700', Completed: 'bg-blue-100 text-blue-700', 'Under Review': 'bg-yellow-100 text-yellow-700', Approved: 'bg-green-100 text-green-700', Rejected: 'bg-red-100 text-red-700' }
  return m[status] || 'bg-gray-100 text-gray-700'
}

function progressColor(pct) {
  pct = parseInt(pct) || 0
  if (pct >= 100) return 'bg-green-500'
  if (pct >= 50) return 'bg-blue-500'
  if (pct >= 25) return 'bg-orange-500'
  return 'bg-red-500'
}

onMounted(fetchData)
</script>
