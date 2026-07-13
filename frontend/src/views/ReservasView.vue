<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h2 class="text-2xl font-bold text-white">Reservas</h2>
        <p class="text-sm text-gray-500 mt-1">Gestión y control de reservas</p>
      </div>
      <BaseButton @click="openCreate" :disabled="loading">+ Nueva Reserva</BaseButton>
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
        <span
          v-for="h in habitacionesDisponibles" :key="h.id"
          @click="form.id_habitacion = h.id"
          class="cursor-pointer text-xs bg-green-900/40 text-green-300 border border-green-800 rounded-full px-3 py-1 hover:bg-green-900/70 transition-colors"
        >
          ✓ Hab. {{ h.numero }} ({{ h.tipo }}) – ${{ Number(h.precio_noche).toLocaleString('es-CO') }}
        </span>
      </div>
    </div>

    <!-- Tabla de Reservas -->
    <BaseTable :columns="columns" :data="reservasPaginadas" :pagination="true" :current-page="currentPage" :total-pages="totalPages" @prev="paginaAnterior" @next="paginaSiguiente">
      <template #estado="{ item }">
        <span :class="estadoClass(item.estado)" class="px-2.5 py-0.5 rounded-full text-xs font-medium capitalize">{{ item.estado }}</span>
      </template>
      <template #habitacion="{ item }">
        <span class="text-gray-300">{{ item.habitacion_numero || item.id_habitacion }}</span>
      </template>
      <template #huesped="{ item }">
        <span class="text-gray-300 text-xs">{{ item.huesped_nombre || `ID: ${item.id_huesped}` }}</span>
      </template>
      <template #total="{ item }">
        <span class="text-hotel-gold font-medium">${{ Number(item.total).toLocaleString('es-CO') }}</span>
      </template>
      <template #acciones="{ item }">
        <div class="flex gap-2 flex-wrap">
          <button v-if="['Pendiente'].includes(item.estado)" @click="confirmarReserva(item.id)" class="text-xs text-green-400 hover:text-green-300 transition-colors">Confirmar</button>
          <button v-if="['Confirmada', 'Pendiente'].includes(item.estado)" @click="openEdit(item)" class="text-xs text-hotel-gold hover:text-yellow-400 transition-colors">Editar</button>
          <button v-if="['Pendiente', 'Confirmada'].includes(item.estado)" @click="cancelar(item.id)" class="text-xs text-red-400 hover:text-red-300 transition-colors">Cancelar</button>
          <button v-if="canDelete && item.estado === 'Pendiente'" @click="confirmarEliminarReserva(item)" class="text-xs text-red-600 hover:text-red-500 transition-colors">Eliminar</button>
        </div>
      </template>
    </BaseTable>

    <!-- Modal Confirmar Eliminación -->
    <BaseConfirmModal
      v-model="showDeleteConfirm"
      message="¿Eliminar esta reserva? Se borrará permanentemente."
      confirmText="Eliminar reserva"
      variant="danger"
      :loading="deleting"
      @confirm="eliminarReserva"
    />
    <!-- Modal Confirmar Cancelación -->
    <BaseConfirmModal
      v-model="showCancelConfirm"
      message="¿Cancelar esta reserva? Se cambiará el estado a cancelada."
      confirmText="Sí, cancelar reserva"
      variant="danger"
      @confirm="ejecutarCancelacion"
    />

    <!-- Modal Crear / Editar -->
    <BaseModal v-model="showModal" :title="editingItem ? 'Editar Reserva' : 'Nueva Reserva'">
      <form id="reserva-form" @submit.prevent="guardar" class="space-y-4">
        <!-- PASO 1: Fechas (obligatorio antes de buscar habitaciones) -->
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="label">Fecha de entrada <span class="text-red-400">*</span></label>
            <input v-model="form.fecha_entrada" type="date" required class="input-field w-full" @change="validarFechas" :min="hoy" />
          </div>
          <div>
            <label class="label">Fecha de salida <span class="text-red-400">*</span></label>
            <input v-model="form.fecha_salida" type="date" required class="input-field w-full" @change="validarFechas" :min="manana" />
          </div>
        </div>

        <!-- PASO 2: Botón consultar disponibilidad -->
        <div v-if="!editingItem" class="flex justify-center">
          <BaseButton 
            variant="secondary" 
            type="button" 
            @click="buscarHabitacionesDisponibles"
            :disabled="!form.fecha_entrada || !form.fecha_salida || buscandoHabitaciones"
            class="w-full max-w-md"
          >
            {{ buscandoHabitaciones ? 'Buscando...' : '🔍 Consultar habitaciones disponibles' }}
          </BaseButton>
        </div>

        <!-- Mensaje si no hay fechas o no hay resultados -->
        <p v-if="!editingItem && (!form.fecha_entrada || !form.fecha_salida)" class="text-center text-gray-500 text-sm">
          Primero selecciona las fechas y pulsa "Consultar habitaciones disponibles"
        </p>
        <p v-if="!editingItem && habitacionesParaModal.length === 0 && !buscandoHabitaciones && form.fecha_entrada && form.fecha_salida" class="text-center text-red-400 text-sm">
          No hay habitaciones disponibles para esas fechas. Cambia las fechas e inténtalo de nuevo.
        </p>

        <!-- PASO 3: Habitación (solo las disponibles para las fechas seleccionadas) -->
        <div v-if="editingItem || habitacionesParaModal.length > 0">
          <label class="label">Habitación <span class="text-red-400">*</span></label>
          <SearchSelect
            v-model="form.id_habitacion"
            :options="habitacionesParaModal.map(h => ({ value: h.id, label: h.numero + ' – ' + h.tipo + ' — $' + Number(h.precio_noche).toLocaleString('es-CO') }))"
            placeholder="Seleccionar..."
            :disabled="!habitacionesParaModal.length"
          />
        </div>

        <!-- PASO 4: Huésped -->
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="label">Huésped <span class="text-red-400">*</span></label>
            <SearchSelect
              v-model="form.id_huesped"
              :options="huespedes.map(h => ({ value: h.id, label: h.nombre + ' ' + h.apellido + ' — ' + h.documento_id }))"
              placeholder="Seleccionar..."
            />
          </div>
        </div>

        <div>
          <label class="label">Notas</label>
          <textarea v-model="form.notas" rows="2" class="input-field w-full" placeholder="Notas opcionales..."></textarea>
        </div>
      </form>
      <template #footer>
        <BaseButton variant="secondary" @click="cerrarModal">Cancelar</BaseButton>
        <BaseButton type="submit" form="reserva-form" :disabled="saving || !habitacionesParaModal.length">{{ saving ? 'Guardando...' : 'Guardar' }}</BaseButton>
      </template>
    </BaseModal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, inject } from 'vue';
