<template>
  <div>
    <!-- Encabezado con acciones -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h2 class="text-2xl font-bold text-white">Habitaciones</h2>
        <p class="text-sm text-gray-500 mt-1">Gestión de habitaciones del hotel</p>
      </div>
      <BaseButton v-if="canEdit" @click="openCreate">+ Nueva Habitación</BaseButton>
    </div>

    <!-- Filtros -->
    <div class="bg-gray-900 border border-gray-800 rounded-xl p-4 mb-6 flex flex-wrap gap-3">
      <select v-model="filtroEstado" class="bg-gray-800 border border-gray-700 text-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-hotel-gold">
        <option value="">Todos los estados</option>
        <option value="Disponible">Disponible</option>
        <option value="Ocupada">Ocupada</option>
        <option value="Mantenimiento">Mantenimiento</option>
      </select>
      <select v-model="filtroTipo" class="bg-gray-800 border border-gray-700 text-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-hotel-gold">
        <option value="">Todos los tipos</option>
        <option value="Simple">Simple</option>
        <option value="Doble">Doble</option>
        <option value="Suite">Suite</option>
        <option value="Deluxe">Deluxe</option>
      </select>
      <button @click="cargarHabitaciones" class="ml-auto text-xs text-gray-400 hover:text-white transition-colors">↻ Actualizar</button>
    </div>

    <!-- Tabla -->
    <BaseTable :columns="columns" :data="habitacionesFiltradas" :pagination="true" :current-page="currentPage" :total-pages="totalPages" @prev="currentPage--" @next="currentPage++">
      <template #numero="{ item }">
        <span class="font-mono font-bold text-hotel-gold">{{ item.numero }}</span>
      </template>
      <template #tipo="{ item }">
        <span :class="tipoClass(item.tipo)" class="inline-flex px-2 py-0.5 rounded-full text-xs font-medium capitalize">
          {{ item.tipo }}
        </span>
      </template>
      <template #estado="{ item }">
        <span :class="estadoClass(item.estado)" class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium">
          <span class="w-1.5 h-1.5 rounded-full" :class="estadoDot(item.estado)"></span>
          {{ item.estado }}
        </span>
      </template>
      <template #precio_noche="{ item }">
        <span class="text-gray-300">${{ Number(item.precio_noche).toLocaleString('es-CO') }}</span>
      </template>
      <template #acciones="{ item }">
        <div class="flex gap-2">
          <button @click="openEdit(item)" class="text-xs text-hotel-gold hover:text-yellow-400 transition-colors">Editar</button>
          <button v-if="authStore.userRole === 'admin'" @click="eliminar(item.id)" class="text-xs text-red-400 hover:text-red-300 transition-colors">Eliminar</button>
        </div>
      </template>
    </BaseTable>

    <BaseModal v-model="showModal" :title="editingItem ? 'Editar Habitación' : 'Nueva Habitación'">
      <form id="habitacion-form" @submit.prevent="guardar" class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-xs font-medium text-gray-400 mb-1">Número</label>
            <input v-model="form.numero" required class="input-field w-full" placeholder="101" />
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-400 mb-1">Piso</label>
            <input v-model.number="form.piso" type="number" required class="input-field w-full" placeholder="1" />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-4">
        <div>
            <label class="block text-xs font-medium text-gray-400 mb-1">Tipo</label>
            <select v-model="form.tipo" required class="input-field w-full">
              <option value="Simple">Simple</option>
              <option value="Doble">Doble</option>
              <option value="Suite">Suite</option>
              <option value="Deluxe">Deluxe</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-400 mb-1">Capacidad</label>
            <input v-model.number="form.capacidad" type="number" required class="input-field w-full" placeholder="2" />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-xs font-medium text-gray-400 mb-1">Precio/Noche (COP)</label>
            <input v-model.number="form.precio_noche" type="number" required class="input-field w-full" placeholder="150000" />
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-400 mb-1">Estado</label>
            <select v-model="form.estado" class="input-field w-full">
              <option value="Disponible">Disponible</option>
              <option value="Ocupada">Ocupada</option>
              <option value="Mantenimiento">Mantenimiento</option>
            </select>
          </div>
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-400 mb-1">Descripción</label>
          <textarea v-model="form.descripcion" rows="2" class="input-field w-full" placeholder="Descripción de la habitación..."></textarea>
        </div>
      </form>
      <template #footer>
        <BaseButton variant="secondary" @click="showModal = false">Cancelar</BaseButton>
        <BaseButton type="submit" form="habitacion-form" :disabled="saving">{{ saving ? 'Guardando...' : 'Guardar' }}</BaseButton>
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

