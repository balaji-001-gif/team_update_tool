<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-xl font-bold text-gray-900">Projects</h2>
      <button class="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700">+ New Project</button>
    </div>
    <div class="card">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr>
              <th class="table-header">Title</th>
              <th class="table-header">Status</th>
              <th class="table-header">Team</th>
              <th class="table-header">Priority</th>
              <th class="table-header">Progress</th>
              <th class="table-header">Assigned To</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in projects" :key="p.name">
              <td class="table-cell font-medium">{{ p.project_title }}</td>
              <td class="table-cell"><span :class="statusClass" class="inline-block px-2 py-0.5 rounded-full text-xs font-medium">{{ p.state }}</span></td>
              <td class="table-cell text-gray-500">{{ p.team || '-' }}</td>
              <td class="table-cell text-gray-500">{{ p.priority || '-' }}</td>
              <td class="table-cell">{{ p.progress_percent || 0 }}%</td>
              <td class="table-cell text-gray-500">{{ p.assigned_to || '-' }}</td>
            </tr>
            <tr v-if="!projects.length"><td colspan="6" class="table-cell text-center text-gray-400 py-8">No projects found</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
const projects = ref([])
const statusClass = 'bg-gray-100 text-gray-700'
onMounted(async () => {
  // Data will be fetched from Frappe API
  projects.value = []
})
</script>