import { useAuthStore } from '../stores/auth';
import api from '../services/api';
import BaseButton from '../components/BaseButton.vue';
import BaseTable from '../components/BaseTable.vue';
import BaseModal from '../components/BaseModal.vue';
import BaseConfirmModal from '../components/BaseConfirmModal.vue';
import SearchSelect from '../components/SearchSelect.vue';

const authStore = useAuthStore();
const toast = inject('toast');
const reservas = ref([]);
const todasHabitaciones = ref([]);
const huespedes = ref([]);
const habitacionesDisponibles = ref([]);
const showModal = ref(false);
const editingItem = ref(null);
const saving = ref(false);
const currentPage = ref(1);
const ITEMS_PER_PAGE = 10;

const disponibilidad = ref({ entrada: '', salida: '' });
const showDeleteConfirm = ref(false);
const showCancelConfirm = ref(false);
const reservaAEliminar = ref(null);
const reservaACancelar = ref(null);
const deleting = ref(false);
const loading = ref(true);
const habitacionesParaModal = ref([]);

const buscandoHabitaciones = ref(false);

const hoy = computed(() => new Date().toISOString().split('T')[0]);
const manana = computed(() => {
  const d = new Date();
  d.setDate(d.getDate() + 1);
  return d.toISOString().split('T')[0];
});

const defaultForm = { id_habitacion: '', id_huesped: '', fecha_entrada: '', fecha_salida: '', notas: '' };
const form = ref({ ...defaultForm });