const authStore = useAuthStore();
const toast = inject('toast');
const canEdit = computed(() => ['admin', 'recepcionista'].includes(authStore.userRole));

const habitaciones = ref([]);
const filtroEstado = ref('');
const filtroTipo = ref('');
const showModal = ref(false);
const editingItem = ref(null);
const saving = ref(false);
const currentPage = ref(1);
const totalPages = ref(1);
const ITEMS_PER_PAGE = 10;

const defaultForm = { numero: '', piso: 1, tipo: 'Simple', capacidad: 2, precio_noche: '', estado: 'Disponible', descripcion: '' };
const form = ref({ ...defaultForm });

const columns = [
  { key: 'numero', label: 'Número' },
  { key: 'tipo', label: 'Tipo' },
  { key: 'piso', label: 'Piso' },
  { key: 'capacidad', label: 'Capacidad' },
  { key: 'precio_noche', label: 'Precio/Noche' },
  { key: 'estado', label: 'Estado' },
  { key: 'acciones', label: 'Acciones' },
];

const habitacionesFiltradas = computed(() => {
  let result = habitaciones.value;
  if (filtroEstado.value) result = result.filter(h => h.estado === filtroEstado.value);
  if (filtroTipo.value) result = result.filter(h => h.tipo === filtroTipo.value);
  totalPages.value = Math.ceil(result.length / ITEMS_PER_PAGE) || 1;
  const start = (currentPage.value - 1) * ITEMS_PER_PAGE;
  return result.slice(start, start + ITEMS_PER_PAGE);
});

async function cargarHabitaciones() {
  try {
    const res = await api.get('/habitaciones/');
    habitaciones.value = res.data.data || res.data;
  } catch {
    toast?.value?.add('Error al cargar habitaciones', 'error');
  }
}

function openCreate() {
  editingItem.value = null;
  form.value = { ...defaultForm };
  showModal.value = true;
}

function openEdit(item) {
  editingItem.value = item;
  form.value = { ...item };
  showModal.value = true;
}

async function guardar() {
  saving.value = true;
  try {
    if (editingItem.value) {
      await api.put(`/habitaciones/${editingItem.value.id}`, form.value);
      toast?.value?.add('Habitación actualizada correctamente', 'success');
    } else {
      await api.post('/habitaciones/', form.value);
      toast?.value?.add('Habitación creada correctamente', 'success');
    }
    showModal.value = false;
    await cargarHabitaciones();
  } catch (err) {
    toast?.value?.add(err.response?.data?.error?.message || 'Error al guardar', 'error');
  } finally {
    saving.value = false;
  }
}

async function eliminar(id) {
  if (!confirm('¿Eliminar esta habitación?')) return;
  try {
    await api.delete(`/habitaciones/${id}`);
    toast?.value?.add('Habitación eliminada', 'success');
    await cargarHabitaciones();
  } catch {
    toast?.value?.add('Error al eliminar', 'error');
  }
}

const tipoClass = (tipo) => ({
  Simple: 'bg-blue-900/50 text-blue-300',
  Doble: 'bg-indigo-900/50 text-indigo-300',
  Suite: 'bg-hotel-gold/20 text-hotel-gold',
  Deluxe: 'bg-purple-900/50 text-purple-300'
}[tipo] || 'bg-gray-800 text-gray-400');
const estadoClass = (estado) => ({
  Disponible: 'bg-green-900/50 text-green-300',
  Ocupada: 'bg-red-900/50 text-red-300',
  Mantenimiento: 'bg-yellow-900/50 text-yellow-300'
}[estado] || 'bg-gray-800 text-gray-400');
const estadoDot = (estado) => ({
  Disponible: 'bg-green-400',
  Ocupada: 'bg-red-400',
  Mantenimiento: 'bg-yellow-400'
}[estado] || 'bg-gray-500');

onMounted(cargarHabitaciones);
</script>

<style scoped>
@reference "../style.css";
.input-field { @apply bg-gray-800 border border-gray-700 text-gray-200 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-hotel-gold focus:ring-1 focus:ring-hotel-gold transition; }
.label { @apply block text-xs font-medium text-gray-400 mb-1; }
</style>
