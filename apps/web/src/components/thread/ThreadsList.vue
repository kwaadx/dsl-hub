<script setup lang="ts">
import { computed } from 'vue';
import { useThreadsForFlow } from '@/composables/data/threads/useThreadsForFlow';
import UiLoadingDots from '@/components/UiLoadingDots.vue';
import UiErrorAlert from '@/components/UiErrorAlert.vue';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import { useRoute } from 'vue-router';

const props = defineProps<{ flowId: string }>();

const route = useRoute();
const slug = computed(() => String(route.params.slug ?? ''));

const { data: threads, isLoading, isError, error } = useThreadsForFlow(computed(() => props.flowId));
</script>

<template>
  <section class="shrink-0 flex flex-col gap-2">
    <header class="flex items-center gap-2">
      <h2 class="text-base font-medium">Threads</h2>
    </header>

    <div v-if="isLoading" class="p-3 flex items-center justify-center">
      <UiLoadingDots />
    </div>

    <UiErrorAlert v-else-if="isError" :error="error" fallback="Failed to load threads" />

    <div v-else>
      <DataTable :value="threads" tableStyle="min-width: 50rem">
        <Column field="id" header="ID">
          <template #body="{ data }">
            <RouterLink
              :to="{ name: 'ThreadFlow', params: { slug: slug, threadId: data.id } }"
              class="text-primary-600 hover:underline"
            >
              {{ data.id }}
            </RouterLink>
          </template>
        </Column>
        <Column field="status" header="Status" />
        <Column field="started_at" header="Started at">
          <template #body="{ data }">
            {{ new Date(data.started_at).toLocaleString() }}
          </template>
        </Column>

        <template #empty>
          <div class="text-sm text-surface-500 dark:text-surface-400">
            No threads yet. Create one to start a chat.
          </div>
        </template>
      </DataTable>
    </div>
  </section>
</template>