const canDelete = computed(() => authStore.userRole === 'admin');

const columns = [
  { key: 'id', label: '#' },
  { key: 'habitacion', label: 'Habitación' },
  { key: 'huesped', label: 'Huésped' },
  { key: 'fecha_entrada', label: 'Entrada' },
  { key: 'fecha_salida', label: 'Salida' },
  { key: 'noches', label: 'Noches' },
  { key: 'estado', label: 'Estado' },
  { key: 'total', label: 'Total' },
  { key: 'acciones', label: 'Acciones' },
];

const totalPages = computed(() => Math.max(1, Math.ceil(reservas.value.length / ITEMS_PER_PAGE)));

const reservasPaginadas = computed(() => {
  const start = (currentPage.value - 1) * ITEMS_PER_PAGE;
  return reservas.value.slice(start, start + ITEMS_PER_PAGE);
});

function paginaAnterior() {
  currentPage.value = Math.max(1, currentPage.value - 1);
}

function paginaSiguiente() {
  currentPage.value = Math.min(totalPages.value, currentPage.value + 1);
}

async function cargarReservas() {
  try {
    const res = await api.get('/reservas/');
    reservas.value = res.data.data || res.data;
    currentPage.value = Math.min(currentPage.value, totalPages.value);
  } catch { toast?.value?.add('Error al cargar reservas', 'error'); }
}

async function cargarHabitaciones() {
  try {
    const res = await api.get('/habitaciones/');
    todasHabitaciones.value = res.data.data || res.data;
  } catch {}
}

async function cargarHuespedes() {
  try {
    const res = await api.get('/huespedes/');
    huespedes.value = res.data.data || res.data;
  } catch {}
}

async function consultarDisponibilidad() {
  if (!disponibilidad.value.entrada || !disponibilidad.value.salida) {
    toast?.value?.add('Selecciona las fechas de entrada y salida', 'error');
    return;
  }
  try {
    const res = await api.get('/habitaciones/disponibles', {
      params: { fecha_entrada: disponibilidad.value.entrada, fecha_salida: disponibilidad.value.salida }
    });
    habitacionesDisponibles.value = res.data.data || res.data;
    if (!habitacionesDisponibles.value.length) toast?.value?.add('No hay habitaciones disponibles en esas fechas', 'error');
  } catch { toast?.value?.add('Error al consultar disponibilidad', 'error'); }
}

function validarFechas() {
  if (form.value.fecha_entrada && form.value.fecha_salida && new Date(form.value.fecha_entrada) >= new Date(form.value.fecha_salida)) {
    form.value.fecha_salida = '';
    toast?.value?.add('La fecha de salida debe ser posterior a la de entrada', 'error');
  }
}

function openCreate() { 
  editingItem.value = null; 
  form.value = { ...defaultForm }; 
  habitacionesParaModal.value = []; 
  showModal.value = true; 
}

async function openEdit(item) {
  editingItem.value = item;
  form.value = {
    id_habitacion: item.id_habitacion,
    id_huesped: item.id_huesped,
    fecha_entrada: item.fecha_entrada,
    fecha_salida: item.fecha_salida,
    notas: item.notas || ''
  };
  // En edición, cargar habitaciones disponibles para esas fechas (incluyendo la actual)
  try {
    const res = await api.get('/habitaciones/disponibles', {
      params: { fecha_entrada: item.fecha_entrada, fecha_salida: item.fecha_salida }
    });
    const disponibles = res.data.data || res.data;
    // Incluir la habitación actual aunque no esté "disponible" en el resultado
    const actual = todasHabitaciones.value.find(h => h.id === item.id_habitacion);
    habitacionesParaModal.value = actual ? [...disponibles, actual] : disponibles;
  } catch {
    habitacionesParaModal.value = [];
  }
  showModal.value = true;
}

function cerrarModal() {
  showModal.value = false;
  editingItem.value = null;
  form.value = { ...defaultForm };
  habitacionesParaModal.value = [];
}

