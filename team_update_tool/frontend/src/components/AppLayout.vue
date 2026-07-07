<template>
  <div class="flex h-screen bg-gray-50">
    <Sidebar :collapsed="sidebarCollapsed" @toggle="sidebarCollapsed = !sidebarCollapsed" />
    <div class="flex-1 flex flex-col overflow-hidden" :class="{ 'ml-0': sidebarCollapsed }">
      <TopNavbar @toggle-sidebar="sidebarCollapsed = !sidebarCollapsed" />
      <main class="flex-1 overflow-y-auto p-6">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Sidebar from './Sidebar.vue'
import TopNavbar from './TopNavbar.vue'

const sidebarCollapsed = ref(false)
</script>
