import {createPinia} from 'pinia'
import {createPersistedState} from 'pinia-plugin-persistedstate'

type StorageLike = Pick<Storage, 'getItem' | 'setItem' | 'removeItem'>

const storage: StorageLike =
  typeof window !== 'undefined'
    ? window.localStorage
    : {
      getItem: () => null,
      setItem: () => {
      },
      removeItem: () => {
      },
    }

const pinia = createPinia()

pinia.use(
  createPersistedState({
    key: (id) => `dsl-hub-web-${id}`,
    storage,
  })
)

export default pinia