async function buscarHabitacionesDisponibles() {
  if (!form.value.fecha_entrada || !form.value.fecha_salida) {
    toast?.value?.add('Selecciona las fechas de entrada y salida', 'error');
    return;
  }
  if (new Date(form.value.fecha_entrada) >= new Date(form.value.fecha_salida)) {
    toast?.value?.add('La fecha de salida debe ser posterior a la de entrada', 'error');
    return;
  }
  buscandoHabitaciones.value = true;
  try {
    const res = await api.get('/habitaciones/disponibles', {
      params: { fecha_entrada: form.value.fecha_entrada, fecha_salida: form.value.fecha_salida }
    });
    habitacionesParaModal.value = res.data.data || res.data;
    if (!habitacionesParaModal.value.length) {
      toast?.value?.add('No hay habitaciones disponibles para esas fechas', 'error');
    }
  } catch {
    toast?.value?.add('Error al buscar habitaciones', 'error');
    habitacionesParaModal.value = [];
  } finally {
    buscandoHabitaciones.value = false;
  }
}



async function guardar() {
  if (!habitacionesParaModal.value.length) {
    toast?.value?.add('Primero consulta habitaciones disponibles', 'error');
    return;
  }
  saving.value = true;
  try {
    const datos = { ...form.value };
    delete datos.notas;
    if (editingItem.value) {
      await api.patch(`/reservas/${editingItem.value.id}`, datos);
      toast?.value?.add('Reserva actualizada', 'success');
    } else {
      await api.post('/reservas/', datos);
      toast?.value?.add('Reserva creada correctamente', 'success');
    }
    showModal.value = false;
    await cargarReservas();
  } catch (err) {
    const msg = err.response?.data?.error?.message || err.response?.data?.mensaje || 'Error al guardar';
    toast?.value?.add(msg, 'error');
  } finally { saving.value = false; }
}

async function confirmarReserva(id) {
  try {
    await api.post(`/pagos/garantia/${id}`, { metodo: 'Efectivo' });
    toast?.value?.add('Reserva confirmada (Garantía pagada)', 'success');
    await cargarReservas();
  } catch (err) {
    const msg = err.response?.data?.error || err.response?.data?.mensaje || 'Error al confirmar';
    toast?.value?.add(msg, 'error');
  }
}

async function cancelar(id) {
  reservaACancelar.value = id;
  showCancelConfirm.value = true;
}

async function ejecutarCancelacion() {
  if (!reservaACancelar.value) return;
  try {
    await api.put(`/reservas/${reservaACancelar.value}/cancelar`);
    toast?.value?.add('Reserva cancelada', 'success');
    showCancelConfirm.value = false;
    await cargarReservas();
  } catch (err) {
    const msg = err.response?.data?.mensaje || 'Error al cancelar';
    toast?.value?.add(msg, 'error');
  }
}

function confirmarEliminarReserva(item) {
  reservaAEliminar.value = item;
  showDeleteConfirm.value = true;
}

async function eliminarReserva() {
  if (!reservaAEliminar.value) return;
  deleting.value = true;
  try {
    await api.delete(`/reservas/${reservaAEliminar.value.id}`);
    toast?.value?.add('Reserva eliminada correctamente', 'success');
    showDeleteConfirm.value = false;
    await cargarReservas();
  } catch (err) {
    const msg = err.response?.data?.mensaje || 'Error al eliminar';
    toast?.value?.add(msg, 'error');
  } finally { deleting.value = false; }
}







const estadoClass = (e) => ({
  Confirmada: 'bg-blue-900/50 text-blue-300',
  Pendiente: 'bg-yellow-900/50 text-yellow-300',
  Ocupada: 'bg-green-900/50 text-green-300',
  Completada: 'bg-gray-700 text-gray-300',
  Cancelada: 'bg-red-900/50 text-red-300'
}[e] || 'bg-gray-800 text-gray-400');

async function cargarTodo() {
  loading.value = true;
  await Promise.all([cargarReservas(), cargarHabitaciones(), cargarHuespedes()]);
  loading.value = false;
}

onMounted(cargarTodo);
</script>

<style scoped>
@reference "../style.css";
.input-field { @apply bg-gray-800 border border-gray-700 text-gray-200 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-hotel-gold focus:ring-1 focus:ring-hotel-gold transition; }
.label { @apply block text-xs font-medium text-gray-400 mb-1; }
</style>
