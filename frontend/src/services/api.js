import axios from 'axios';
import { useAuthStore } from '../stores/auth';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

let isRefreshing = false;
let pendingRequests = [];

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response && error.response.status === 401 && !originalRequest._retry) {
      if (originalRequest.url === '/auth/refresh') {
        const authStore = useAuthStore();
        authStore.logout();
        return Promise.reject(error);
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          pendingRequests.push({ resolve, reject, error });
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        await axios.post(
          `${api.defaults.baseURL}/auth/refresh`,
          {},
          { withCredentials: true },
        );
        isRefreshing = false;
        pendingRequests.forEach((p) => p.resolve(api(p.error.config)));
        pendingRequests = [];
        return api(originalRequest);
      } catch {
        isRefreshing = false;
        pendingRequests = [];
        const authStore = useAuthStore();
        authStore.logout();
        return Promise.reject(error);
      }
    }

    return Promise.reject(error);
  },
);

export default api;
