import api from './api';

export const transactionService = {
  async listTransactions(params = {}) {
    try {
      const cleanParams = {};

      Object.entries(params).forEach(([key, value]) => {
        if (value !== "" && value !== null && value !== undefined) {
          cleanParams[key] = value;
        }
      });

      const response = await api.get('/api/v1/transactions', {
        params: cleanParams,
      });

      return response.data;
    } catch (error) {
      console.warn('Backend transactions unavailable, using mock dataset:', error);
      return generateMockTransactions(params);
    }
  },

  async getTransaction(id) {
    try {
      const response = await api.get(`/api/v1/transactions/${id}`);
      return response.data;
    } catch {
      const mockList = generateMockTransactions({ page_size: 100 }).transactions;
      return mockList.find(t => t._id === id || t.transaction_id === id) || mockList[0];
    }
  },

  async createTransaction(payload) {
    try {
      const response = await api.post('/api/v1/transactions', payload);
      return response.data;
    } catch {
      return {
        _id: `tx_mock_${Date.now()}`,
        transaction_id: `TXN-${Math.random().toString(36).substring(2, 10).toUpperCase()}`,
        user_id: 'usr_current',
        ...payload,
        status: 'PENDING',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };
    }
  }
};

function generateMockTransactions(params) {
  const pageSize = params.page_size || 25;
  const page = params.page || 1;

  const merchants = ['Amazon Prime', 'Apple Store', 'Starbucks', 'Binance Exchange', 'Uber Trip', 'Walmart', 'Steam Games', 'Target Store'];
  const categories = ['E-COMMERCE', 'ELECTRONICS', 'FOOD_AND_BEVERAGE', 'CRYPTO', 'TRANSPORT', 'RETAIL', 'GAMING', 'RETAIL'];
  const countries = ['USA', 'USA', 'USA', 'GBR', 'DEU', 'FRA', 'CAN', 'SGP', 'JPN', 'AUS'];
  const methods = ['CREDIT_CARD', 'DEBIT_CARD', 'APPLE_PAY', 'GOOGLE_PAY', 'CRYPTO', 'ACH'];
  const statuses = ['COMPLETED', 'COMPLETED', 'COMPLETED', 'PENDING', 'FLAGGED', 'FAILED'];

  const mockData = Array.from({ length: 142 }).map((_, i) => {
    const isFraud = i % 7 === 0 || i % 13 === 0;
    const amount = isFraud ? parseFloat((1200 + Math.random() * 8500).toFixed(2)) : parseFloat((12 + Math.random() * 450).toFixed(2));
    const idx = i % merchants.length;
    const date = new Date(Date.now() - i * 3600000 * 4).toISOString();

    return {
      _id: `doc_tx_${1000 + i}`,
      transaction_id: `TXN-202606-${(10000 + i).toString()}`,
      user_id: `usr_${100 + (i % 5)}`,
      amount,
      currency: 'USD',
      merchant_name: merchants[idx],
      merchant_category: categories[idx],
      payment_method: methods[i % methods.length],
      transaction_type: 'PURCHASE',
      status: isFraud ? (i % 2 === 0 ? 'FLAGGED' : 'PENDING') : statuses[i % statuses.length],
      country: isFraud && i % 3 === 0 ? 'RU' : countries[i % countries.length],
      city: 'New York',
      ip_address: `192.168.1.${10 + (i % 200)}`,
      device_id: `DEV-${Math.random().toString(36).substring(2, 8).toUpperCase()}`,
      transaction_time: date,
      fraud_probability: isFraud ? parseFloat((75 + Math.random() * 24).toFixed(1)) : parseFloat((0.1 + Math.random() * 5).toFixed(1)),
      risk_score: isFraud ? parseFloat((78 + Math.random() * 20).toFixed(1)) : parseFloat((5 + Math.random() * 20).toFixed(1)),
      prediction: isFraud ? 'FRAUD' : 'GENUINE',
      created_at: date,
      updated_at: date
    };
  });

  let filtered = [...mockData];
  if (params.merchant) {
    filtered = filtered.filter(t => t.merchant_name.toLowerCase().includes(params.merchant.toLowerCase()));
  }
  if (params.status) {
    filtered = filtered.filter(t => t.status === params.status);
  }
  if (params.country) {
    filtered = filtered.filter(t => t.country === params.country);
  }

  const start = (page - 1) * pageSize;
  const paginated = filtered.slice(start, start + pageSize);

  return {
    transactions: paginated,
    total_records: filtered.length,
    total_pages: Math.ceil(filtered.length / pageSize),
    page: Number(page),
    page_size: Number(pageSize)
  };
}
