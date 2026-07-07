import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '../api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const isLoggedIn = ref(false)
  const roles = ref([])

  async function checkSession() {
    try {
      const res = await api.get('/api/method/frappe.auth.get_logged_user')
      if (res.message) {
        const userInfo = await api.get('/api/method/frappe.api.get_user_info')
        user.value = userInfo.message
        roles.value = userInfo.message?.roles || []
        isLoggedIn.value = true
        return true
      }
    } catch {
      isLoggedIn.value = false
      user.value = null
    }
    return false
  }

  async function login(email, password) {
    const res = await api.post('/api/method/login', {
      usr: email,
      pwd: password,
    })
    if (res.message === 'Logged In') {
      await checkSession()
      return true
    }
    return false
  }

  async function logout() {
    await api.post('/api/method/logout')
    user.value = null
    isLoggedIn.value = false
    roles.value = []
  }

  function hasRole(role) {
    return roles.value.includes(role)
  }

  return { user, isLoggedIn, roles, checkSession, login, logout, hasRole }
})
