import {createRouter, createWebHistory, type RouteRecordRaw} from 'vue-router'
import layoutDefault from '@/layouts/default.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/agent',
    name: 'AgentPage',
    component: () => import('@/pages/AgentPage.vue'),
    meta: {
      layout: layoutDefault,
    },
  },
  {
    path: '/404',
    name: '404Page',
    component: () => import('@/pages/404Page.vue'),
    meta: {
      layout: layoutDefault,
    },
  },
  {path: '/:pathMatch(.*)*', redirect: '/404'}
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) return savedPosition
    if (to.hash) return {el: to.hash}
    return {top: 0}
  },
})

export default router
