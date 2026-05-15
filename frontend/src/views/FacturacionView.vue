<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h2 class="text-2xl font-bold text-white">Facturación</h2>
        <p class="text-sm text-gray-500 mt-1">Generación y consulta de facturas</p>
      </div>
      <BaseButton @click="showGenerar = true">+ Generar Factura</BaseButton>
    </div>

    <BaseTable :columns="columns" :data="facturas" :pagination="true" :current-page="currentPage" :total-pages="totalPages" @prev="currentPage--" @next="currentPage++">
      <template #estado="{ item }">
        <span :class="estadoClass(item.estado)" class="px-2.5 py-0.5 rounded-full text-xs font-medium capitalize">{{ item.estado }}</span>
      </template>
      <template #total="{ item }">
        <span class="text-hotel-gold font-bold">${{ Number(item.total).toLocaleString('es-CO') }}</span>
      </template>
      <template #iva="{ item }">
        <span class="text-gray-400">${{ Number(item.iva).toLocaleString('es-CO') }}</span>
      </template>
      <template #acciones="{ item }">
        <a :href="`${apiBase}/facturas/${item.id}/pdf`" target="_blank" class="text-xs text-blue-400 hover:text-blue-300 transition-colors">Ver PDF</a>
      </template>
    </BaseTable>

    <!-- Modal: Generar Factura -->
    <BaseModal v-model="showGenerar" title="Generar Factura">
      <form id="factura-form" @submit.prevent="generarFactura" class="space-y-4">
        <div>
          <label class="label">ID de Reserva</label>
          <input v-model.number="facturaForm.reserva_id" type="number" required class="input-field w-full" placeholder="Número de reserva" />
        </div>
        <p class="text-xs text-gray-500">Se generará una factura con IVA del 19% calculado automáticamente sobre el total de la reserva.</p>
      </form>
      <template #footer>
        <BaseButton variant="secondary" @click="showGenerar = false">Cancelar</BaseButton>
        <BaseButton type="submit" form="factura-form" :disabled="generando">{{ generando ? 'Generando...' : 'Generar' }}</BaseButton>
      </template>
    </BaseModal>
  </div>
</template>

<script setup>
import { ref, onMounted, inject } from 'vue';
import api from '../services/api';
import BaseButton from '../components/BaseButton.vue';
import BaseTable from '../components/BaseTable.vue';
import BaseModal from '../components/BaseModal.vue';

const toast = inject('toast');
const facturas = ref([]);
const showGenerar = ref(false);
const generando = ref(false);
const currentPage = ref(1);
const totalPages = ref(1);
const apiBase = import.meta.env.VITE_API_URL;
const facturaForm = ref({ reserva_id: '' });

const columns = [
  { key: 'id', label: '#' },
  { key: 'reserva_id', label: 'Reserva' },
  { key: 'subtotal', label: 'Subtotal' },
  { key: 'iva', label: 'IVA (19%)' },
  { key: 'total', label: 'Total' },
  { key: 'estado', label: 'Estado' },
  { key: 'fecha_emision', label: 'Fecha' },
  { key: 'acciones', label: 'Acciones' },
];

async function cargar() {
  try {
    const res = await api.get('/facturas');
    facturas.value = res.data.data || res.data;
    totalPages.value = Math.ceil(facturas.value.length / 10) || 1;
  } catch { toast?.value?.add('Error al cargar facturas', 'error'); }
}

async function generarFactura() {
  generando.value = true;
  try {
    await api.post('/facturas', { reserva_id: facturaForm.value.reserva_id });
    toast?.value?.add('Factura generada correctamente', 'success');
    showGenerar.value = false;
    facturaForm.value = { reserva_id: '' };
    await cargar();
  } catch (err) {
    toast?.value?.add(err.response?.data?.error?.message || 'Error al generar factura', 'error');
  } finally { generando.value = false; }
}

const estadoClass = (e) => ({ pagada: 'bg-green-900/50 text-green-300', pendiente: 'bg-yellow-900/50 text-yellow-300', reembolsada: 'bg-purple-900/50 text-purple-300' }[e] || 'bg-gray-800 text-gray-400');
onMounted(cargar);
</script>

<style scoped>
.input-field { @apply bg-gray-800 border border-gray-700 text-gray-200 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-hotel-gold focus:ring-1 focus:ring-hotel-gold transition; }
.label { @apply block text-xs font-medium text-gray-400 mb-1; }
</style>
