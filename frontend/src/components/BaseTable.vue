<template>
  <div class="overflow-x-auto shadow ring-1 ring-black ring-opacity-5 sm:rounded-lg">
    <table class="min-w-full divide-y divide-gray-700">
      <thead class="bg-gray-800">
        <tr>
          <th
            v-for="column in columns"
            :key="column.key"
            scope="col"
            class="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider"
          >
            {{ column.label }}
          </th>
        </tr>
      </thead>
      <tbody class="bg-gray-900 divide-y divide-gray-800">
        <tr v-for="(row, index) in data" :key="row.id || index" class="hover:bg-gray-800">
          <td
            v-for="column in columns"
            :key="column.key"
            class="px-6 py-4 whitespace-nowrap text-sm text-gray-300"
          >
            <slot :name="column.key" :item="row">
              {{ row[column.key] }}
            </slot>
          </td>
        </tr>
        <tr v-if="data.length === 0">
          <td :colspan="columns.length" class="px-6 py-4 text-center text-sm text-gray-500">
            No hay datos disponibles
          </td>
        </tr>
      </tbody>
    </table>
    <!-- Paginación Básica (opcional/expandible) -->
    <div v-if="pagination" class="bg-gray-800 px-4 py-3 flex items-center justify-between border-t border-gray-700 sm:px-6">
      <div class="flex-1 flex justify-between sm:hidden">
        <button @click="$emit('prev')" class="relative inline-flex items-center px-4 py-2 border border-gray-600 text-sm font-medium rounded-md text-gray-300 bg-gray-700 hover:bg-gray-600">
          Anterior
        </button>
        <button @click="$emit('next')" class="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-600 text-sm font-medium rounded-md text-gray-300 bg-gray-700 hover:bg-gray-600">
          Siguiente
        </button>
      </div>
      <div class="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
        <div>
          <p class="text-sm text-gray-400">
            Página <span class="font-medium text-gray-200">{{ currentPage }}</span> de <span class="font-medium text-gray-200">{{ totalPages }}</span>
          </p>
        </div>
        <div>
          <nav class="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
            <button @click="$emit('prev')" :disabled="currentPage <= 1" class="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-600 bg-gray-800 text-sm font-medium text-gray-400 hover:bg-gray-700">
              <span class="sr-only">Anterior</span>
              &larr;
            </button>
            <button @click="$emit('next')" :disabled="currentPage >= totalPages" class="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-600 bg-gray-800 text-sm font-medium text-gray-400 hover:bg-gray-700">
              <span class="sr-only">Siguiente</span>
              &rarr;
            </button>
          </nav>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  columns: {
    type: Array,
    required: true
    // [{ key: 'id', label: 'ID' }]
  },
  data: {
    type: Array,
    default: () => []
  },
  pagination: {
    type: Boolean,
    default: false
  },
  currentPage: {
    type: Number,
    default: 1
  },
  totalPages: {
    type: Number,
    default: 1
  }
});
defineEmits(['prev', 'next']);
</script>
