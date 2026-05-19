<template>
  <teleport to="body">
    <div
      v-if="modelValue"
      class="fixed inset-0 z-50 overflow-y-auto"
      aria-modal="true"
    >
      <!-- Overlay -->
      <div class="fixed inset-0 bg-black/70 transition-opacity" @click="$emit('update:modelValue', false)" />

      <!-- Panel -->
      <div class="flex min-h-full items-center justify-center p-4">
        <div class="relative bg-gray-900 rounded-xl shadow-2xl border border-gray-700 w-full max-w-lg transform transition-all">
          <!-- Header -->
          <div class="flex items-center justify-between px-6 py-4 border-b border-gray-700">
            <h3 class="text-lg font-semibold text-hotel-gold">{{ title }}</h3>
            <button
              @click="$emit('update:modelValue', false)"
              class="text-gray-400 hover:text-white transition-colors"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <!-- Body -->
          <div class="px-6 py-4">
            <slot />
          </div>
          <!-- Footer -->
          <div v-if="$slots.footer" class="px-6 py-4 border-t border-gray-700 flex justify-end gap-3">
            <slot name="footer" />
          </div>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup>
defineProps({
  modelValue: { type: Boolean, required: true },
  title: { type: String, default: '' }
});
defineEmits(['update:modelValue']);
</script>
