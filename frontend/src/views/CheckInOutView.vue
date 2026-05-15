<template>
  <div>
    <div class="mb-6">
      <h2 class="text-2xl font-bold text-white">Recepción</h2>
      <p class="text-sm text-gray-500 mt-1">Gestión de Check-in y Check-out</p>
    </div>

    <!-- Tabs -->
    <div class="flex gap-2 mb-6 border-b border-gray-800">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        @click="activeTab = tab.key"
        :class="['px-5 py-2.5 text-sm font-medium transition-colors -mb-px border-b-2', activeTab === tab.key ? 'border-hotel-gold text-hotel-gold' : 'border-transparent text-gray-400 hover:text-white']"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- CHECK-IN -->
    <div v-if="activeTab === 'checkin'">
      <div class="bg-gray-900 border border-gray-800 rounded-xl p-6 max-w-lg">
        <h3 class="text-base font-semibold text-gray-200 mb-4">Registrar Check-in</h3>
        <form @submit.prevent="hacerCheckin" class="space-y-4">
          <div>
            <label class="label">ID de Reserva</label>
            <input v-model.number="checkinForm.reserva_id" type="number" required class="input-field w-full" placeholder="Número de reserva" />
          </div>
          <div>
            <label class="label">Notas de entrada</label>
            <textarea v-model="checkinForm.notas" rows="2" class="input-field w-full" placeholder="Observaciones del check-in..."></textarea>
          </div>
          <BaseButton type="submit" :disabled="procesando">{{ procesando ? 'Procesando...' : '✓ Confirmar Check-in' }}</BaseButton>
        </form>
        <!-- Reservas pendientes de check-in -->
        <div class="mt-6">
          <p class="text-xs font-medium text-gray-500 uppercase tracking-wider mb-3">Reservas pendientes de check-in</p>
          <div class="space-y-2 max-h-60 overflow-y-auto">
            <div v-for="r in reservasConfirmadas" :key="r.id"
              @click="checkinForm.reserva_id = r.id"
              class="cursor-pointer bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-lg p-3 transition-colors"
            >
              <div class="flex justify-between items-start">
                <div>
                  <p class="text-sm font-medium text-gray-200">Reserva #{{ r.id }} — Hab. {{ r.habitacion_id }}</p>
                  <p class="text-xs text-gray-500">{{ r.fecha_entrada }} → {{ r.fecha_salida }}</p>
                </div>
                <span class="text-xs bg-blue-900/50 text-blue-300 px-2 py-0.5 rounded-full">confirmada</span>
              </div>
            </div>
            <p v-if="reservasConfirmadas.length === 0" class="text-sm text-gray-600 text-center py-4">Sin reservas pendientes</p>
          </div>
        </div>
      </div>
    </div>

    <!-- CHECK-OUT -->
    <div v-else-if="activeTab === 'checkout'">
      <div class="bg-gray-900 border border-gray-800 rounded-xl p-6 max-w-lg">
        <h3 class="text-base font-semibold text-gray-200 mb-4">Registrar Check-out</h3>
        <form @submit.prevent="hacerCheckout" class="space-y-4">
          <div>
            <label class="label">ID de Reserva</label>
            <input v-model.number="checkoutForm.reserva_id" type="number" required class="input-field w-full" @change="cargarResumenCheckout" placeholder="Número de reserva" />
          </div>
          <!-- Resumen de cargos -->
          <div v-if="resumenCheckout" class="bg-gray-800 border border-gray-700 rounded-lg p-4 space-y-2">
            <p class="text-xs font-medium text-gray-400 uppercase">Resumen de cargos</p>
            <div class="flex justify-between text-sm">
              <span class="text-gray-400">Noches</span>
              <span class="text-gray-200">{{ resumenCheckout.noches }} noche(s)</span>
            </div>
            <div class="flex justify-between text-sm">
              <span class="text-gray-400">Subtotal habitación</span>
              <span class="text-gray-200">${{ Number(resumenCheckout.subtotal).toLocaleString('es-CO') }}</span>
            </div>
            <div class="flex justify-between text-sm border-t border-gray-700 pt-2">
              <span class="text-gray-300 font-medium">Total estimado</span>
              <span class="text-hotel-gold font-bold">${{ Number(resumenCheckout.total).toLocaleString('es-CO') }}</span>
            </div>
          </div>
          <BaseButton type="submit" :disabled="procesando">{{ procesando ? 'Procesando...' : '✓ Confirmar Check-out' }}</BaseButton>
        </form>
        <!-- Reservas en checkin -->
        <div class="mt-6">
          <p class="text-xs font-medium text-gray-500 uppercase tracking-wider mb-3">Huéspedes actualmente hospedados</p>
          <div class="space-y-2 max-h-60 overflow-y-auto">
            <div v-for="r in reservasEnCheckin" :key="r.id"
              @click="checkoutForm.reserva_id = r.id; cargarResumenCheckout()"
              class="cursor-pointer bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-lg p-3 transition-colors"
            >
              <div class="flex justify-between items-start">
                <div>
                  <p class="text-sm font-medium text-gray-200">Reserva #{{ r.id }} — Hab. {{ r.habitacion_id }}</p>
                  <p class="text-xs text-gray-500">Entrada: {{ r.fecha_entrada }}</p>
                </div>
                <span class="text-xs bg-green-900/50 text-green-300 px-2 py-0.5 rounded-full">check-in</span>
              </div>
            </div>
            <p v-if="reservasEnCheckin.length === 0" class="text-sm text-gray-600 text-center py-4">Sin huéspedes activos</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, inject } from 'vue';
