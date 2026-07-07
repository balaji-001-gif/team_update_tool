<template>
  <router-view />
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'

const router = useRouter()
const auth = useAuthStore()

onMounted(async () => {
  const loggedIn = await auth.checkSession()
  if (!loggedIn && router.currentRoute.value.name !== 'Login') {
    router.push('/login')
  }
})
</script>
