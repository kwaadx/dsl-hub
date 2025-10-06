import {createRouter, createWebHistory, type RouteRecordRaw} from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/HomeView.vue'),
    meta: {layout: 'main'},
  },
  {
    path: '/flows/:slug',
    name: 'FlowRoot',
    redirect: to => ({name: 'Flow', params: {slug: to.params.slug, mode: 'agent'}}),
  },
  {
    path: '/flows/:slug/:mode(agent)',
    name: 'Flow',
    component: () => import('@/views/FlowView.vue'),
    meta: {layout: 'main'},
    props: true,
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFoundView.vue'),
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
