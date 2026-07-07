<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-xl font-bold text-gray-900">Screenshots</h2>
      <button class="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700">+ Upload Screenshot</button>
    </div>
    <div class="card p-6">
      <div class="grid grid-cols-4 gap-4">
        <div v-for="s in screenshots" :key="s.name" class="border border-gray-200 rounded-xl overflow-hidden">
          <img :src="s.screenshot_url" class="w-full h-32 object-cover" />
          <div class="p-2 text-xs text-gray-500">{{ s.caption }}</div>
        </div>
        <div v-if="!screenshots.length" class="col-span-4 text-center text-gray-400 py-12">No screenshots uploaded yet</div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
const screenshots = ref([])
onMounted(async () => { screenshots.value = [] })
</script>
