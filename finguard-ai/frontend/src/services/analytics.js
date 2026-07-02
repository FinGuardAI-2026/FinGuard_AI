import api from './api';

export const analyticsService = {
  async getDashboardStats() {
    const { data } = await api.get('/api/v1/analytics/dashboard');

    return {
      totalTransactions: data.total_transactions,
      fraudTransactions: data.fraud_transactions,
      fraudPercentage: data.fraud_percentage,

      pendingCases: data.pending_cases,
      criticalCases: data.risk_distribution.critical,

      riskDistribution: {
        low: data.risk_distribution.low,
        medium: data.risk_distribution.medium,
        high: data.risk_distribution.high,
        critical: data.risk_distribution.critical,
      },

      totalTransactionsChange:
        `${data.transaction_change >= 0 ? '+' : ''}${data.transaction_change}%`,
      fraudTransactionsChange:
        `${data.fraud_transaction_change >= 0 ? "+" : ""}${data.fraud_transaction_change}%`,
      fraudPercentageChange:
        `${data.fraud_percentage_change >= 0 ? "+" : ""}${data.fraud_percentage_change}%`,
    };
  },

  async getFraudTrendData() {
    const { data } = await api.get('/api/v1/analytics/fraud-trend');
    return data;
  },

  async getRiskTrendData() {
    const { data } = await api.get('/api/v1/analytics/risk-trend');
    return data;
  },

  async getCountryDistribution() {
    const { data } = await api.get('/api/v1/analytics/country-distribution');
    return data;
  },

  async getPaymentMethodData() {
    const { data } = await api.get('/api/v1/analytics/payment-methods');
    return data;
  },

  async getMerchantCategoryData() {
    const { data } = await api.get('/api/v1/analytics/merchant-categories');
    return data;
  },

  async getLiveAlerts() {
    const { data } = await api.get('/api/v1/analytics/live-alerts');
    return data;
  },

  async getModelComparisonData() {
    const { data } = await api.get("/api/v1/analytics/model-performance");

    return data.map(item => ({
        metric: item.model.toUpperCase(),
        Accuracy: +(item.accuracy * 100).toFixed(2),
        Precision: +(item.precision * 100).toFixed(2),
        Recall: +(item.recall * 100).toFixed(2),
        F1: +(item.f1 * 100).toFixed(2),
        ROC_AUC: +(item.roc_auc * 100).toFixed(2),

        training_time_s: item.training_time_s,
        inference_time_per_sample_ms: item.inference_time_per_sample_ms

    }));
  },

  async getSHAPGlobalImportance() {
    const { data } = await api.get("/api/v1/analytics/shap/global");
    return data;
  },

  async getInvestigationReport(transactionId) {
    const { data } = await api.get(
      `/api/v1/reports/transaction/${transactionId}`
    );
    return data;
  }
};
