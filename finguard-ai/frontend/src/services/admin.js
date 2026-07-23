import api from './api';

export const adminService = {
  /**
   * Fetch all active (non-soft-deleted) users
   */
  async listUsers() {
    const response = await api.get('/api/v1/admin/users');
    return response.data;
  },

  /**
   * Create a new investigator user account
   */
  async createUser(payload) {
    const response = await api.post('/api/v1/admin/users', payload);
    return response.data;
  },

  /**
   * Update an investigator user account
   */
  async editUser(userId, payload) {
    const response = await api.patch(`/api/v1/admin/users/${userId}`, payload);
    return response.data;
  },

  /**
   * Soft-delete a user
   */
  async deleteUser(userId) {
    const response = await api.delete(`/api/v1/admin/users/${userId}`);
    return response.data;
  },

  /**
   * Bulk status change (suspend/activate)
   */
  async bulkStatusUpdate(userIds, isActive) {
    const response = await api.post('/api/v1/admin/users/bulk-status', {
      user_ids: userIds,
      is_active: isActive
    });
    return response.data;
  },

  /**
   * Bulk soft-delete users
   */
  async bulkDelete(userIds) {
    const response = await api.post('/api/v1/admin/users/bulk-delete', {
      user_ids: userIds
    });
    return response.data;
  },

  /**
   * Reset a user's password
   */
  async resetPassword(userId, password) {
    const response = await api.post(`/api/v1/admin/users/${userId}/reset-password`, {
      password
    });
    return response.data;
  },

  /**
   * List paginated & filterable audit logs
   */
  async listAuditLogs(params = {}) {
    const response = await api.get('/api/v1/admin/audit-logs', { params });
    return response.data;
  },

  /**
   * Get system health and telemetry variables
   */
  async getSystemTelemetry() {
    const response = await api.get('/api/v1/admin/system/telemetry');
    return response.data;
  },

  /**
   * Get Permission Matrix
   */
  async getPermissionMatrix() {
    const response = await api.get('/api/v1/admin/permissions');
    return response.data;
  },

  /**
   * Update Permission Matrix
   */
  async updatePermissionMatrix(matrix) {
    const response = await api.put('/api/v1/admin/permissions', { matrix });
    return response.data;
  },

  /**
   * Fetch admin governance notifications
   */
  async getAdminNotifications() {
    const response = await api.get('/api/v1/admin/notifications');
    return response.data;
  },

  /**
   * Revoke a specific user device session
   */
  async revokeUserSession(userId, sessionId) {
    const response = await api.post(`/api/v1/admin/users/${userId}/sessions/${sessionId}/revoke`);
    return response.data;
  },

  async getActivityTrend() {
    const response = await api.get('/api/v1/admin/activity-trend');
    return response.data;
  },

  async getBrowserDistribution() {
    const response = await api.get('/api/v1/admin/browser-distribution');
    return response.data;
  },
};
