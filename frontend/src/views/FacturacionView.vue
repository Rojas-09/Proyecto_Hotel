<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h2 class="text-2xl font-bold text-white">Facturación</h2>
        <p class="text-sm text-gray-500 mt-1">Emisión y consulta de facturas</p>
      </div>
    </div>

    <!-- Panel de acción rápida -->
    <div class="bg-gray-900 border border-gray-800 rounded-xl p-5 mb-6 max-w-md">
      <p class="text-xs font-medium text-gray-500 uppercase tracking-wider mb-3">Emitir factura para reserva</p>
      <div class="flex gap-3">
        <select v-model.number="reservaSeleccionada" class="input-field flex-1">
          <option value="" disabled>Seleccionar reserva completada...</option>
          <option v-for="r in reservasCompletadas" :key="r.id" :value="r.id">
            #{{ r.id }} — {{ r.huesped_nombre || `Huésped ${r.id_huesped}` }} — ${{ Number(r.total).toLocaleString('es-CO') }}
          </option>
        </select>
        <BaseButton @click="emitirFactura" :disabled="!reservaSeleccionada || emitiendo">
          {{ emitiendo ? '...' : '+ Emitir' }}
        </BaseButton>
      </div>
    </div>

    <!-- Tabla de facturas -->
    <BaseTable :columns="columns" :data="facturas" :pagination="true" :current-page="currentPage" :total-pages="totalPages" @prev="currentPage--" @next="currentPage++">
      <template #estado="{ item }">
        <span :class="estadoClass(item.estado)" class="px-2.5 py-0.5 rounded-full text-xs font-medium capitalize">{{ item.estado }}</span>
      </template>
      <template #subtotal="{ item }">
        <span class="text-gray-400">${{ Number(item.subtotal).toLocaleString('es-CO') }}</span>
      </template>
      <template #total="{ item }">
        <span class="text-hotel-gold font-bold">${{ Number(item.total).toLocaleString('es-CO') }}</span>
      </template>
      <template #acciones="{ item }">
        <div class="flex gap-2">
          <button @click="descargarPDF(item.id_reserva)" class="text-xs text-blue-400 hover:text-blue-300 transition-colors">📄 PDF</button>
          <button
            v-if="item.estado === 'emitida'"
            @click="anularFactura(item.id)"
            class="text-xs text-red-400 hover:text-red-300 transition-colors"
          >Anular</button>
        </div>
      </template>
    </BaseTable>
  </div>
</template>

<script setup>
import { ref, onMounted, inject } from 'vue';
import api from '../services/api';
import BaseButton from '../components/BaseButton.vue';
import BaseTable from '../components/BaseTable.vue';

const toast = inject('toast');
const facturas = ref([]);
const reservasCompletadas = ref([]);
const reservaSeleccionada = ref('');
const emitiendo = ref(false);
const currentPage = ref(1);
const totalPages = ref(1);

const columns = [
  { key: 'id', label: '#' },
  { key: 'id_reserva', label: 'Reserva' },
  { key: 'fecha_emision', label: 'Emisión' },
  { key: 'subtotal', label: 'Subtotal' },
  { key: 'total', label: 'Total' },
  { key: 'estado', label: 'Estado' },
  { key: 'acciones', label: 'Acciones' },
];

async function cargar() {
  try {
    const [resR] = await Promise.all([
      api.get('/reservas/'),
    ]);
    const reservas = resR.data.data || resR.data;
    reservasCompletadas.value = reservas.filter(r => r.estado === 'Completada');

    // Cargar facturas de cada reserva completada
    const facturasList = [];
    for (const r of reservasCompletadas.value) {
      try {
        const resF = await api.get(`/facturas/reserva/${r.id}`);
        if (resF.data.success && resF.data.data) {
          facturasList.push(resF.data.data);
        }
      } catch {}
    }
    facturas.value = facturasList;
    totalPages.value = Math.ceil(facturas.value.length / 10) || 1;
  } catch { toast?.value?.add('Error al cargar datos', 'error'); }
}

async function emitirFactura() {
  if (!reservaSeleccionada.value) return;
  emitiendo.value = true;
  try {
    await api.post(`/facturas/reserva/${reservaSeleccionada.value}/emitir`);
    toast?.value?.add('Factura emitida correctamente', 'success');
    reservaSeleccionada.value = '';
    await cargar();
  } catch (err) {
    const msg = err.response?.data?.mensaje || err.response?.data?.error?.message || 'Error al emitir factura';
    toast?.value?.add(msg, 'error');
  } finally { emitiendo.value = false; }
}

function descargarPDF(reservaId) {
  const token = localStorage.getItem('token');
  window.open(`${import.meta.env.VITE_API_URL}/facturas/reserva/${reservaId}/descargar?token=${token}`, '_blank');
}

async function anularFactura(facturaId) {
  if (!confirm('¿Anular esta factura?')) return;
  try {
    await api.put(`/facturas/${facturaId}/anular`, { motivo: 'Anulada desde administración' });
    toast?.value?.add('Factura anulada', 'success');
    await cargar();
  } catch (err) {
    toast?.value?.add(err.response?.data?.mensaje || 'Error al anular', 'error');
  }
}

const estadoClass = (e) => ({
  emitida: 'bg-blue-900/50 text-blue-300',
  pendiente: 'bg-yellow-900/50 text-yellow-300',
  pagada: 'bg-green-900/50 text-green-300',
  anulada: 'bg-red-900/50 text-red-300'
}[e] || 'bg-gray-800 text-gray-400');

onMounted(cargar);
</script>

<style scoped>
@reference "../style.css";
.input-field { @apply bg-gray-800 border border-gray-700 text-gray-200 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-hotel-gold focus:ring-1 focus:ring-hotel-gold transition; }
.label { @apply block text-xs font-medium text-gray-400 mb-1; }
</style>
