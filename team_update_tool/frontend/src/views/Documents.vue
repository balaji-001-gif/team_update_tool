<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-xl font-bold text-gray-900">Documents</h2>
      <button class="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700">+ Upload Document</button>
    </div>
    <div class="card">
      <div class="overflow-x-auto"><table class="w-full"><thead><tr><th class="table-header">File</th><th class="table-header">Description</th><th class="table-header">Project</th><th class="table-header">Uploaded</th></tr></thead><tbody><tr v-if="!docs.length"><td colspan="4" class="table-cell text-center text-gray-400 py-8">No documents uploaded</td></tr></tbody></table></div>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
const docs = ref([])
onMounted(async () => { docs.value = [] })
</script>
