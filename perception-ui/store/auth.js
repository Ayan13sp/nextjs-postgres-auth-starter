import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import api from '@/api/axios';

export const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      isLoading: true,
      error: null,
      
      login: async (values) => {
        set({ isLoading: true, error: null });
        try {
          const response = await api.post('/auth/login', values);
          
          set({
            user: response.data,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          set({
            error: error.response?.data?.detail || 'Login failed',
            isLoading: false,
            isAuthenticated: false,
            user: null,
          });
          throw error;
        }
      },

      logout: () => {
        set({ user: null, isAuthenticated: false });
      },
      
      checkAuth: () => {
        const user = get().user;
        if (user) {
          set({ isAuthenticated: true, isLoading: false });
        } else {
          set({ isLoading: false });
        }
      },
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => localStorage),
    }
  )
);
