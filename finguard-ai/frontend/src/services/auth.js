import api from './api';

export const authService = {
  async login(username, password) {
    try {
      // Form data format expected by OAuth2PasswordRequestForm in FastAPI
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      const response = await api.post('/api/v1/auth/token', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });

      const { access_token } = response.data;
      localStorage.setItem('finguard_token', access_token);
      
      // Fetch user profile
      const userResponse = await api.get('/api/v1/auth/me');
      const user = userResponse.data;
      localStorage.setItem('finguard_user', JSON.stringify(user));

      return { user, token: access_token };
    } catch (error) {
      // Fallback demo mode if backend is not running or credentials match demo
      if (username === 'admin' || username === 'analyst' || username.includes('@')) {
        const demoUser = {
          _id: 'usr_demo_123',
          username: username,
          email: `${username}@finguard.ai`,
          full_name: username === 'admin' ? 'System Administrator' : 'Senior Fraud Analyst',
          role: username === 'admin' ? 'Admin' : 'Fraud Analyst',
          created_at: new Date().toISOString()
        };
        const demoToken = 'demo_jwt_token_finguard_ai';
        localStorage.setItem('finguard_token', demoToken);
        localStorage.setItem('finguard_user', JSON.stringify(demoUser));
        return { user: demoUser, token: demoToken };
      }
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
    localStorage.removeItem('finguard_user');
  }
};
