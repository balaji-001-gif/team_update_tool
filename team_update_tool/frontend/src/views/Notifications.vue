<template>
  <div>
    <h2 class="text-xl font-bold text-gray-900 mb-6">Notifications</h2>
    <div class="card">
      <div v-for="n in notifications" :key="n.name" class="flex items-center gap-3 px-5 py-3 border-b border-gray-100 last:border-0 hover:bg-gray-50 cursor-pointer">
        <span class="text-lg">🔔</span>
        <span class="flex-1 text-sm">{{ n.subject }}</span>
        <span class="text-xs text-gray-400">{{ n.creation }}</span>
      </div>
      <div v-if="!notifications.length" class="p-8 text-center text-gray-400">No notifications</div>
    </div>
  </div>
</template>
<script setup>
import { ref } from 'vue'
const notifications = ref([])
</script>
