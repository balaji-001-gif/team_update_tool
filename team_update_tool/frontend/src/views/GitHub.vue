<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-xl font-bold text-gray-900">GitHub Repositories</h2>
      <button class="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700">+ Add Repository</button>
    </div>
    <div class="card">
      <div class="overflow-x-auto"><table class="w-full"><thead><tr><th class="table-header">Project</th><th class="table-header">Repository URL</th><th class="table-header">Team</th><th class="table-header">Last Updated</th></tr></thead><tbody><tr v-if="!repos.length"><td colspan="4" class="table-cell text-center text-gray-400 py-8">No GitHub repositories linked</td></tr></tbody></table></div>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
const repos = ref([])
onMounted(async () => { repos.value = [] })
</script>
