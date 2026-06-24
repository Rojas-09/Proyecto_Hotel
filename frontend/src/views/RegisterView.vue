<template>
  <div class="min-h-screen bg-gray-950 flex items-center justify-center p-4">
    <div class="w-full max-w-md">
      <div class="text-center mb-8">
        <div class="text-6xl mb-4">🏨</div>
        <h1 class="text-3xl font-bold text-hotel-gold tracking-wide">HotelBook Pro</h1>
        <p class="text-gray-400 mt-2 text-sm">Crear cuenta de cliente</p>
      </div>

      <div class="bg-gray-900 border border-gray-800 rounded-2xl shadow-2xl p-8">
        <h2 class="text-lg font-semibold text-gray-200 mb-6">Registrarse</h2>

        <form @submit.prevent="handleRegister" class="space-y-4">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label for="nombre" class="block text-sm font-medium text-gray-400 mb-1">Nombre</label>
              <input id="nombre" v-model="form.nombre" type="text" required
                class="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-hotel-gold focus:ring-1 focus:ring-hotel-gold transition"
                placeholder="Juan" />
            </div>
            <div>
              <label for="apellido" class="block text-sm font-medium text-gray-400 mb-1">Apellido</label>
              <input id="apellido" v-model="form.apellido" type="text" required
                class="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-hotel-gold focus:ring-1 focus:ring-hotel-gold transition"
                placeholder="Pérez" />
            </div>
          </div>

          <div>
            <label for="email" class="block text-sm font-medium text-gray-400 mb-1">Correo electrónico</label>
            <input id="email" v-model="form.email" type="email" required
              class="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-hotel-gold focus:ring-1 focus:ring-hotel-gold transition"
              placeholder="correo@ejemplo.com" />
          </div>

          <div>
            <label for="password" class="block text-sm font-medium text-gray-400 mb-1">Contraseña</label>
            <div class="relative">
              <input id="password" v-model="form.password" :type="showPassword ? 'text' : 'password'" required minlength="8"
                class="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-hotel-gold focus:ring-1 focus:ring-hotel-gold transition pr-10"
                placeholder="Mínimo 8 caracteres" />
              <button type="button" @click="showPassword = !showPassword"
                class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 transition-colors">
                {{ showPassword ? '🙈' : '👁️' }}
              </button>
            </div>
          </div>

          <div>
            <label for="telefono" class="block text-sm font-medium text-gray-400 mb-1">Teléfono</label>
            <input id="telefono" v-model="form.telefono" type="tel"
              class="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-hotel-gold focus:ring-1 focus:ring-hotel-gold transition"
              placeholder="+57 300 123 4567" />
          </div>

          <div>
            <label for="documento_id" class="block text-sm font-medium text-gray-400 mb-1">
              Documento de identidad <span class="text-red-400">*</span>
            </label>
            <div class="flex gap-2">
              <select v-model="form.tipo_documento"
                class="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5 text-sm text-gray-200 focus:outline-none focus:border-hotel-gold focus:ring-1 focus:ring-hotel-gold transition w-28">
                <option value="CC">CC</option>
                <option value="CE">CE</option>
                <option value="Pasaporte">Pasaporte</option>
              </select>
              <input id="documento_id" v-model="form.documento_id" type="text" required
                class="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-hotel-gold focus:ring-1 focus:ring-hotel-gold transition"
                placeholder="123456789" />
            </div>
          </div>

          <p v-if="errorMsg" class="text-sm text-red-400 bg-red-900/30 border border-red-800 rounded-lg px-3 py-2">
            {{ errorMsg }}
          </p>

          <button type="submit" :disabled="loading"
            class="w-full bg-hotel-gold hover:bg-yellow-600 text-white font-semibold py-2.5 px-4 rounded-lg transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed text-sm">
            <span v-if="loading">Creando cuenta...</span>
            <span v-else>Crear cuenta</span>
          </button>
        </form>

        <p class="text-center text-gray-500 text-sm mt-6">
          ¿Ya tienes cuenta?
          <router-link to="/login" class="text-hotel-gold hover:text-yellow-500 transition-colors font-medium">
            Inicia sesión
          </router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import api from '../services/api';

const router = useRouter();

const form = ref({
  nombre: '',
  apellido: '',
  email: '',
  password: '',
  telefono: '',
  tipo_documento: 'CC',
  documento_id: '',
});

const loading = ref(false);
const errorMsg = ref('');
const showPassword = ref(false);

async function handleRegister() {
  loading.value = true;
  errorMsg.value = '';

  if (form.value.password.length < 8) {
    errorMsg.value = 'La contraseña debe tener al menos 8 caracteres.';
    loading.value = false;
    return;
  }

  try {
    await api.post('/auth/register', {
      nombre: form.value.nombre.trim(),
      apellido: form.value.apellido.trim(),
      email: form.value.email.trim().toLowerCase(),
      password: form.value.password,
      telefono: form.value.telefono.trim() || undefined,
      tipo_documento: form.value.tipo_documento,
      documento_id: form.value.documento_id.trim(),
    });
    router.push('/login');
  } catch (err) {
    if (err.response?.data?.error?.message) {
      const msg = err.response.data.error.message;
      errorMsg.value = typeof msg === 'string' ? msg : Object.values(msg).flat().join(', ');
    } else {
      errorMsg.value = 'Error al conectar con el servidor.';
    }
  } finally {
    loading.value = false;
  }
}
</script>
