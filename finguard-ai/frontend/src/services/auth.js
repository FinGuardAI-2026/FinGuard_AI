import api from './api';

export const authService = {
  async login(email, password) {
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

    return {
      user,
      token: access_token
    };
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

  async logout() {
    try {
      await api.post('/api/v1/auth/logout');
    } catch (err) {
      console.warn('Backend session cleanup failed:', err);
    }
    localStorage.removeItem('finguard_token');
    localStorage.removeItem('finguard_refresh_token');
    localStorage.removeItem('finguard_user');
  },

  async getAccountCenter() {
    const response = await api.get('/api/v1/auth/profile/center');
    return response.data;
  },

  async updateProfileDetails(payload) {
    const response = await api.patch('/api/v1/auth/profile', payload);
    localStorage.setItem('finguard_user', JSON.stringify(response.data));
    return response.data;
  },

  async revokeSession(sessionId) {
    const response = await api.post(`/api/v1/auth/sessions/${sessionId}/revoke`);
    return response.data;
  },

  async revokeAllSessions() {
    const response = await api.post('/api/v1/auth/sessions/revoke-all');
    return response.data;
  },

  async changePassword(oldPassword, newPassword) {
    const response = await api.post('/api/v1/auth/change-password', {
      old_password: oldPassword,
      new_password: newPassword
    });
    return response.data;
  }
};
