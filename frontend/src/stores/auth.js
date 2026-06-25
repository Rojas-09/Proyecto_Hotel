import { defineStore } from 'pinia';
import router from '../router';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: JSON.parse(localStorage.getItem('user') || 'null'),
    _ready: false,
  }),
  getters: {
    isAuthenticated: (state) => !!state.user,
    userRole: (state) => (state.user ? state.user.rol : null),
    ready: (state) => state._ready,
  },
  actions: {
    login(user) {
      this.user = user;
      this._ready = true;
      localStorage.setItem('user', JSON.stringify(user));
    },
    async logout() {
      const api = (await import('../services/api')).default;
      try {
        await api.post('/auth/logout');
      } catch {
        // cerrar sesión aunque falle el endpoint
      }
      this.user = null;
      this._ready = true;
      localStorage.removeItem('user');
      router.push('/login');
    },
    async checkAuth() {
      const api = (await import('../services/api')).default;
      try {
        const res = await api.get('/auth/me');
        this.user = res.data.data.usuario;
        localStorage.setItem('user', JSON.stringify(this.user));
      } catch {
        // Intentar refresh antes de cerrar sesión
        try {
          await api.post('/auth/refresh', {}, { withCredentials: true });
          const res = await api.get('/auth/me');
          this.user = res.data.data.usuario;
          localStorage.setItem('user', JSON.stringify(this.user));
        } catch {
          this.user = null;
          localStorage.removeItem('user');
        }
      } finally {
        this._ready = true;
      }
    },
    hasRole(role) {
      return this.userRole === role;
    },
  },
});
