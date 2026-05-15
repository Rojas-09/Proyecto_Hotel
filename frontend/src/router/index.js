import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '../stores/auth';

import MainLayout from '../layouts/MainLayout.vue';
import LoginView from '../views/LoginView.vue';
import HabitacionesView from '../views/HabitacionesView.vue';
import ReservasView from '../views/ReservasView.vue';
import HuespedesView from '../views/HuespedesView.vue';
import CheckInOutView from '../views/CheckInOutView.vue';
import FacturacionView from '../views/FacturacionView.vue';
import ReportesView from '../views/ReportesView.vue';
import ServiciosView from '../views/ServiciosView.vue';

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: LoginView,
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: MainLayout,
    meta: { requiresAuth: true },
    children: [
      { path: '', redirect: '/habitaciones' },
      { path: 'habitaciones', name: 'Habitaciones', component: HabitacionesView },
      { path: 'reservas', name: 'Reservas', component: ReservasView },
      { path: 'huespedes', name: 'Huespedes', component: HuespedesView },
      { path: 'recepcion', name: 'Recepcion', component: CheckInOutView },
      { path: 'facturacion', name: 'Facturacion', component: FacturacionView },
      { path: 'servicios', name: 'Servicios', component: ServiciosView },
      {
        path: 'reportes',
        name: 'Reportes',
        component: ReportesView,
        meta: { requiresAuth: true, roles: ['gerente', 'admin'] }
      },
    ]
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore();

  // Ruta requiere auth y usuario no autenticado → login
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return next('/login');
  }

  // Usuario autenticado intenta ir a login
  if (!to.meta.requiresAuth && authStore.isAuthenticated && to.path === '/login') {
    return next('/habitaciones');
  }

  // Control de rol para rutas restringidas
  if (to.meta.roles && !to.meta.roles.includes(authStore.userRole)) {
    return next('/habitaciones');
  }

  next();
});

export default router;
