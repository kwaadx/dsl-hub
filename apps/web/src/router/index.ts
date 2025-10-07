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
    name: 'Flow',
    component: () => import('@/views/FlowView.vue'),
    meta: {layout: 'main'},
    redirect: {name: 'DetailFlow'},
    props: true,
    children: [
      {
        path: 'details',
        name: 'DetailFlow',
        component: () => import('@/views/flow/DetailFlowView.vue'),
        props: true,
      },
      {
        path: 'pipelines',
        name: 'PipelineFlow',
        component: () => import('@/views/flow/PipelineFlowView.vue'),
        props: true,
      },
      {
        path: 'threads',
        name: 'ThreadFlow',
        component: () => import('@/views/flow/ThreadFlowView.vue'),
        props: true,
      },
    ],
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
