<script setup lang="ts">
import { useCreateThread } from '@/composables/data/threads/useCreateThread';
import type { Flow } from '@/services/flow';
import { useRoute, useRouter } from 'vue-router';

const props = defineProps<{ flow?: Flow | null }>();

const router = useRouter();
const route = useRoute();
const { mutateAsync: createThread, isLoading: creatingThread } = useCreateThread();

async function handleCreateThread() {
  try {
    const flowId = props.flow?.id;
    if (!flowId) return;
    const created = await createThread({ flowId });
    const slug = String(route.params.slug ?? '');
    await router.push({ name: 'ThreadFlow', params: { slug, threadId: created.id } });
  } catch (e) {
    // eslint-disable-next-line no-console
    console.error('Failed to create thread', e);
  }
}
</script>

<template>
  <Button
    :loading="creatingThread"
    :disabled="creatingThread || !props.flow"
    @click="handleCreateThread"
    class="p-button-sm p-button-primary"
  >
    Create thread
  </Button>
</template>
