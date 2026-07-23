import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useRef,
  useCallback
} from 'react';
import { notificationService } from '../services/notifications';
import { useAuth } from './AuthContext';

const NotificationContext = createContext(null);

export function NotificationProvider({ children }) {
  const { isAuthenticated } = useAuth();
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [preferences, setPreferences] = useState(null);
  
  const pollIntervalRef = useRef(null);

  // Helper: Fast fetch for unread count only (for polling)
  const fetchUnreadCount = useCallback(async () => {
    if (!isAuthenticated) return;
    try {
      const data = await notificationService.getUnreadCount();
      setUnreadCount(data.count);
    } catch (err) {
      console.error('Failed to poll unread count:', err);
    }
  }, [isAuthenticated]);

  // Helper: Full fetch of notifications
  const fetchNotifications = useCallback(async (params = {}) => {
    if (!isAuthenticated) return;
    setLoading(true);
    try {
      const data = await notificationService.getNotifications(params);
      setNotifications(data.notifications || []);
      setUnreadCount(data.unread_count || 0);
    } catch (err) {
      console.error('Failed to fetch notifications:', err);
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  // Helper: Fetch preferences
  const fetchPreferences = useCallback(async () => {
    if (!isAuthenticated) return;
    try {
      const data = await notificationService.getPreferences();
      setPreferences(data);
    } catch (err) {
      console.error('Failed to fetch notification preferences:', err);
    }
  }, [isAuthenticated]);

  // Set up polling and fetch on authentication state changes
  useEffect(() => {
    if (isAuthenticated) {
      fetchNotifications();
      fetchPreferences();

      // Poll unread count every 30 seconds
      pollIntervalRef.current = setInterval(fetchUnreadCount, 30000);
    } else {
      setNotifications([]);
      setUnreadCount(0);
      setPreferences(null);
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    }

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, [isAuthenticated, fetchNotifications, fetchPreferences, fetchUnreadCount]);

  // ── Optimistic Update Actions ──────────────────────────────────────────────

  const markRead = async (id) => {
    // Snapshot old state for rollback
    const prevNotifications = [...notifications];
    const prevUnreadCount = unreadCount;

    // Optimistically update local state
    setNotifications(prev =>
      prev.map(n => (n._id === id || n.id === id ? { ...n, is_read: true } : n))
    );
    setUnreadCount(prev => Math.max(0, prev - 1));

    try {
      await notificationService.markRead(id);
    } catch (err) {
      console.error('Failed to mark notification read, rolling back:', err);
      // Rollback on failure
      setNotifications(prevNotifications);
      setUnreadCount(prevUnreadCount);
    }
  };

  const markAllRead = async () => {
    const prevNotifications = [...notifications];
    const prevUnreadCount = unreadCount;

    // Optimistically update
    setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
    setUnreadCount(0);

    try {
      await notificationService.markAllRead();
    } catch (err) {
      console.error('Failed to mark all read, rolling back:', err);
      setNotifications(prevNotifications);
      setUnreadCount(prevUnreadCount);
    }
  };

  const bulkMarkRead = async (ids) => {
    const prevNotifications = [...notifications];
    const prevUnreadCount = unreadCount;

    // Optimistically update
    setNotifications(prev =>
      prev.map(n => (ids.includes(n._id) || ids.includes(n.id) ? { ...n, is_read: true } : n))
    );
    // Recalculate unread count from the list
    setUnreadCount(prev => {
      const readCount = ids.filter(id => {
        const item = prevNotifications.find(n => n._id === id || n.id === id);
        return item && !item.is_read;
      }).length;
      return Math.max(0, prev - readCount);
    });

    try {
      await notificationService.bulkMarkRead(ids);
    } catch (err) {
      console.error('Failed to bulk mark read, rolling back:', err);
      setNotifications(prevNotifications);
      setUnreadCount(prevUnreadCount);
    }
  };

  const deleteNotification = async (id) => {
    const prevNotifications = [...notifications];
    const prevUnreadCount = unreadCount;

    const targetedItem = notifications.find(n => n._id === id || n.id === id);
    const wasUnread = targetedItem ? !targetedItem.is_read : false;

    // Optimistically update
    setNotifications(prev => prev.filter(n => n._id !== id && n.id !== id));
    if (wasUnread) {
      setUnreadCount(prev => Math.max(0, prev - 1));
    }

    try {
      await notificationService.deleteNotification(id);
    } catch (err) {
      console.error('Failed to delete notification, rolling back:', err);
      setNotifications(prevNotifications);
      setUnreadCount(prevUnreadCount);
    }
  };

  const clearRead = async () => {
    const prevNotifications = [...notifications];

    // Optimistically update: filter out read notifications
    setNotifications(prev => prev.filter(n => !n.is_read));

    try {
      await notificationService.clearRead();
    } catch (err) {
      console.error('Failed to clear read notifications, rolling back:', err);
      setNotifications(prevNotifications);
    }
  };

  const updatePreferences = async (newPrefs) => {
    const prevPrefs = preferences;
    setPreferences(newPrefs);
    try {
      await notificationService.updatePreferences(newPrefs);
    } catch (err) {
      console.error('Failed to update preferences, rolling back:', err);
      setPreferences(prevPrefs);
    }
  };

  return (
    <NotificationContext.Provider
      value={{
        notifications,
        unreadCount,
        loading,
        preferences,
        fetchNotifications,
        fetchUnreadCount,
        markRead,
        markAllRead,
        bulkMarkRead,
        deleteNotification,
        clearRead,
        updatePreferences,
      }}
    >
      {children}
    </NotificationContext.Provider>
  );
}

export const useNotifications = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
};
