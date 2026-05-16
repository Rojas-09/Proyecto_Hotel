<template>
  <div>
    <div class="mb-6">
      <h2 class="text-2xl font-bold text-white">Reportes Estratégicos</h2>
      <p class="text-sm text-gray-500 mt-1">Análisis de ocupación e ingresos</p>
    </div>

    <!-- Filtros de fecha -->
    <div class="bg-gray-900 border border-gray-800 rounded-xl p-5 mb-6 flex flex-wrap gap-4 items-end">
      <div>
        <label class="label">Fecha inicio</label>
        <input v-model="filtros.fecha_inicio" type="date" class="input-field" />
      </div>
      <div>
        <label class="label">Fecha fin</label>
        <input v-model="filtros.fecha_fin" type="date" class="input-field" />
      </div>
      <BaseButton @click="cargarReportes">Generar</BaseButton>
      <div class="ml-auto flex gap-2">
        <a :href="exportUrl('excel')" class="inline-flex items-center gap-1 px-3 py-2 text-xs font-medium bg-green-900/40 text-green-300 border border-green-800 rounded-lg hover:bg-green-900/60 transition-colors">📊 Excel</a>
        <a :href="exportUrl('pdf')" class="inline-flex items-center gap-1 px-3 py-2 text-xs font-medium bg-red-900/40 text-red-300 border border-red-800 rounded-lg hover:bg-red-900/60 transition-colors">📄 PDF</a>
      </div>
    </div>

    <!-- KPIs -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
      <div v-for="kpi in kpis" :key="kpi.label" class="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <p class="text-sm text-gray-500 mb-1">{{ kpi.label }}</p>
        <p class="text-2xl font-bold" :class="kpi.color">{{ kpi.value }}</p>
        <p class="text-xs text-gray-600 mt-1">{{ kpi.sub }}</p>
      </div>
    </div>

    <!-- Tabla de ocupación -->
    <div class="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-800">
        <h3 class="font-semibold text-gray-200">Detalle por habitación</h3>
      </div>
      <BaseTable :columns="columnasOcupacion" :data="datosOcupacion" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, inject } from 'vue';
import api from '../services/api';
import BaseButton from '../components/BaseButton.vue';
import BaseTable from '../components/BaseTable.vue';

const toast = inject('toast');
const apiBase = import.meta.env.VITE_API_URL;
const reporteOcupacion = ref(null);
const reporteIngresos = ref(null);
const datosOcupacion = ref([]);

const today = new Date();
const firstOfMonth = new Date(today.getFullYear(), today.getMonth(), 1).toISOString().split('T')[0];
const todayStr = today.toISOString().split('T')[0];

const filtros = ref({ fecha_inicio: firstOfMonth, fecha_fin: todayStr });

const columnasOcupacion = [
  { key: 'numero', label: 'Habitación' },
  { key: 'tipo', label: 'Tipo' },
  { key: 'noches_ocupadas', label: 'Noches Ocupadas' },
  { key: 'ingresos', label: 'Ingresos' },
  { key: 'ocupacion_pct', label: '% Ocupación' },
];

const kpis = computed(() => [
  {
    label: 'Ocupación promedio',
    value: reporteOcupacion.value ? `${reporteOcupacion.value.porcentaje_ocupacion ?? 0}%` : '—',
    color: 'text-hotel-gold',
    sub: 'Del período seleccionado'
  },
  {
    label: 'Total ingresos',
    value: reporteIngresos.value ? `$${Number(reporteIngresos.value.total_ingresos ?? 0).toLocaleString('es-CO')}` : '—',
    color: 'text-green-400',
    sub: 'Ingresos facturados'
  },
  {
    label: 'Reservas activas',
    value: reporteOcupacion.value?.total_reservas ?? '—',
    color: 'text-blue-400',
    sub: 'En el período'
  },
  {
    label: 'Habitaciones disponibles',
    value: reporteOcupacion.value?.habitaciones_disponibles ?? '—',
    color: 'text-gray-300',
    sub: 'Actualmente libres'
  },
]);

function exportUrl(formato) {
  const params = new URLSearchParams({ fecha_inicio: filtros.value.fecha_inicio, fecha_fin: filtros.value.fecha_fin });
  const token = localStorage.getItem('token');
  return `${apiBase}/reportes/ocupacion/${formato}?${params}&token=${token}`;
}

async function cargarReportes() {
  const params = { params: filtros.value };
  try {
    const [resOcup, resIng] = await Promise.all([
      api.get('/reportes/ocupacion', params),
      api.get('/reportes/ingresos', params)
    ]);
    reporteOcupacion.value = resOcup.data.data || resOcup.data;
    reporteIngresos.value = resIng.data.data || resIng.data;
    datosOcupacion.value = reporteOcupacion.value?.detalle || [];
  } catch (err) {
    toast?.value?.add('Error al cargar reportes', 'error');
  }
}

onMounted(cargarReportes);
</script>

<style scoped>
@reference "../style.css";
.input-field { @apply bg-gray-800 border border-gray-700 text-gray-200 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-hotel-gold focus:ring-1 focus:ring-hotel-gold transition; }
.label { @apply block text-xs font-medium text-gray-400 mb-1; }
</style>
