import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { layout: 'blank' },
  },
  {
    path: '/',
    component: () => import('../components/AppLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '', name: 'Dashboard', component: () => import('../views/Dashboard.vue') },
      { path: 'projects', name: 'Projects', component: () => import('../views/Projects.vue') },
      { path: 'tasks', name: 'Tasks', component: () => import('../views/Tasks.vue') },
      { path: 'teams', name: 'Teams', component: () => import('../views/Teams.vue') },
      { path: 'members', name: 'Members', component: () => import('../views/Members.vue') },
      { path: 'github', name: 'GitHub', component: () => import('../views/GitHub.vue') },
      { path: 'screenshots', name: 'Screenshots', component: () => import('../views/Screenshots.vue') },
      { path: 'documents', name: 'Documents', component: () => import('../views/Documents.vue') },
      { path: 'reports', name: 'Reports', component: () => import('../views/Reports.vue') },
      { path: 'notifications', name: 'Notifications', component: () => import('../views/Notifications.vue') },
      { path: 'settings', name: 'Settings', component: () => import('../views/Settings.vue') },
      { path: 'profile', name: 'Profile', component: () => import('../views/Profile.vue') },
    ],
  },
]

const router = createRouter({
  history: createWebHistory('/team-update'),
  routes,
})

export default router
