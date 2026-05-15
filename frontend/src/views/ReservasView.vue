<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h2 class="text-2xl font-bold text-white">Reservas</h2>
        <p class="text-sm text-gray-500 mt-1">Gestión y control de reservas</p>
      </div>
      <BaseButton @click="openCreate">+ Nueva Reserva</BaseButton>
    </div>

    <!-- Filtros de disponibilidad -->
    <div class="bg-gray-900 border border-gray-800 rounded-xl p-4 mb-6">
      <p class="text-xs font-medium text-gray-500 uppercase tracking-wider mb-3">Consultar disponibilidad</p>
      <div class="flex flex-wrap gap-3 items-end">
        <div>
          <label class="block text-xs text-gray-400 mb-1">Fecha entrada</label>
          <input v-model="disponibilidad.entrada" type="date" class="input-field" />
        </div>
        <div>
          <label class="block text-xs text-gray-400 mb-1">Fecha salida</label>
          <input v-model="disponibilidad.salida" type="date" class="input-field" />
        </div>
        <BaseButton variant="secondary" @click="consultarDisponibilidad">Consultar</BaseButton>
      </div>
      <div v-if="habitacionesDisponibles.length" class="mt-3 flex flex-wrap gap-2">
        <span v-for="h in habitacionesDisponibles" :key="h.id" class="text-xs bg-green-900/40 text-green-300 border border-green-800 rounded-full px-3 py-1">
          Hab. {{ h.numero }} ({{ h.tipo }}) – ${{ Number(h.precio_noche).toLocaleString('es-CO') }}
        </span>
      </div>
    </div>

    <!-- Tabla de Reservas -->
    <BaseTable :columns="columns" :data="reservas" :pagination="true" :current-page="currentPage" :total-pages="totalPages" @prev="currentPage--" @next="currentPage++">
      <template #estado="{ item }">
        <span :class="estadoClass(item.estado)" class="px-2.5 py-0.5 rounded-full text-xs font-medium capitalize">{{ item.estado }}</span>
      </template>
      <template #total="{ item }">
        <span class="text-gray-300">${{ Number(item.total).toLocaleString('es-CO') }}</span>
      </template>
      <template #acciones="{ item }">
        <div class="flex gap-2">
          <button @click="openEdit(item)" class="text-xs text-hotel-gold hover:text-yellow-400 transition-colors">Editar</button>
          <button v-if="item.estado === 'confirmada'" @click="cancelar(item.id)" class="text-xs text-red-400 hover:text-red-300 transition-colors">Cancelar</button>
        </div>
      </template>
    </BaseTable>

    <!-- Modal Crear / Editar -->
    <BaseModal v-model="showModal" :title="editingItem ? 'Editar Reserva' : 'Nueva Reserva'">
      <form id="reserva-form" @submit.prevent="guardar" class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="label">Habitación</label>
            <select v-model.number="form.habitacion_id" required class="input-field w-full">
              <option value="" disabled>Seleccionar...</option>
              <option v-for="h in todasHabitaciones" :key="h.id" :value="h.id">{{ h.numero }} – {{ h.tipo }}</option>
            </select>
          </div>
          <div>
            <label class="label">Huésped (usuario_id)</label>
            <input v-model.number="form.usuario_id" type="number" required class="input-field w-full" placeholder="ID del usuario" />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="label">Fecha de entrada</label>
            <input v-model="form.fecha_entrada" type="date" required class="input-field w-full" />
          </div>
          <div>
            <label class="label">Fecha de salida</label>
            <input v-model="form.fecha_salida" type="date" required class="input-field w-full" />
          </div>
        </div>
        <div>
          <label class="label">Notas</label>
          <textarea v-model="form.notas" rows="2" class="input-field w-full" placeholder="Notas opcionales..."></textarea>
        </div>
      </form>
      <template #footer>
        <BaseButton variant="secondary" @click="showModal = false">Cancelar</BaseButton>
        <BaseButton type="submit" form="reserva-form" :disabled="saving">{{ saving ? 'Guardando...' : 'Guardar' }}</BaseButton>
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
const reservas = ref([]);
const todasHabitaciones = ref([]);
const habitacionesDisponibles = ref([]);
const showModal = ref(false);
const editingItem = ref(null);
const saving = ref(false);
const currentPage = ref(1);
const totalPages = ref(1);

const disponibilidad = ref({ entrada: '', salida: '' });
const defaultForm = { habitacion_id: '', usuario_id: '', fecha_entrada: '', fecha_salida: '', notas: '' };
const form = ref({ ...defaultForm });

const columns = [
  { key: 'id', label: '#' },
  { key: 'habitacion_id', label: 'Habitación' },
  { key: 'fecha_entrada', label: 'Entrada' },
  { key: 'fecha_salida', label: 'Salida' },
  { key: 'estado', label: 'Estado' },
  { key: 'total', label: 'Total' },
  { key: 'acciones', label: 'Acciones' },
];

async function cargarReservas() {
  try {
    const res = await api.get('/reservas');
    reservas.value = res.data.data || res.data;
    totalPages.value = Math.ceil(reservas.value.length / 10) || 1;
  } catch { toast?.value?.add('Error al cargar reservas', 'error'); }
}

async function cargarHabitaciones() {
  try {
    const res = await api.get('/habitaciones');
    todasHabitaciones.value = res.data.data || res.data;
  } catch {}
}

async function consultarDisponibilidad() {
  try {
    const res = await api.get('/habitaciones/disponibilidad', { params: { fecha_entrada: disponibilidad.value.entrada, fecha_salida: disponibilidad.value.salida } });
    habitacionesDisponibles.value = res.data.data || res.data;
  } catch { toast?.value?.add('Error al consultar disponibilidad', 'error'); }
}

function openCreate() { editingItem.value = null; form.value = { ...defaultForm }; showModal.value = true; }
function openEdit(item) { editingItem.value = item; form.value = { ...item }; showModal.value = true; }

async function guardar() {
  saving.value = true;
  try {
    if (editingItem.value) {
      await api.put(`/reservas/${editingItem.value.id}`, form.value);
      toast?.value?.add('Reserva actualizada', 'success');
    } else {
      await api.post('/reservas', form.value);
      toast?.value?.add('Reserva creada correctamente', 'success');
    }
    showModal.value = false;
    await cargarReservas();
  } catch (err) {
    toast?.value?.add(err.response?.data?.error?.message || 'Error al guardar', 'error');
  } finally { saving.value = false; }
}

async function cancelar(id) {
  if (!confirm('¿Cancelar esta reserva?')) return;
  try {
    await api.delete(`/reservas/${id}`);
    toast?.value?.add('Reserva cancelada', 'success');
    await cargarReservas();
  } catch { toast?.value?.add('Error al cancelar', 'error'); }
}

const estadoClass = (e) => ({ confirmada: 'bg-blue-900/50 text-blue-300', checkin: 'bg-green-900/50 text-green-300', checkout: 'bg-gray-700 text-gray-300', cancelada: 'bg-red-900/50 text-red-300' }[e] || 'bg-gray-800 text-gray-400');

onMounted(() => { cargarReservas(); cargarHabitaciones(); });
</script>

<style scoped>
.input-field { @apply bg-gray-800 border border-gray-700 text-gray-200 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-hotel-gold focus:ring-1 focus:ring-hotel-gold transition; }
.label { @apply block text-xs font-medium text-gray-400 mb-1; }
</style>
