<template>
  <div>
    <div class="mb-6">
      <h2 class="text-2xl font-bold text-white">Servicios Adicionales</h2>
      <p class="text-sm text-gray-500 mt-1">Comedor, Spa y más — vinculados a reservas activas</p>
    </div>

    <!-- Selector de reserva activa -->
    <div class="bg-gray-900 border border-gray-800 rounded-xl p-5 mb-6">
      <label class="label mb-2">Seleccionar reserva en curso (estado: Ocupada)</label>
      <div class="flex gap-3 flex-wrap items-center">
        <select v-model.number="reservaId" class="input-field flex-1 min-w-48" @change="cargarServicios">
          <option value="" disabled>Seleccionar reserva...</option>
          <option v-for="r in reservasOcupadas" :key="r.id" :value="r.id">
            #{{ r.id }} — Hab. {{ r.habitacion_numero || r.id_habitacion }} — {{ r.huesped_nombre || `Huésped ${r.id_huesped}` }}
          </option>
        </select>
        <span v-if="reservasOcupadas.length === 0" class="text-xs text-yellow-500">
          ⚠️ No hay reservas con check-in activo. Primero haz check-in.
        </span>
      </div>
    </div>

    <div v-if="reservaId">
      <!-- Tabs -->
      <div class="flex gap-2 mb-6 border-b border-gray-800">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          @click="activeTab = tab.key"
          :class="['px-5 py-2.5 text-sm font-medium transition-colors -mb-px border-b-2',
            activeTab === tab.key ? 'border-hotel-gold text-hotel-gold' : 'border-transparent text-gray-400 hover:text-white']"
        >{{ tab.label }}</button>
      </div>

      <!-- Formulario: Añadir servicio -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 class="text-sm font-semibold text-gray-300 mb-4">
            {{ activeTab === 'comedor' ? '🍽️ Añadir pedido al comedor' : activeTab === 'spa' ? '💆 Agendar servicio Spa' : '🧺 Añadir servicio' }}
          </h3>
          <form @submit.prevent="agregarServicio" class="space-y-4">
            <div>
              <label class="label">Descripción</label>
              <textarea
                v-model="form.descripcion"
                rows="3"
                required
                class="input-field w-full"
                :placeholder="activeTab === 'comedor'
                  ? 'Ej: Desayuno continental para 2, café negro...'
                  : activeTab === 'spa'
                  ? 'Ej: Masaje relajante 60 min, Facial...'
                  : 'Descripción del servicio'"
              ></textarea>
            </div>
            <div>
              <label class="label">Costo (COP)</label>
              <input v-model.number="form.costo" type="number" min="1" required class="input-field w-full" placeholder="45000" />
            </div>
            <BaseButton type="submit" :disabled="guardando">
              {{ guardando ? 'Guardando...' : '+ Agregar' }}
            </BaseButton>
          </form>
        </div>

        <!-- Listado de servicios de esta reserva -->
        <div class="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 class="text-sm font-semibold text-gray-300 mb-4">Servicios registrados en reserva #{{ reservaId }}</h3>
          <div v-if="serviciosFiltrados.length === 0" class="text-center text-gray-600 py-8 text-sm">
            Sin servicios de {{ activeTab }} registrados aún.
          </div>
          <div v-else class="space-y-2 max-h-72 overflow-y-auto">
            <div
              v-for="s in serviciosFiltrados"
              :key="s.id"
              class="flex items-center justify-between bg-gray-800 border border-gray-700 rounded-lg px-4 py-3"
            >
              <div>
                <p class="text-sm text-gray-200">{{ s.descripcion }}</p>
                <p class="text-xs text-gray-500 mt-0.5">{{ s.tipo }} · {{ s.fecha_hora?.split('T')[0] }}</p>
              </div>
              <div class="flex items-center gap-3">
                <span class="text-hotel-gold font-bold text-sm">${{ Number(s.costo).toLocaleString('es-CO') }}</span>
                <button v-if="canDeleteServicio" @click="eliminarServicio(s.id)" class="text-xs text-red-400 hover:text-red-300 transition-colors">✕</button>
              </div>
            </div>
          </div>
          <!-- Subtotal -->
          <div v-if="todosServicios.length > 0" class="mt-4 pt-4 border-t border-gray-700 flex justify-between text-sm">
            <span class="text-gray-400">Total servicios</span>
            <span class="text-hotel-gold font-bold">
              ${{ todosServicios.reduce((acc, s) => acc + Number(s.costo), 0).toLocaleString('es-CO') }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Estado vacío -->
    <div v-else class="text-center text-gray-600 py-16 text-sm">
      Selecciona una reserva activa (con check-in) para gestionar sus servicios.
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, inject } from 'vue';
import api from '../services/api';
import BaseButton from '../components/BaseButton.vue';
import { useAuthStore } from '../stores/auth';

