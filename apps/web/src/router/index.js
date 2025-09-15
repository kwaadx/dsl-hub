import { createRouter, createWebHistory } from 'vue-router'

import layoutDefault from '@/layouts/default'
import store from '@/store'

const routes = [
  {
    path: '/',
    name: 'Main',
    component: () => import('@/pages/Main'),
    meta: { requiresAuth: true },
  },
  {
    path: '/404',
    name: '404',
    component: () => import('@/components/404'),
  },
  {
    path: '/:catchAll(.*)',
    redirect: '/404',
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

router.beforeEach((to, from, next) => {
  to.meta.layout = layoutDefault

  next()
})

export default router
