import React, { useState, useMemo } from 'react';
import { DashboardLayout } from '../layouts/DashboardLayout';
import { Card, Button, Badge } from '../components/ui';
import { useNotifications } from '../context/NotificationContext';
import { useNavigate } from 'react-router-dom';
import {
  Bell,
  CheckCheck,
  Trash2,
  // AlertTriangle,
  FileText,
  User,
  ShieldAlert,
  Activity,
  LogIn,
  LogOut,
  Key,
  UserCheck,
  Settings,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

// Relative Time Helper
function formatRelativeTime(dateString) {
  if (!dateString) return '';
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now - date;
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHr = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHr / 24);

  if (diffSec < 60) return 'just now';
  if (diffMin < 60) return `${diffMin}m ago`;
  if (diffHr < 24) return `${diffHr}h ago`;
  if (diffDay === 1) return 'yesterday';
  return `${diffDay}d ago`;
}

// Icon mapper for notification types
const getNotificationIcon = (type) => {
  switch (type) {
    case 'fraud_alert':
      return <ShieldAlert className="w-5 h-5 text-red-400" />;
    case 'report':
      return <FileText className="w-5 h-5 text-cyan-400" />;
    case 'system':
      return <Activity className="w-5 h-5 text-violet-400" />;
    case 'user_registered':
      return <UserCheck className="w-5 h-5 text-emerald-400" />;
    case 'auth_login':
      return <LogIn className="w-5 h-5 text-blue-400" />;
    case 'auth_logout':
      return <LogOut className="w-5 h-5 text-slate-400" />;
    case 'auth_password_change':
      return <Key className="w-5 h-5 text-amber-400" />;
    case 'profile_update':
      return <User className="w-5 h-5 text-indigo-400" />;
    case 'role_change':
      return <ShieldAlert className="w-5 h-5 text-orange-400" />;
    default:
      return <Bell className="w-5 h-5 text-cyan-400" />;
  }
};

const getSeverityStyles = (severity) => {
  switch (severity) {
    case 'critical':
      return 'border-l-4 border-l-red-500 bg-red-950/10';
    case 'high':
      return 'border-l-4 border-l-orange-500 bg-orange-950/10';
    case 'medium':
      return 'border-l-4 border-l-amber-500 bg-amber-950/10';
    case 'low':
      return 'border-l-4 border-l-blue-500 bg-blue-950/10';
    default:
      return 'border-l-4 border-l-cyan-500/60 bg-slate-900/40';
  }
};

