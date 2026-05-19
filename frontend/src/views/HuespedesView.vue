<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h2 class="text-2xl font-bold text-white">Huéspedes</h2>
        <p class="text-sm text-gray-500 mt-1">Gestión de huéspedes registrados</p>
      </div>
      <BaseButton @click="openCreate">+ Nuevo Huésped</BaseButton>
    </div>

    <!-- Búsqueda -->
    <div class="bg-gray-900 border border-gray-800 rounded-xl p-4 mb-6">
      <input v-model="busqueda" type="text" placeholder="Buscar por nombre, apellido o email..." class="input-field w-full" />
    </div>

    <BaseTable :columns="columns" :data="huespedesFiltrados" :pagination="true" :current-page="currentPage" :total-pages="totalPages" @prev="currentPage--" @next="currentPage++">
      <template #nombre="{ item }">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-full bg-hotel-gold/30 flex items-center justify-center text-hotel-gold text-sm font-bold">
            {{ item.nombre?.charAt(0) }}{{ item.apellido?.charAt(0) }}
          </div>
          <div>
            <p class="text-gray-200 font-medium">{{ item.nombre }} {{ item.apellido }}</p>
            <p class="text-gray-500 text-xs">{{ item.email }}</p>
          </div>
        </div>
      </template>
      <template #documento="{ item }">
        <span class="text-gray-400 text-xs">{{ item.tipo_documento }}: {{ item.documento_id }}</span>
      </template>
      <template #acciones="{ item }">
        <div class="flex gap-2">
          <button @click="verHistorial(item)" class="text-xs text-blue-400 hover:text-blue-300 transition-colors">Historial</button>
          <button @click="openEdit(item)" class="text-xs text-hotel-gold hover:text-yellow-400 transition-colors">Editar</button>
        </div>
      </template>
    </BaseTable>

    <!-- Modal Crear/Editar -->
    <BaseModal v-model="showModal" :title="editingItem ? 'Editar Huésped' : 'Nuevo Huésped'">
      <form id="huesped-form" @submit.prevent="guardar" class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="label">Nombre</label>
            <input v-model="form.nombre" required class="input-field w-full" placeholder="Juan" />
          </div>
          <div>
            <label class="label">Apellido</label>
            <input v-model="form.apellido" required class="input-field w-full" placeholder="Pérez" />
          </div>
        </div>
        <div>
          <label class="label">Email</label>
          <input v-model="form.email" type="email" required class="input-field w-full" placeholder="juan@email.com" />
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="label">Teléfono</label>
            <input v-model="form.telefono" class="input-field w-full" placeholder="+57 300..." />
          </div>
          <div>
            <label class="label">Tipo documento</label>
            <select v-model="form.tipo_documento" class="input-field w-full">
              <option value="CC">CC</option>
              <option value="Pasaporte">Pasaporte</option>
              <option value="CE">CE</option>
            </select>
          </div>
        </div>
        <div>
          <label class="label">Número de documento</label>
          <input v-model="form.documento_id" required class="input-field w-full" placeholder="123456789" />
        </div>
        <div v-if="!editingItem">
          <label class="label">Contraseña</label>
          <input v-model="form.password" type="password" :required="!editingItem" class="input-field w-full" placeholder="Mínimo 8 caracteres" />
        </div>
      </form>
      <template #footer>
        <BaseButton variant="secondary" @click="showModal = false">Cancelar</BaseButton>
        <BaseButton type="submit" form="huesped-form" :disabled="saving">{{ saving ? 'Guardando...' : 'Guardar' }}</BaseButton>
      </template>
    </BaseModal>

    <!-- Modal Historial -->
    <BaseModal v-model="showHistorial" :title="`Historial — ${huespedSeleccionado?.nombre} ${huespedSeleccionado?.apellido}`">
      <div v-if="historial.length === 0" class="text-center text-gray-500 py-6 text-sm">Sin reservas registradas</div>
      <div v-else class="space-y-3 max-h-80 overflow-y-auto">
        <div v-for="r in historial" :key="r.id" class="bg-gray-800 rounded-lg p-3 border border-gray-700">
          <div class="flex justify-between text-sm">
            <span class="text-gray-300">Hab. {{ r.habitacion_numero || r.id_habitacion }}</span>
            <span :class="estadoClass(r.estado)" class="px-2 py-0.5 rounded-full text-xs font-medium capitalize">{{ r.estado }}</span>
          </div>
          <p class="text-xs text-gray-500 mt-1">{{ r.fecha_entrada }} → {{ r.fecha_salida }} ({{ r.noches }} noches)</p>
          <p class="text-hotel-gold text-sm font-medium mt-1">${{ Number(r.total).toLocaleString('es-CO') }}</p>
        </div>
      </div>
    </BaseModal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, inject } from 'vue';
