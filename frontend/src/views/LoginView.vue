<template>
  <div class="min-h-screen bg-gray-950 flex items-center justify-center p-4">
    <div class="w-full max-w-md">
      <!-- Logo y Encabezado -->
      <div class="text-center mb-8">
        <div class="text-6xl mb-4">🏨</div>
        <h1 class="text-3xl font-bold text-hotel-gold tracking-wide">HotelBook Pro</h1>
        <p class="text-gray-400 mt-2 text-sm">Sistema de gestión hotelera</p>
      </div>

      <!-- Card de Login -->
      <div class="bg-gray-900 border border-gray-800 rounded-2xl shadow-2xl p-8">
        <h2 class="text-lg font-semibold text-gray-200 mb-6">Iniciar sesión</h2>

        <form @submit.prevent="handleLogin" class="space-y-5">
          <!-- Email -->
          <div>
            <label for="email" class="block text-sm font-medium text-gray-400 mb-1">Correo electrónico</label>
            <input
              id="email"
              v-model="form.email"
              type="email"
              required
              placeholder="correo@hotel.com"
              class="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-hotel-gold focus:ring-1 focus:ring-hotel-gold transition"
            />
          </div>

          <!-- Contraseña -->
          <div>
            <label for="password" class="block text-sm font-medium text-gray-400 mb-1">Contraseña</label>
            <div class="relative">
              <input
                id="password"
                v-model="form.password"
                :type="showPassword ? 'text' : 'password'"
                required
                placeholder="••••••••"
                class="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-hotel-gold focus:ring-1 focus:ring-hotel-gold transition pr-10"
              />
              <button
                type="button"
                @click="showPassword = !showPassword"
                class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 transition-colors"
              >
                {{ showPassword ? '🙈' : '👁️' }}
              </button>
            </div>
          </div>

          <!-- Error -->
          <p v-if="errorMsg" class="text-sm text-red-400 bg-red-900/30 border border-red-800 rounded-lg px-3 py-2">
            {{ errorMsg }}
          </p>

          <!-- Botón -->
          <button
            type="submit"
            :disabled="loading"
            class="w-full bg-hotel-gold hover:bg-yellow-600 text-white font-semibold py-2.5 px-4 rounded-lg transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
          >
            <span v-if="loading">Ingresando...</span>
            <span v-else>Ingresar</span>
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import api from '../services/api';

const router = useRouter();
const authStore = useAuthStore();

const form = ref({ email: '', password: '' });
const loading = ref(false);
const errorMsg = ref('');
const showPassword = ref(false);

async function handleLogin() {
  loading.value = true;
  errorMsg.value = '';
  try {
    const res = await api.post('/auth/login', {
      email: form.value.email,
      password: form.value.password,
    });

    const { token, usuario } = res.data.data;
    authStore.login(token, usuario);
    router.push('/habitaciones');
  } catch (err) {
    if (err.response?.data?.error?.message) {
      errorMsg.value = err.response.data.error.message;
    } else {
      errorMsg.value = 'Error al conectar con el servidor.';
    }
  } finally {
    loading.value = false;
  }
}
</script>
