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
            <label class="label">Reserva confirmada</label>
            <SearchSelect
              v-model="checkinForm.reserva_id"
              :options="reservasConfirmadas.map(r => ({ value: r.id, label: '#' + r.id + ' — Hab. ' + (r.habitacion_numero || r.id_habitacion) + ' — ' + (r.huesped_nombre || 'Huésped ' + r.id_huesped) }))"
              placeholder="Seleccionar reserva..."
            />
          </div>
          <div v-if="checkinForm.reserva_id" class="bg-gray-800 border border-gray-700 rounded-lg p-3 text-sm text-gray-400">
            <p v-for="r in reservasConfirmadas.filter(r => r.id === checkinForm.reserva_id)" :key="r.id">
              📅 Entrada: <span class="text-gray-200">{{ r.fecha_entrada }}</span> &nbsp;|&nbsp;
              Salida: <span class="text-gray-200">{{ r.fecha_salida }}</span> &nbsp;|&nbsp;
              Total: <span class="text-hotel-gold font-medium">${{ Number(r.total).toLocaleString('es-CO') }}</span>
            </p>
          </div>
          <BaseButton type="submit" :disabled="procesando || !checkinForm.reserva_id">
            {{ procesando ? 'Procesando...' : '✓ Confirmar Check-in' }}
          </BaseButton>
        </form>

        <div class="mt-6" v-if="reservasConfirmadas.length === 0">
          <div class="text-center text-gray-600 py-6 text-sm border border-dashed border-gray-700 rounded-lg">
            No hay reservas confirmadas pendientes de check-in.<br/>
            <span class="text-xs text-gray-700">Primero confirma la reserva desde el módulo de Reservas.</span>
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
            <label class="label">Huésped actualmente hospedado</label>
            <SearchSelect
              v-model="checkoutForm.reserva_id"
              :options="reservasEnCheckin.map(r => ({ value: r.id, label: '#' + r.id + ' — Hab. ' + (r.habitacion_numero || r.id_habitacion) + ' — ' + (r.huesped_nombre || 'Huésped ' + r.id_huesped) }))"
              placeholder="Seleccionar reserva..."
              @update:model-value="cargarResumenCheckout"
            />
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
            <div class="flex justify-between text-sm" v-if="resumenCheckout.servicios > 0">
              <span class="text-gray-400">Servicios Adicionales (Spa, Comedor, etc)</span>
              <span class="text-gray-200">${{ Number(resumenCheckout.servicios).toLocaleString('es-CO') }}</span>
            </div>
            <div class="flex justify-between text-sm">
              <span class="text-gray-400">IVA (19%)</span>
              <span class="text-gray-200">${{ Number(resumenCheckout.impuestos).toLocaleString('es-CO') }}</span>
            </div>
            <div class="flex justify-between text-sm border-t border-gray-700 pt-2">
              <span class="text-gray-300 font-medium">Total Final</span>
              <span class="text-hotel-gold font-bold">${{ Number(resumenCheckout.total).toLocaleString('es-CO') }}</span>
            </div>
          </div>

          <!-- Advertencia de pago -->
          <div class="bg-yellow-900/20 border border-yellow-800/50 rounded-lg p-3 text-xs text-yellow-400">
            ⚠️ El check-out requiere registrar el pago de liquidación previamente. Si falla, ve al módulo de <strong>Pagos</strong> primero.
          </div>

          <BaseButton type="submit" :disabled="procesando || !checkoutForm.reserva_id">
            {{ procesando ? 'Procesando...' : '✓ Confirmar Check-out' }}
          </BaseButton>
        </form>

        <div class="mt-6" v-if="reservasEnCheckin.length === 0">
          <div class="text-center text-gray-600 py-6 text-sm border border-dashed border-gray-700 rounded-lg">
            No hay huéspedes actualmente en check-in.
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
import SearchSelect from '../components/SearchSelect.vue';

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

const checkinForm = ref({ reserva_id: '' });
const checkoutForm = ref({ reserva_id: '' });

async function cargarReservas() {
  try {
    const res = await api.get('/reservas/');
    const all = res.data.data || res.data;
    // Los estados vienen con mayúscula inicial del backend (ej: "Confirmada", "Ocupada")
    reservasConfirmadas.value = all.filter(r => r.estado === 'Confirmada');
    reservasEnCheckin.value = all.filter(r => r.estado === 'Ocupada');
  } catch {}
}

async function hacerCheckin() {
  procesando.value = true;
  try {
    await api.put(`/reservas/${checkinForm.value.reserva_id}/checkin`);
    toast?.value?.add('Check-in registrado exitosamente', 'success');
    checkinForm.value = { reserva_id: '' };
    await cargarReservas();
  } catch (err) {
    const msg = err.response?.data?.message || err.response?.data?.mensaje || 'Error al hacer check-in';
    toast?.value?.add(msg, 'error');
  } finally { procesando.value = false; }
}

async function cargarResumenCheckout() {
  if (!checkoutForm.value.reserva_id) return;
  const reserva = reservasEnCheckin.value.find(r => r.id === checkoutForm.value.reserva_id);
  if (reserva) {
    try {
      const resServ = await api.get(`/reservas/${reserva.id}/servicios`);
      const servicios = resServ.data.servicios || resServ.data.data || [];
      const totalServicios = servicios.reduce((acc, s) => acc + Number(s.costo), 0);
      
      resumenCheckout.value = {
        noches: reserva.noches,
        subtotal: reserva.subtotal,
        impuestos: reserva.impuestos,
        servicios: totalServicios,
        total: Number(reserva.total) + totalServicios
      };
    } catch {
      resumenCheckout.value = {
        noches: reserva.noches,
        subtotal: reserva.subtotal,
        impuestos: reserva.impuestos,
        servicios: 0,
        total: reserva.total
      };
    }
  }
}

async function hacerCheckout() {
  procesando.value = true;
  try {
    // Para hacer check-out, se requiere el pago de liquidación aprobado (RF-13)
    await api.post(`/pagos/liquidacion/${checkoutForm.value.reserva_id}`, { metodo: 'Efectivo' });
    
    await api.put(`/reservas/${checkoutForm.value.reserva_id}/checkout`);
    toast?.value?.add('Check-out completado. Se generó la factura automáticamente.', 'success');
    checkoutForm.value = { reserva_id: '' };
    resumenCheckout.value = null;
    await cargarReservas();
  } catch (err) {
    const msg = err.response?.data?.error || err.response?.data?.message || err.response?.data?.mensaje || 'Error al hacer check-out';
    toast?.value?.add(msg, 'error');
  } finally { procesando.value = false; }
}

onMounted(cargarReservas);
</script>

<style scoped>
@reference "../style.css";
.input-field { @apply bg-gray-800 border border-gray-700 text-gray-200 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-hotel-gold focus:ring-1 focus:ring-hotel-gold transition; }
.label { @apply block text-xs font-medium text-gray-400 mb-1; }
</style>
