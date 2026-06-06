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
import ClienteView from '../views/ClienteView.vue';

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
    meta: { requiresAuth: true, roles: ['admin', 'recepcionista', 'gerente', 'cliente'] },
    children: [
      { path: '', redirect: '/habitaciones' },
      { path: 'habitaciones', name: 'Habitaciones', component: HabitacionesView, meta: { roles: ['admin', 'recepcionista', 'gerente'] } },
      { path: 'reservas', name: 'Reservas', component: ReservasView, meta: { roles: ['admin', 'recepcionista', 'gerente'] } },
      { path: 'huespedes', name: 'Huespedes', component: HuespedesView, meta: { roles: ['admin', 'recepcionista'] } },
      { path: 'recepcion', name: 'Recepcion', component: CheckInOutView, meta: { roles: ['admin', 'recepcionista'] } },
      { path: 'facturacion', name: 'Facturacion', component: FacturacionView, meta: { roles: ['admin', 'recepcionista'] } },
      { path: 'servicios', name: 'Servicios', component: ServiciosView, meta: { roles: ['admin', 'recepcionista', 'gerente'] } },
      {
        path: 'reportes',
        name: 'Reportes',
        component: ReportesView,
        meta: { roles: ['gerente', 'admin'] }
      },
      { path: 'mi-panel', name: 'MiPanel', component: ClienteView, meta: { roles: ['cliente'] } },
    ]
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to, from) => {
  const authStore = useAuthStore();
  const dashboardRoles = ['admin', 'recepcionista', 'gerente', 'cliente'];
  const homeByRole = {
    admin: '/habitaciones',
    recepcionista: '/habitaciones',
    gerente: '/reportes',
    cliente: '/mi-panel',
  };

  // Ruta requiere auth y usuario no autenticado → login
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return '/login';
  }

  // Usuario autenticado intenta ir a login
  if (!to.meta.requiresAuth && authStore.isAuthenticated && to.path === '/login' && dashboardRoles.includes(authStore.userRole)) {
    return homeByRole[authStore.userRole];
  }

  const hasUnauthorizedRole = to.matched.some(
    route => route.meta?.roles && !route.meta.roles.includes(authStore.userRole)
  );
  if (hasUnauthorizedRole) {
    if (authStore.isAuthenticated && homeByRole[authStore.userRole]) {
      return homeByRole[authStore.userRole];
    }
    return '/login';
  }

  return true;
});

export default router;
