<template>
  <div class="flex h-screen bg-gray-950">
    <!-- Sidebar -->
    <aside :class="['flex-shrink-0 flex flex-col bg-gray-900 border-r border-gray-800 transition-all duration-300', sidebarOpen ? 'w-64' : 'w-16']">
      <!-- Logo -->
      <div class="flex items-center h-16 px-4 border-b border-gray-800 overflow-hidden">
        <span class="text-hotel-gold text-2xl font-bold">🏨</span>
        <span v-if="sidebarOpen" class="ml-3 text-hotel-gold font-bold text-sm tracking-wide whitespace-nowrap">HotelBook Pro</span>
      </div>

      <!-- Navigation -->
      <nav class="flex-1 px-2 py-4 space-y-1 overflow-y-auto">
        <template v-for="item in navItems" :key="item.path">
          <router-link
            v-if="!item.role || authStore.userRole === item.role || authStore.userRole === 'admin'"
            :to="item.path"
            :class="[
              'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors duration-150',
              $route.path.startsWith(item.path) ? 'bg-hotel-gold/20 text-hotel-gold' : 'text-gray-400 hover:bg-gray-800 hover:text-white'
            ]"
          >
            <span class="text-xl flex-shrink-0">{{ item.icon }}</span>
            <span v-if="sidebarOpen" class="whitespace-nowrap">{{ item.label }}</span>
          </router-link>
        </template>
      </nav>

      <!-- User Info -->
      <div class="border-t border-gray-800 p-3 flex items-center gap-3">
        <div class="w-8 h-8 rounded-full bg-hotel-gold/30 flex items-center justify-center flex-shrink-0">
          <span class="text-hotel-gold text-sm font-bold">{{ userInitial }}</span>
        </div>
        <div v-if="sidebarOpen" class="overflow-hidden">
          <p class="text-xs font-medium text-gray-200 truncate">{{ authStore.user?.nombre }}</p>
          <p class="text-xs text-gray-500 capitalize">{{ authStore.user?.rol }}</p>
        </div>
        <button v-if="sidebarOpen" @click="authStore.logout()" class="ml-auto text-gray-500 hover:text-red-400 transition-colors" title="Cerrar sesión">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
        </button>
      </div>
    </aside>

    <!-- Main Content -->
    <div class="flex-1 flex flex-col min-w-0 overflow-hidden">
      <!-- Header -->
      <header class="h-16 bg-gray-900 border-b border-gray-800 flex items-center px-4 gap-4 flex-shrink-0">
        <button @click="sidebarOpen = !sidebarOpen" class="text-gray-400 hover:text-white transition-colors">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        <h1 class="text-gray-200 font-semibold text-base">{{ currentPageTitle }}</h1>
        <div class="ml-auto flex items-center gap-4">
          <span class="text-xs text-gray-500">{{ formattedDate }}</span>
        </div>
      </header>

      <!-- Page View -->
      <main class="flex-1 overflow-y-auto p-6">
        <router-view />
      </main>
    </div>

    <!-- Toast global -->
    <BaseToast ref="toastRef" />
  </div>
</template>

<script setup>
import { ref, computed, provide } from 'vue';
import { useRoute } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import BaseToast from '../components/BaseToast.vue';

const authStore = useAuthStore();
const route = useRoute();
const sidebarOpen = ref(true);
const toastRef = ref(null);

const navItems = [
  { path: '/habitaciones', label: 'Habitaciones', icon: '🛏️' },
  { path: '/reservas', label: 'Reservas', icon: '📋' },
  { path: '/huespedes', label: 'Huéspedes', icon: '👥' },
  { path: '/recepcion', label: 'Recepción', icon: '🔑' },
  { path: '/facturacion', label: 'Facturación', icon: '🧾' },
  { path: '/servicios', label: 'Servicios', icon: '🍽️' },
  { path: '/reportes', label: 'Reportes', icon: '📊', role: 'gerente' },
];

const pageTitles = {
  '/habitaciones': 'Habitaciones',
  '/reservas': 'Reservas',
  '/huespedes': 'Huéspedes',
  '/recepcion': 'Recepción / Check-in / Check-out',
  '/facturacion': 'Facturación',
  '/servicios': 'Servicios Adicionales',
  '/reportes': 'Reportes Estratégicos',
};

const currentPageTitle = computed(() => {
  for (const key of Object.keys(pageTitles)) {
    if (route.path.startsWith(key)) return pageTitles[key];
  }
  return 'HotelBook Pro';
});

const userInitial = computed(() => {
  const name = authStore.user?.nombre || '';
  return name.charAt(0).toUpperCase();
});

const formattedDate = computed(() => {
  return new Date().toLocaleDateString('es-CO', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
});

provide('toast', toastRef);
</script>
