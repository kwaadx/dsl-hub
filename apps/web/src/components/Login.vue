<template>
  <div class="bg-animation"></div>
  <div class="grid grid-nogutter justify-content-center align-items-center bbh-h-screen">
    <div class="lg:col-2 md:col-6 col-12">
      <form autocomplete="on" class="md:m-0 m-4 back" @submit.prevent="onSubmit">
        <div class="p-4">
          <div class="text-center mb-3">
            <img alt="Logo" class="w-full" src="@/assets/images/logo.svg" />
          </div>
          <label class="block mb-2" for="username">
            {{ $t('field.username') }}
          </label>
          <InputText
            id="username"
            v-model="username"
            :class="{ 'p-invalid': errors.username }"
            autocomplete="username"
            class="w-full mb-2"
            name="username"
          />
          <div class="flex justify-content-between mb-4">
            <small class="text-red-400">{{ errors.username }}</small>
          </div>
          <label class="block mb-2" for="password">
            {{ $t('field.password') }}
          </label>
          <Password
            v-model="password"
            :class="{ 'p-invalid': errors.password }"
            :feedback="false"
            :input-props="{ id: 'password', autocomplete: 'current-password', name: 'password' }"
            class="w-full mb-2"
            input-class="w-full"
            toggle-mask
          />
          <div class="flex justify-content-between mb-4">
            <small class="text-red-400">{{ errors.password }}</small>
          </div>
          <Button
            :label="$t('button.login')"
            :loading="isAuthenticating"
            class="w-full"
            icon="pi pi-user"
            type="submit"
          />
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
  import { useField, useForm } from 'vee-validate'
  import { computed, onMounted, onUnmounted, watch } from 'vue'
  import { useI18n } from 'vue-i18n'
  import { useRouter } from 'vue-router'
  import { useStore } from 'vuex'
  import * as yup from 'yup'

  import { prepareFormData } from '@/utils/prepareFormData'

  const store = useStore()
  const router = useRouter()
  const { t } = useI18n()

  const schema = yup.object({
    username: yup.string().required().label(t('field.username')),
    password: yup.string().required().label(t('field.password')),
  })

  const { handleSubmit, errors } = useForm({
    validationSchema: schema,
  })

  const { value: username } = useField('username')
  const { value: password } = useField('password')

  const isAuthenticated = computed(() => store.getters['auth/isAuthenticated'])
  const isAuthenticating = computed(() => store.getters['auth/isAuthenticating'])

  watch(isAuthenticated, (newVal) => {
    if (newVal) {
      router.push('/')
    }
  })

  const onSubmit = handleSubmit((values) => {
    const formData = prepareFormData(values)
    store.dispatch('auth/login', formData)
  })

  const setViewportHeight = () => {
    const vh = window.innerHeight * 0.01
    document.documentElement.style.setProperty('--vh', `${vh}px`)
  }

  onMounted(() => {
    setViewportHeight()
    window.addEventListener('resize', setViewportHeight)
  })

  onUnmounted(() => {
    window.removeEventListener('resize', setViewportHeight)
  })
</script>

<style scoped>
  .bbh-h-screen {
    height: calc(var(--vh, 1vh) * 100);
  }

  .bg-animation {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    z-index: -1;
    pointer-events: none;
    opacity: 0.5;
    background:
      radial-gradient(
        circle at 30% 40%,
        rgba(0, 255, 255, 0.7) 0%,
        rgba(0, 0, 0, 0.1) 50%,
        transparent 70%
      ),
      radial-gradient(
        circle at 70% 60%,
        rgba(255, 0, 255, 0.7) 0%,
        rgba(0, 0, 0, 0.1) 50%,
        transparent 70%
      ),
      radial-gradient(
        circle at 50% 20%,
        rgba(0, 150, 255, 0.6) 0%,
        rgba(0, 0, 0, 0.1) 50%,
        transparent 80%
      );
    background-size: 150% 150%;
    background-repeat: no-repeat;
    animation:
      cyberFlow 16s infinite alternate ease-in-out,
      pulse 8s infinite ease-in-out;
    filter: blur(10px);
  }

  @keyframes cyberFlow {
    0% {
      background-position:
        0% 0%,
        100% 100%,
        50% 50%;
    }
    50% {
      background-position:
        100% 0%,
        0% 100%,
        50% 100%;
    }
    100% {
      background-position:
        0% 0%,
        100% 100%,
        50% 50%;
    }
  }

  @keyframes pulse {
    0%,
    100% {
      opacity: 0.4;
    }
    50% {
      opacity: 0.6;
    }
  }
</style>