export function Notifications() {
  const {
    notifications,
    unreadCount,
    preferences,
    markRead,
    markAllRead,
    deleteNotification,
    clearRead,
    updatePreferences
  } = useNotifications();

  const [activeTab, setActiveTab] = useState('all');
  const [showPrefs, setShowPrefs] = useState(false);
  const navigate = useNavigate();

  // Tab Filtering
  const filteredNotifications = useMemo(() => {
    return notifications.filter(n => {
      if (activeTab === 'unread') return !n.is_read;
      if (activeTab === 'action_required') return n.action_required && !n.is_read;
      if (activeTab === 'fraud') return n.type === 'fraud_alert';
      if (activeTab === 'system') return n.type === 'system' || n.type === 'admin';
      return true; // 'all'
    });
  }, [notifications, activeTab]);

  // Date Grouping
  const groupedNotifications = useMemo(() => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    const sevenDaysAgo = new Date(today);
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);

    const groups = {
      today: [],
      yesterday: [],
      thisWeek: [],
      older: []
    };

    filteredNotifications.forEach(n => {
      const created = new Date(n.created_at);
      created.setHours(0, 0, 0, 0);

      if (created.getTime() === today.getTime()) {
        groups.today.push(n);
      } else if (created.getTime() === yesterday.getTime()) {
        groups.yesterday.push(n);
      } else if (created >= sevenDaysAgo) {
        groups.thisWeek.push(n);
      } else {
        groups.older.push(n);
      }
    });

    return groups;
  }, [filteredNotifications]);

  const handleTogglePref = (type) => {
    if (!preferences) return;
    const updatedSubscribed = preferences.subscribed_types.map(pref =>
      pref.type === type ? { ...pref, enabled: !pref.enabled } : pref
    );
    updatePreferences({
      ...preferences,
      subscribed_types: updatedSubscribed
    });
  };

  const tabs = [
    { id: 'all', label: 'All Alerts' },
    { id: 'unread', label: `Unread (${unreadCount})` },
    { id: 'action_required', label: 'Action Required' },
    { id: 'fraud', label: 'Fraud alerts' },
    { id: 'system', label: 'System & Admin' }
  ];

  return (
    <DashboardLayout>
      <div className="pb-2 border-b border-slate-800 flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Bell className="w-6 h-6 text-cyan-400" />
            <h1 className="text-2xl font-bold text-slate-100 tracking-tight">Notification Center</h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time feed of risk assessments, security alerts, and system health status.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-2 w-full lg:w-auto">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setShowPrefs(!showPrefs)}
            className="w-full sm:w-auto flex items-center justify-center gap-1.5 font-bold text-xs"
          >
            <Settings size={14} />
            <span>Preferences</span>
            {showPrefs ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </Button>

          {unreadCount > 0 && (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => markAllRead()}
              className="w-full sm:w-auto flex items-center justify-center gap-1.5 text-xs text-cyan-400 hover:text-cyan-300 font-bold"            >
              <CheckCheck size={14} />
              <span>Mark All Read</span>
            </Button>
          )}

          <Button
            variant="secondary"
            size="sm"
            onClick={() => clearRead()}
            className="w-full sm:w-auto flex items-center justify-center gap-1.5 text-xs text-red-400 hover:text-red-300 font-bold border-red-500/20 hover:bg-red-500/5"
          >
            <Trash2 size={14} />
            <span>Clear Read</span>
          </Button>
        </div>
      </div>

      {/* Preferences Section */}
      {showPrefs && preferences && (
        <Card
          title="Notification Preferences"
          subtitle="Configure alert delivery filters for your account"
          className="animate-fade-in border-cyan-500/20 bg-cyan-950/5"
        >
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            {preferences.subscribed_types.map(pref => (
              <label
                key={pref.type}
                className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 p-3 rounded-lg bg-slate-900/60 border border-slate-800 hover:border-slate-700/80 transition-colors cursor-pointer"
              >
                <span className="text-xs font-semibold text-slate-300">
                  {pref.label || pref.type.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())}
                </span>
                <input
                  type="checkbox"
                  checked={pref.enabled}
                  onChange={() => handleTogglePref(pref.type)}
                  className="rounded bg-slate-950 border-slate-800 accent-cyan-500 focus:ring-0 cursor-pointer h-4 w-4"
                />
              </label>
            ))}
          </div>
        </Card>
      )}

      {/* Filters & Content Tabs */}
      <div className="flex gap-2 border-b border-slate-800 pb-3 overflow-x-auto whitespace-nowrap">
        {tabs.map(tab => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 rounded-lg text-xs font-bold transition-all ${isActive
                ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 shadow-lg shadow-cyan-500/10'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Main Alerts Feed */}
      <div className="space-y-6">
        {filteredNotifications.length === 0 ? (
          <Card className="text-center py-12">
            <Bell className="w-12 h-12 text-slate-700 mx-auto mb-4 animate-bounce" />
            <h3 className="text-slate-300 font-bold text-sm">No Notifications Found</h3>
            <p className="text-slate-500 text-xs mt-1 max-w-xs mx-auto">
              Your feed is empty. No notifications match the selected filter category.
            </p>
          </Card>
        ) : (
          Object.keys(groupedNotifications).map(groupKey => {
            const groupList = groupedNotifications[groupKey];
            if (groupList.length === 0) return null;

            const groupTitle =
              groupKey === 'today'
                ? 'Today'
                : groupKey === 'yesterday'
                  ? 'Yesterday'
                  : groupKey === 'thisWeek'
                    ? 'This Week'
                    : 'Older';

            return (
              <div key={groupKey} className="space-y-3">
                <h3 className="text-[10px] uppercase font-bold tracking-widest text-slate-500 pl-1 border-l-2 border-slate-800">
                  {groupTitle}
                </h3>
                <div className="space-y-2">
                  {groupList.map(n => {
                    const id = n._id || n.id;
                    return (
                      <div
                        key={id}
                        className={`flex items-start justify-between p-4 rounded-xl transition-all duration-300 border ${getSeverityStyles(
                          n.severity
                        )} ${n.is_read
                          ? 'bg-slate-950/20 border-slate-900 opacity-60'
                          : 'bg-slate-900/60 border-slate-800/80 shadow-md shadow-slate-950/30 hover:border-slate-700'
                          }`}
                      >
                        <div className="flex gap-3">
                          <div className="mt-0.5 p-2 rounded-lg bg-slate-950/80 border border-slate-800">
                            {getNotificationIcon(n.type)}
                          </div>
                          <div>
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className="text-xs font-bold text-slate-200">
                                {n.title}
                              </span>
                              <span className="text-[10px] text-slate-500">
                                {formatRelativeTime(n.created_at)}
                              </span>
                              {n.action_required && !n.is_read && (
                                <Badge variant="warning" className="text-[8px] tracking-wide uppercase px-1 py-0 font-extrabold animate-pulse">
                                  Action Required
                                </Badge>
                              )}
                            </div>
                            <p className="text-[11px] text-slate-400 mt-1 max-w-2xl leading-relaxed">
                              {n.message}
                            </p>

                            {/* Action Button */}
                            {n.action_url && !n.is_read && (
                              <Button
                                variant="primary"
                                size="sm"
                                onClick={() => {
                                  markRead(id);
                                  navigate(n.action_url);
                                }}
                                className="mt-3 text-[10px] font-bold py-1 px-3"
                              >
                                View Details & Act
                              </Button>
                            )}
                          </div>
                        </div>

                        {/* Item Actions */}
                        <div className="flex justify-end sm:justify-start items-center gap-1.5">
                          {!n.is_read && (
                            <button
                              onClick={() => markRead(id)}
                              title="Mark read"
                              className="p-1.5 rounded-lg text-slate-500 hover:text-cyan-400 hover:bg-slate-800/80 transition-colors"
                            >
                              <CheckCheck size={14} />
                            </button>
                          )}
                          <button
                            onClick={() => deleteNotification(id)}
                            title="Delete"
                            className="p-1.5 rounded-lg text-slate-500 hover:text-red-400 hover:bg-slate-800/80 transition-colors"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })
        )}
      </div>
    </DashboardLayout>
  );
}
