<template>
  <div>
    <h2 class="text-xl font-bold text-gray-900 mb-6">Reports</h2>
    <div class="grid grid-cols-2 gap-4">
      <div v-for="r in reports" :key="r.name" class="card p-5 cursor-pointer hover:shadow-md transition-shadow">
        <h3 class="font-semibold text-gray-900">{{ r.title }}</h3>
        <p class="text-sm text-gray-500 mt-1">{{ r.description }}</p>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref } from 'vue'
const reports = ref([{ name: 'project-status', title: 'Project Status Summary', description: 'Overview of all projects with status, progress, and assignments.' }])
</script>
