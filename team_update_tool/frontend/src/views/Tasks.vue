<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-xl font-bold text-gray-900">Tasks</h2>
      <div class="flex gap-2">
        <button class="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700">+ New Task</button>
        <button class="px-4 py-2 border border-gray-200 rounded-lg text-sm font-medium hover:bg-gray-50">Kanban</button>
      </div>
    </div>
    <div class="card">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr>
              <th class="table-header">Task</th>
              <th class="table-header">Status</th>
              <th class="table-header">Team</th>
              <th class="table-header">Progress</th>
              <th class="table-header">Assigned</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="t in tasks" :key="t.name">
              <td class="table-cell font-medium">{{ t.project_title }}</td>
              <td class="table-cell"><span :class="statusClass(t.status)" class="inline-block px-2 py-0.5 rounded-full text-xs font-medium">{{ t.status }}</span></td>
              <td class="table-cell text-gray-500">{{ t.team || '-' }}</td>
              <td class="table-cell">{{ t.progress_percent || 0 }}%</td>
              <td class="table-cell text-gray-500">{{ t.assigned_to || '-' }}</td>
            </tr>
            <tr v-if="!tasks.length"><td colspan="5" class="table-cell text-center text-gray-400 py-8">No tasks found</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'
const tasks = ref([])
const statusClass = (s) => {
  const m = { Draft: 'bg-gray-100 text-gray-700', Assigned: 'bg-purple-100 text-purple-700', 'In Progress': 'bg-orange-100 text-orange-700', Completed: 'bg-blue-100 text-blue-700', 'Under Review': 'bg-yellow-100 text-yellow-700', Approved: 'bg-green-100 text-green-700', Rejected: 'bg-red-100 text-red-700' }
  return m[s] || 'bg-gray-100 text-gray-700'
}
onMounted(async () => { try { const r = await api.getProjects(); tasks.value = r.data || [] } catch {} })
</script>
