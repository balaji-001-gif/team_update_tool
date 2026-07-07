<template>
  <div>
    <h2 class="text-xl font-bold text-gray-900 mb-6">Profile</h2>
    <div class="card max-w-2xl">
      <div class="p-6 flex items-center gap-4 border-b border-gray-100">
        <div class="w-16 h-16 rounded-full bg-green-600 flex items-center justify-center text-white font-bold text-xl">{{ initials }}</div>
        <div>
          <h3 class="font-semibold text-lg">{{ auth.user?.full_name || 'User' }}</h3>
          <p class="text-sm text-gray-500">{{ auth.user?.email || '' }}</p>
        </div>
      </div>
      <div class="p-6 space-y-4">
        <div><label class="text-xs font-medium text-gray-500 uppercase">Full Name</label><p class="text-sm mt-1">{{ auth.user?.full_name || '-' }}</p></div>
        <div><label class="text-xs font-medium text-gray-500 uppercase">Email</label><p class="text-sm mt-1">{{ auth.user?.email || '-' }}</p></div>
        <div><label class="text-xs font-medium text-gray-500 uppercase">Roles</label><p class="text-sm mt-1">{{ auth.roles.join(', ') || '-' }}</p></div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { computed } from 'vue'
import { useAuthStore } from '../stores/auth'
const auth = useAuthStore()
const initials = computed(() => (auth.user?.full_name || 'U')[0])
</script>
