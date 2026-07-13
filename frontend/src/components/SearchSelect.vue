<template>
  <div class="relative" ref="container">
    <div
      class="input-field w-full flex items-center"
      :class="['cursor-pointer', { 'ring-1 ring-hotel-gold': isOpen, 'opacity-50 cursor-not-allowed': disabled }]"
      @click="disabled ? null : toggle()"
    >
      <span v-if="selectedLabel" class="text-gray-200 flex-1 truncate">{{ selectedLabel }}</span>
      <span v-else class="text-gray-500 flex-1 truncate">{{ placeholder }}</span>
      <svg class="w-4 h-4 text-gray-500 transition-transform" :class="{ 'rotate-180': isOpen }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
      </svg>
    </div>
    <div
      v-if="isOpen && !disabled"
      class="absolute z-50 mt-1 w-full bg-gray-800 border border-gray-700 rounded-lg shadow-xl max-h-60 flex flex-col"
    >
      <div class="p-1.5 border-b border-gray-700">
        <input
          ref="searchInput"
          v-model="search"
          type="text"
          class="w-full bg-gray-900 text-gray-200 text-sm rounded-md px-3 py-1.5 placeholder-gray-500 border border-gray-700 focus:outline-none focus:border-hotel-gold"
          placeholder="Buscar..."
          @click.stop
        />
      </div>
      <div class="overflow-y-auto flex-1">
        <button
          v-for="option in filteredOptions"
          :key="option.value"
          class="w-full text-left px-3 py-2 text-sm text-gray-300 hover:bg-gray-700 hover:text-white transition-colors"
          :class="{ 'bg-gray-700 text-white': option.value === modelValue }"
          @click="select(option)"
        >
          {{ option.label }}
        </button>
        <div v-if="filteredOptions.length === 0" class="px-3 py-4 text-center text-gray-600 text-sm">
          Sin resultados
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'

const props = defineProps({
  modelValue: { type: [Number, String], default: null },
  options: { type: Array, required: true },
  placeholder: { type: String, default: 'Seleccionar...' },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue'])

const container = ref(null)
const searchInput = ref(null)
const search = ref('')
const isOpen = ref(false)

const selectedLabel = computed(() => {
  const opt = props.options.find(o => o.value === props.modelValue)
  return opt ? opt.label : null
})

const filteredOptions = computed(() => {
  if (!search.value) return props.options
  const q = search.value.toLowerCase()
  return props.options.filter(o => o.label.toLowerCase().includes(q))
})

function toggle() {
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    search.value = ''
    nextTick(() => searchInput.value?.focus())
  }
}

function select(option) {
  emit('update:modelValue', option.value)
  isOpen.value = false
  search.value = ''
}

function handleClickOutside(e) {
  if (container.value && !container.value.contains(e.target)) {
    isOpen.value = false
  }
}

onMounted(() => document.addEventListener('click', handleClickOutside))
onBeforeUnmount(() => document.removeEventListener('click', handleClickOutside))
</script>
