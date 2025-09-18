import {createRouter, createWebHistory, type RouteRecordRaw} from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'HomePage',
    component: () => import('@/pages/HomePage.vue'),
    meta: {layout: 'main'},
  },
  {
    path: '/flow/:id',
    name: 'FlowPage',
    component: () => import('@/pages/FlowPage.vue'),
    meta: {layout: 'main'},
    props: true,
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFoundPage',
    component: () => import('@/pages/NotFoundPage.vue'),
    meta: {layout: 'default'},
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior() {
    return {top: 0}
  },
})

export default router
