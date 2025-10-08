import {createRouter, createWebHistory, type RouteRecordRaw} from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/HomeView.vue'),
    meta: {
      layout: 'main'
    },
  },
  {
    path: '/flows/:slug',
    name: 'Flow',
    component: () => import('@/views/FlowView.vue'),
    meta: {
      layout: 'main',
    },
    props: true,
    children: [
      {
        path: 'pipelines/:pipelineId',
        name: 'PipelineFlow',
        component: () => import('@/views/flow/PipelineFlowView.vue'),
        meta: {
          layout: 'main',
        },
        props: true,
      },
      {
        path: 'threads/:threadId',
        name: 'ThreadFlow',
        component: () => import('@/views/flow/ThreadFlowView.vue'),
        meta: {
          layout: 'main',
        },
        props: true,
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFoundView.vue'),
    meta: {
      layout: 'default'
    },
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior() {
    return { top: 0 }
  },
})

export default router
