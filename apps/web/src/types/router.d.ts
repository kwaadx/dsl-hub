import 'vue-router'

type LayoutKey = 'default' | 'main'

declare module 'vue-router' {
  interface RouteMeta {
    layout?: LayoutKey
  }
}
