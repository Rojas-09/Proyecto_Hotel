import { defineStore } from 'pinia';
import router from '../router';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: JSON.parse(localStorage.getItem('user')) || null,
  }),
  getters: {
    isAuthenticated: (state) => !!state.user,
    userRole: (state) => (state.user ? state.user.rol : null),
  },
  actions: {
    login(user) {
      this.user = user;
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
        this.user = null;
        localStorage.removeItem('user');
      }
    },
    hasRole(role) {
      return this.userRole === role;
    },
  },
});
