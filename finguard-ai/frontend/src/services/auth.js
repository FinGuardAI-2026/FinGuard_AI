import api from './api';

export const authService = {
  async login(email, password) {
    try {
      const response = await api.post('/api/v1/auth/login', {
        email,
        password
      });

      const {
        access_token,
        refresh_token,
        user
      } = response.data;

      localStorage.setItem('finguard_token', access_token);
      localStorage.setItem('finguard_refresh_token', refresh_token);
      localStorage.setItem('finguard_user', JSON.stringify(user));
      // console.log("TOKEN SAVED:", localStorage.getItem("finguard_token"));

      return {
        user,
        token: access_token
      };
    } catch (error) {
      throw error;
    }
  },

  async getCurrentUser() {
    try {
      const response = await api.get('/api/v1/auth/me');
      return response.data;
    } catch {
      const cached = localStorage.getItem('finguard_user');
      if (cached) return JSON.parse(cached);
      return null;
    }
  },

  logout() {
    localStorage.removeItem('finguard_token');
    localStorage.removeItem('finguard_refresh_token');
    localStorage.removeItem('finguard_user');
  }
};
