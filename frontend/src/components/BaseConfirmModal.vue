<template>
  <teleport to="body">
    <div
      v-if="modelValue"
      class="fixed inset-0 z-50 overflow-y-auto"
      aria-modal="true"
    >
      <div class="fixed inset-0 bg-black/70 transition-opacity" @click="cancel" />
      <div class="flex min-h-full items-center justify-center p-4">
        <div class="relative bg-gray-900 rounded-xl shadow-2xl border border-gray-700 w-full max-w-sm transform transition-all">
          <div class="px-6 py-4 text-center">
            <div v-if="icon" class="mx-auto mb-3 w-12 h-12 rounded-full flex items-center justify-center" :class="iconClass">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path v-if="variant === 'danger'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p class="text-sm text-gray-300">{{ message }}</p>
          </div>
          <div class="px-6 py-4 border-t border-gray-700 flex justify-center gap-3">
            <BaseButton variant="secondary" @click="cancel">Cancelar</BaseButton>
            <BaseButton :variant="variant === 'danger' ? 'danger' : 'primary'" :disabled="loading" @click="confirm">
              {{ loading ? 'Procesando...' : confirmText }}
            </BaseButton>
          </div>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup>
import BaseButton from './BaseButton.vue';

const props = defineProps({
  modelValue: { type: Boolean, required: true },
  message: { type: String, required: true },
  confirmText: { type: String, default: 'Confirmar' },
  variant: { type: String, default: 'danger' },
  loading: { type: Boolean, default: false },
  icon: { type: Boolean, default: true },
});

const emit = defineEmits(['update:modelValue', 'confirm']);

const iconClass = props.variant === 'danger'
  ? 'bg-red-900/30 text-red-400'
  : 'bg-yellow-900/30 text-yellow-400';

function cancel() {
  emit('update:modelValue', false);
}

function confirm() {
  emit('confirm');
}
</script>