import api from '../services/api';
import BaseButton from '../components/BaseButton.vue';
import BaseTable from '../components/BaseTable.vue';
import BaseModal from '../components/BaseModal.vue';

const toast = inject('toast');
const huespedes = ref([]);
const busqueda = ref('');
const showModal = ref(false);
const showHistorial = ref(false);
const editingItem = ref(null);
const huespedSeleccionado = ref(null);
const historial = ref([]);
const saving = ref(false);
const currentPage = ref(1);
const totalPages = ref(1);

const columns = [
  { key: 'nombre', label: 'Huésped' },
  { key: 'documento', label: 'Documento' },
  { key: 'telefono', label: 'Teléfono' },
  { key: 'acciones', label: 'Acciones' },
];

const defaultForm = {
  nombre: '', apellido: '', email: '', telefono: '',
  documento_id: '', tipo_documento: 'CC', password: ''
};
const form = ref({ ...defaultForm });

const huespedesFiltrados = computed(() => {
  let result = huespedes.value;
  if (busqueda.value) {
    const q = busqueda.value.toLowerCase();
    result = result.filter(h => `${h.nombre} ${h.apellido} ${h.email} ${h.documento_id}`.toLowerCase().includes(q));
  }
  totalPages.value = Math.ceil(result.length / 10) || 1;
  const start = (currentPage.value - 1) * 10;
  return result.slice(start, start + 10);
});

async function cargar() {
  try {
    const res = await api.get('/huespedes/');
    huespedes.value = res.data.data || res.data;
  } catch { toast?.value?.add('Error al cargar huéspedes', 'error'); }
}

function openCreate() { editingItem.value = null; form.value = { ...defaultForm }; showModal.value = true; }
function openEdit(item) {
  editingItem.value = item;
  form.value = {
    nombre: item.nombre,
    apellido: item.apellido,
    email: item.email,
    telefono: item.telefono || '',
    documento_id: item.documento_id || '',
    tipo_documento: item.tipo_documento || 'CC',
    password: ''
  };
  showModal.value = true;
}

async function verHistorial(huesped) {
  huespedSeleccionado.value = huesped;
  try {
    const res = await api.get('/reservas/', { params: { id_huesped: huesped.id } });
    historial.value = res.data.data || res.data;
  } catch { historial.value = []; }
  showHistorial.value = true;
}

async function guardar() {
  saving.value = true;
  try {
    if (editingItem.value) {
      // Actualizar datos del usuario (nombre, apellido, teléfono)
      await api.put(`/auth/usuarios/${editingItem.value.id_usuario}`, {
        nombre: form.value.nombre,
        apellido: form.value.apellido,
        telefono: form.value.telefono,
      });
      // Actualizar datos del huésped (documento)
      await api.put(`/huespedes/${editingItem.value.id}`, {
        documento_id: form.value.documento_id,
        tipo_documento: form.value.tipo_documento,
      });
      toast?.value?.add('Huésped actualizado', 'success');
    } else {
      // Registrar nuevo usuario cliente + huésped
      await api.post('/auth/register', {
        nombre: form.value.nombre,
        apellido: form.value.apellido,
        email: form.value.email,
        telefono: form.value.telefono,
        password: form.value.password,
        rol: 'cliente',
        documento_id: form.value.documento_id,
        tipo_documento: form.value.tipo_documento,
      });
      toast?.value?.add('Huésped registrado exitosamente', 'success');
    }
    showModal.value = false;
    await cargar();
  } catch (err) {
    const msg = err.response?.data?.error?.message || err.response?.data?.mensaje || 'Error al guardar';
    toast?.value?.add(msg, 'error');
  } finally { saving.value = false; }
}

const estadoClass = (e) => ({
  Confirmada: 'bg-blue-900/50 text-blue-300',
  Pendiente: 'bg-yellow-900/50 text-yellow-300',
  Ocupada: 'bg-green-900/50 text-green-300',
  Completada: 'bg-gray-700 text-gray-300',
  Cancelada: 'bg-red-900/50 text-red-300'
}[e] || 'bg-gray-800 text-gray-400');

onMounted(cargar);
</script>

<style scoped>
@reference "../style.css";
.input-field { @apply bg-gray-800 border border-gray-700 text-gray-200 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-hotel-gold focus:ring-1 focus:ring-hotel-gold transition; }
.label { @apply block text-xs font-medium text-gray-400 mb-1; }
</style>