const authStore = useAuthStore();
const toast = inject('toast');
const reservasOcupadas = ref([]);
const reservaId = ref('');
const todosServicios = ref([]);
const guardando = ref(false);
const activeTab = ref('comedor');

const tabs = [
  { key: 'comedor', label: '🍽️ Comedor' },
  { key: 'spa', label: '💆 Spa' },
  { key: 'lavanderia', label: '🧺 Lavandería' },
  { key: 'otro', label: '📦 Otro' },
];

// Mapa de tab key a tipo del backend
const tipoMap = {
  comedor: 'Comedor',
  spa: 'Spa',
  lavanderia: 'Lavanderia',
  otro: 'Otro',
};

const form = ref({ descripcion: '', costo: '' });
const canDeleteServicio = computed(() => authStore.userRole === 'admin');

// Filtra los servicios según el tab activo
const serviciosFiltrados = computed(() =>
  todosServicios.value.filter(s => s.tipo === tipoMap[activeTab.value])
);

async function cargarReservas() {
  try {
    const res = await api.get('/reservas/');
    const all = res.data.data || res.data;
    reservasOcupadas.value = all.filter(r => r.estado === 'Ocupada');
  } catch {}
}

async function cargarServicios() {
  if (!reservaId.value) return;
  try {
    const res = await api.get(`/reservas/${reservaId.value}/servicios`);
    const payload = res.data?.data || res.data || {};
    todosServicios.value = payload.servicios || [];
  } catch {
    todosServicios.value = [];
  }
}

async function agregarServicio() {
  if (!form.value.descripcion || !form.value.costo) return;
  guardando.value = true;
  try {
    await api.post(`/reservas/${reservaId.value}/servicios`, {
      tipo: tipoMap[activeTab.value],
      descripcion: form.value.descripcion,
      costo: form.value.costo,
    });
    toast?.value?.add('Servicio agregado correctamente', 'success');
    form.value = { descripcion: '', costo: '' };
    await cargarServicios();
  } catch (err) {
    const msg = err.response?.data?.error || err.response?.data?.mensaje || 'Error al agregar servicio';
    toast?.value?.add(msg, 'error');
  } finally { guardando.value = false; }
}

async function eliminarServicio(servicioId) {
  if (!confirm('¿Eliminar este servicio?')) return;
  try {
    await api.delete(`/servicios/${servicioId}`);
    toast?.value?.add('Servicio eliminado', 'success');
    await cargarServicios();
  } catch (err) {
    const msg = err.response?.data?.error || 'Error al eliminar';
    toast?.value?.add(msg, 'error');
  }
}

onMounted(cargarReservas);
</script>

<style scoped>
@reference "../style.css";
.input-field { @apply bg-gray-800 border border-gray-700 text-gray-200 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-hotel-gold focus:ring-1 focus:ring-hotel-gold transition; }
.label { @apply block text-xs font-medium text-gray-400 mb-1; }
</style>
