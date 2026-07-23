import api from './api';

export const notificationService = {
  /**
   * Fetches paginated notifications list.
   * Supports 'type' and 'unread_only' filtering.
   */
  async getNotifications({ limit = 20, offset = 0, unreadOnly = false, type = null } = {}) {
    const params = {
      limit,
      offset,
      unread_only: unreadOnly,
    };
    if (type) {
      params.type = type;
    }
    const response = await api.get('/api/v1/notifications/', { params });
    return response.data;
  },

  /**
   * Fast poll endpoint for the unread badge.
   */
  async getUnreadCount() {
    const response = await api.get('/api/v1/notifications/unread-count');
    return response.data;
  },

  /**
   * Marks a single notification as read.
   */
  async markRead(id) {
    const response = await api.patch(`/api/v1/notifications/${id}/read`);
    return response.data;
  },

  /**
   * Marks all notifications as read for the user.
   */
  async markAllRead() {
    const response = await api.patch('/api/v1/notifications/mark-all-read');
    return response.data;
  },

  /**
   * Marks multiple notifications as read.
   */
  async bulkMarkRead(ids) {
    const response = await api.patch('/api/v1/notifications/bulk-read', {
      notification_ids: ids,
    });
    return response.data;
  },

  /**
   * Deletes a single notification.
   */
  async deleteNotification(id) {
    const response = await api.delete(`/api/v1/notifications/${id}`);
    return response.data;
  },

  /**
   * Clears all read notifications.
   */
  async clearRead() {
    const response = await api.delete('/api/v1/notifications/clear-read');
    return response.data;
  },

  /**
   * Gets user notification preferences.
   */
  async getPreferences() {
    const response = await api.get('/api/v1/notifications/preferences');
    return response.data;
  },

  /**
   * Updates user notification preferences.
   */
  async updatePreferences(preferences) {
    const response = await api.put('/api/v1/notifications/preferences', preferences);
    return response.data;
  },
};