import api from '../services/api';
import BaseButton from '../components/BaseButton.vue';

const toast = inject('toast');
const activeTab = ref('checkin');
const procesando = ref(false);
const reservasConfirmadas = ref([]);
const reservasEnCheckin = ref([]);
const resumenCheckout = ref(null);

const tabs = [
  { key: 'checkin', label: '🔑 Check-in' },
  { key: 'checkout', label: '🚪 Check-out' },
];

const checkinForm = ref({ reserva_id: '', notas: '' });
const checkoutForm = ref({ reserva_id: '' });

async function cargarReservas() {
  try {
    const res = await api.get('/reservas');
    const all = res.data.data || res.data;
    reservasConfirmadas.value = all.filter(r => r.estado === 'confirmada');
    reservasEnCheckin.value = all.filter(r => r.estado === 'checkin');
  } catch {}
}

async function hacerCheckin() {
  procesando.value = true;
  try {
    await api.post(`/reservas/${checkinForm.value.reserva_id}/checkin`, { notas: checkinForm.value.notas });
    toast?.value?.add('Check-in registrado exitosamente', 'success');
    checkinForm.value = { reserva_id: '', notas: '' };
    await cargarReservas();
  } catch (err) {
    toast?.value?.add(err.response?.data?.error?.message || 'Error al hacer check-in', 'error');
  } finally { procesando.value = false; }
}

async function cargarResumenCheckout() {
  if (!checkoutForm.value.reserva_id) return;
  try {
    const res = await api.get(`/reservas/${checkoutForm.value.reserva_id}`);
    const r = res.data.data || res.data;
    const entrada = new Date(r.fecha_entrada);
    const salida = new Date(r.fecha_salida);
    const noches = Math.max(1, Math.ceil((salida - entrada) / (1000 * 60 * 60 * 24)));
    resumenCheckout.value = { noches, subtotal: r.total, total: r.total };
  } catch { resumenCheckout.value = null; }
}

async function hacerCheckout() {
  procesando.value = true;
  try {
    await api.post(`/reservas/${checkoutForm.value.reserva_id}/checkout`, {});
    toast?.value?.add('Check-out registrado exitosamente', 'success');
    checkoutForm.value = { reserva_id: '' };
    resumenCheckout.value = null;
    await cargarReservas();
  } catch (err) {
    toast?.value?.add(err.response?.data?.error?.message || 'Error al hacer check-out', 'error');
  } finally { procesando.value = false; }
}

onMounted(cargarReservas);
</script>

<style scoped>
.input-field { @apply bg-gray-800 border border-gray-700 text-gray-200 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-hotel-gold focus:ring-1 focus:ring-hotel-gold transition; }
.label { @apply block text-xs font-medium text-gray-400 mb-1; }
</style>
