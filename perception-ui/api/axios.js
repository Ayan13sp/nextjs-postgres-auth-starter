import axios from 'axios';
import { useAuthStore } from '@/store/auth';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000',
});

api.interceptors.request.use(
  (config) => {
    const user = useAuthStore.getState().user;
    if (user && user.id) {
      config.headers['x-user-id'] = user.id;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export default api;