<template>
  <div>
    <div class="mb-6">
      <h2 class="text-2xl font-bold text-white">Servicios Adicionales</h2>
      <p class="text-sm text-gray-500 mt-1">Gestión de comedor y spa vinculados a reservas</p>
    </div>

    <!-- Tabs -->
    <div class="flex gap-2 mb-6 border-b border-gray-800">
      <button v-for="tab in tabs" :key="tab.key" @click="activeTab = tab.key"
        :class="['px-5 py-2.5 text-sm font-medium transition-colors -mb-px border-b-2', activeTab === tab.key ? 'border-hotel-gold text-hotel-gold' : 'border-transparent text-gray-400 hover:text-white']">
        {{ tab.label }}
      </button>
    </div>

    <!-- COMEDOR -->
    <div v-if="activeTab === 'comedor'">
      <div class="flex justify-end mb-4">
        <BaseButton @click="openPedido">+ Nuevo Pedido</BaseButton>
      </div>
      <BaseTable :columns="columnasPedidos" :data="pedidos">
        <template #estado="{ item }">
          <span :class="estadoPedidoClass(item.estado)" class="px-2 py-0.5 rounded-full text-xs font-medium capitalize">{{ item.estado }}</span>
        </template>
        <template #total="{ item }">
          <span class="text-hotel-gold font-medium">${{ Number(item.total || 0).toLocaleString('es-CO') }}</span>
        </template>
      </BaseTable>
    </div>

    <!-- SPA -->
    <div v-else-if="activeTab === 'spa'">
      <div class="flex justify-end mb-4">
        <BaseButton @click="openCita">+ Agendar Cita</BaseButton>
      </div>
      <BaseTable :columns="columnasCitas" :data="citas">
        <template #estado="{ item }">
          <span :class="estadoCitaClass(item.estado)" class="px-2 py-0.5 rounded-full text-xs font-medium capitalize">{{ item.estado }}</span>
        </template>
      </BaseTable>
    </div>

    <!-- Modal Pedido -->
    <BaseModal v-model="showPedido" title="Nuevo Pedido — Comedor">
      <form id="pedido-form" @submit.prevent="guardarPedido" class="space-y-4">
        <div>
          <label class="label">ID de Reserva</label>
          <input v-model.number="pedidoForm.reserva_id" type="number" required class="input-field w-full" />
        </div>
        <div>
          <label class="label">Descripción del pedido</label>
          <textarea v-model="pedidoForm.descripcion" rows="3" required class="input-field w-full" placeholder="Ej: Desayuno continental para 2, café negro..."></textarea>
        </div>
        <div>
          <label class="label">Total (COP)</label>
          <input v-model.number="pedidoForm.total" type="number" required class="input-field w-full" placeholder="45000" />
        </div>
      </form>
      <template #footer>
        <BaseButton variant="secondary" @click="showPedido = false">Cancelar</BaseButton>
        <BaseButton type="submit" form="pedido-form" :disabled="guardando">{{ guardando ? 'Guardando...' : 'Guardar' }}</BaseButton>
      </template>
    </BaseModal>

    <!-- Modal Cita Spa -->
    <BaseModal v-model="showCita" title="Agendar Cita — Spa">
      <form id="cita-form" @submit.prevent="guardarCita" class="space-y-4">
        <div>
          <label class="label">ID de Reserva</label>
          <input v-model.number="citaForm.reserva_id" type="number" required class="input-field w-full" />
        </div>
        <div>
          <label class="label">Servicio</label>
          <input v-model="citaForm.servicio" required class="input-field w-full" placeholder="Masaje relajante, Facial, etc." />
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="label">Fecha</label>
            <input v-model="citaForm.fecha" type="date" required class="input-field w-full" />
          </div>
          <div>
            <label class="label">Hora</label>
            <input v-model="citaForm.hora" type="time" required class="input-field w-full" />
          </div>
        </div>
        <div>
          <label class="label">Duración (minutos)</label>
          <input v-model.number="citaForm.duracion_minutos" type="number" required class="input-field w-full" placeholder="60" />
        </div>
      </form>
      <template #footer>
        <BaseButton variant="secondary" @click="showCita = false">Cancelar</BaseButton>
        <BaseButton type="submit" form="cita-form" :disabled="guardando">{{ guardando ? 'Guardando...' : 'Agendar' }}</BaseButton>
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
const activeTab = ref('comedor');
const pedidos = ref([]);
const citas = ref([]);
const showPedido = ref(false);
const showCita = ref(false);
const guardando = ref(false);
const tabs = [{ key: 'comedor', label: '🍽️ Comedor' }, { key: 'spa', label: '💆 Spa' }];

const columnasPedidos = [
  { key: 'id', label: '#' }, { key: 'reserva_id', label: 'Reserva' },
  { key: 'descripcion', label: 'Descripción' }, { key: 'total', label: 'Total' }, { key: 'estado', label: 'Estado' },
];
const columnasCitas = [
  { key: 'id', label: '#' }, { key: 'reserva_id', label: 'Reserva' }, { key: 'servicio', label: 'Servicio' },
  { key: 'fecha', label: 'Fecha' }, { key: 'hora', label: 'Hora' }, { key: 'estado', label: 'Estado' },
];

const pedidoForm = ref({ reserva_id: '', descripcion: '', total: '' });
const citaForm = ref({ reserva_id: '', servicio: '', fecha: '', hora: '', duracion_minutos: 60 });

async function cargar() {
  try {
    const [resP, resC] = await Promise.all([api.get('/comedor/pedidos'), api.get('/spa/citas')]);
    pedidos.value = resP.data.data || resP.data;
    citas.value = resC.data.data || resC.data;
  } catch {}
}

function openPedido() { pedidoForm.value = { reserva_id: '', descripcion: '', total: '' }; showPedido.value = true; }
function openCita() { citaForm.value = { reserva_id: '', servicio: '', fecha: '', hora: '', duracion_minutos: 60 }; showCita.value = true; }

async function guardarPedido() {
  guardando.value = true;
  try {
    await api.post('/comedor/pedidos', pedidoForm.value);
    toast?.value?.add('Pedido registrado', 'success');
    showPedido.value = false;
    await cargar();
  } catch (err) {
    toast?.value?.add(err.response?.data?.error?.message || 'Error al guardar', 'error');
  } finally { guardando.value = false; }
}

async function guardarCita() {
  guardando.value = true;
  try {
    await api.post('/spa/citas', citaForm.value);
    toast?.value?.add('Cita agendada correctamente', 'success');
    showCita.value = false;
    await cargar();
  } catch (err) {
    toast?.value?.add(err.response?.data?.error?.message || 'Error al agendar', 'error');
  } finally { guardando.value = false; }
}

const estadoPedidoClass = (e) => ({ pendiente: 'bg-yellow-900/50 text-yellow-300', preparando: 'bg-blue-900/50 text-blue-300', entregado: 'bg-green-900/50 text-green-300' }[e] || 'bg-gray-800 text-gray-400');
const estadoCitaClass = (e) => ({ programada: 'bg-blue-900/50 text-blue-300', completada: 'bg-green-900/50 text-green-300', cancelada: 'bg-red-900/50 text-red-300' }[e] || 'bg-gray-800 text-gray-400');

onMounted(cargar);
</script>

<style scoped>
.input-field { @apply bg-gray-800 border border-gray-700 text-gray-200 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-hotel-gold focus:ring-1 focus:ring-hotel-gold transition; }
.label { @apply block text-xs font-medium text-gray-400 mb-1; }
</style>
