import api from './api';

export const predictionService = {
  async predict(payload) {
    const response = await api.post('/api/v1/predict', payload);
    return response.data;
  },

  async getHealth() {
    const response = await api.get('/api/v1/predict/health');
    return response.data;
  }
};
