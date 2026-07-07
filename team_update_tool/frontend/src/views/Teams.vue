<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-xl font-bold text-gray-900">Teams</h2>
      <button class="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700">+ New Team</button>
    </div>
    <div class="grid grid-cols-3 gap-4">
      <div v-for="t in teams" :key="t.name" class="card p-5">
        <div class="flex items-center justify-between mb-3">
          <h3 class="font-semibold text-gray-900">{{ t.team_name || t.name }}</h3>
          <span :class="t.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'" class="px-2 py-0.5 rounded-full text-xs font-medium">{{ t.is_active ? 'Active' : 'Inactive' }}</span>
        </div>
        <p class="text-sm text-gray-500 mb-2">{{ t.team_type || 'General' }}</p>
        <div class="flex items-center gap-4 text-sm text-gray-500">
          <span>👤 {{ t.team_lead || 'No lead' }}</span>
          <span>📋 {{ t.project_count || 0 }} projects</span>
        </div>
      </div>
      <div v-if="!teams.length" class="col-span-3 card p-8 text-center text-gray-400">No teams found</div>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'
const teams = ref([])
onMounted(async () => { try { const r = await api.getTeams(); teams.value = r.data || [] } catch {} })
</script>
