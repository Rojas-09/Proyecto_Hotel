<template>
  <div>
    <div class="mb-8">
      <h2 class="text-2xl font-bold text-white">Bienvenido, {{ authStore.user?.nombre }}</h2>
      <p class="text-sm text-gray-500 mt-1">Panel de huésped</p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
      <div class="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <p class="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">Puntos de fidelidad</p>
        <p class="text-3xl font-bold text-hotel-gold">{{ authStore.user?.puntos_fidelizacion || 0 }}</p>
      </div>
      <div class="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <p class="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">Reservas activas</p>
        <p class="text-3xl font-bold text-white">{{ reservasActivas.length }}</p>
      </div>
      <div class="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <p class="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">Total reservas</p>
        <p class="text-3xl font-bold text-white">{{ reservas.length }}</p>
      </div>
    </div>

    <div class="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <h3 class="text-lg font-semibold text-white mb-4">Mis Reservas</h3>
      <div v-if="loading" class="text-gray-400 text-sm py-8 text-center">Cargando...</div>
      <div v-else-if="reservas.length === 0" class="text-gray-500 text-sm py-8 text-center">
        No tienes reservas registradas.
      </div>
      <div v-else class="space-y-3">
        <div
          v-for="r in reservas" :key="r.id"
          class="flex items-center justify-between bg-gray-800/50 rounded-lg p-4"
        >
          <div class="flex-1">
            <div class="flex items-center gap-3">
              <span class="font-medium text-white">#{{ r.id }}</span>
              <span :class="estadoClass(r.estado)" class="px-2.5 py-0.5 rounded-full text-xs font-medium capitalize">{{ r.estado }}</span>
            </div>
            <p class="text-xs text-gray-400 mt-1">
              Hab. {{ r.habitacion_numero }} ({{ r.habitacion_tipo }}) —
              {{ formatDate(r.fecha_entrada) }} → {{ formatDate(r.fecha_salida) }} —
              <span class="text-hotel-gold">${{ Number(r.total).toLocaleString('es-CO') }}</span>
            </p>
          </div>
          <a
            v-if="r.estado === 'Completada'"
            @click.prevent="descargarFactura(r.id)"
            href="#"
            class="text-xs text-blue-400 hover:text-blue-300 transition-colors ml-4"
          >📄 Factura</a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, inject } from 'vue';
import { useAuthStore } from '../stores/auth';
import api from '../services/api';

const authStore = useAuthStore();
const toast = inject('toast');
const loading = ref(false);
const reservas = ref([]);

const reservasActivas = computed(() =>
  reservas.value.filter(r => !['Completada', 'Cancelada', 'No show'].includes(r.estado))
);

function formatDate(iso) {
  if (!iso) return '';
  return new Date(iso).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' });
}

function estadoClass(e) {
  return {
    Pendiente: 'bg-yellow-900/50 text-yellow-300',
    Confirmada: 'bg-green-900/50 text-green-300',
    Completada: 'bg-blue-900/50 text-blue-300',
    Cancelada: 'bg-red-900/50 text-red-300',
    'No show': 'bg-gray-700 text-gray-400',
  }[e] || 'bg-gray-800 text-gray-400';
}

async function cargarReservas() {
  loading.value = true;
  try {
    const res = await api.get('/reservas/mis-reservas');
    reservas.value = res.data.data || [];
  } catch {
    toast?.value?.add('Error al cargar reservas', 'error');
  } finally {
    loading.value = false;
  }
}

async function descargarFactura(reservaId) {
  try {
    const response = await api.get(`/facturas/reserva/${reservaId}/descargar`, {
      responseType: 'blob'
    });
    const header = response.headers?.['content-disposition'] || '';
    const filename = header.match(/filename="?([^"]+)"?/)?.[1] || `factura-${reservaId}.pdf`;
    const blobUrl = URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
    const link = document.createElement('a');
    link.href = blobUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(blobUrl);
  } catch {
    toast?.value?.add('No hay factura disponible para esta reserva', 'error');
  }
}

onMounted(cargarReservas);
</script>
