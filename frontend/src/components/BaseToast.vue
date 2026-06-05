<template>
  <teleport to="body">
    <div class="fixed top-4 right-4 z-[9999] flex flex-col gap-3 w-80">
      <transition-group name="toast">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          :class="[
            'flex items-start gap-3 px-4 py-3 rounded-lg shadow-lg border backdrop-blur-sm',
            toastStyles[toast.type]
          ]"
        >
          <!-- Icon -->
          <span class="text-xl leading-none mt-0.5">
            {{ toast.type === 'success' ? '✓' : toast.type === 'error' ? '✕' : 'ℹ' }}
          </span>
          <!-- Text -->
          <p class="text-sm flex-1 font-medium">{{ toast.message }}</p>
          <!-- Close -->
          <button @click="remove(toast.id)" class="text-current opacity-60 hover:opacity-100 transition-opacity text-lg leading-none">&times;</button>
        </div>
      </transition-group>
    </div>
  </teleport>
</template>

<script setup>
import { ref } from 'vue';

const toasts = ref([]);
let counter = 0;

const toastStyles = {
  success: 'bg-green-900/90 border-green-700 text-green-100',
  error: 'bg-red-900/90 border-red-700 text-red-100',
  info: 'bg-gray-800/90 border-gray-600 text-gray-100',
};

function add(message, type = 'info', duration = 4000) {
  const id = ++counter;
  toasts.value.push({ id, message, type });
  if (duration > 0) {
    setTimeout(() => remove(id), duration);
  }
}

function remove(id) {
  const idx = toasts.value.findIndex(t => t.id === id);
  if (idx !== -1) toasts.value.splice(idx, 1);
}

// Expose so parent can call toast.add(...)
defineExpose({ add });
</script>

<style scoped>
.toast-enter-active, .toast-leave-active { transition: all 0.3s ease; }
.toast-enter-from { opacity: 0; transform: translateX(100%); }
.toast-leave-to { opacity: 0; transform: translateX(100%); }
</style>
