import React, { useState, useEffect, useCallback } from 'react';
import { Search, Bell, Shield, Activity, Command, Menu } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useNotifications } from '../../context/NotificationContext';
import { useNavigate } from 'react-router-dom';
import { CommandPalette } from './CommandPalette';

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

export function Topbar({ isCollapsed, toggleMobileSidebar }) {
  const { user } = useAuth();
  const { notifications, unreadCount, markRead, markAllRead } = useNotifications();
  const [showNotifications, setShowNotifications] = useState(false);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const navigate = useNavigate();

  // Global Ctrl+K / Cmd+K shortcut
  const handleGlobalKey = useCallback((e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      setPaletteOpen((v) => !v);
    }
  }, []);

  useEffect(() => {
    window.addEventListener('keydown', handleGlobalKey);
    return () => window.removeEventListener('keydown', handleGlobalKey);
  }, [handleGlobalKey]);

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return 'text-red-400';
      case 'high': return 'text-orange-400';
      case 'medium': return 'text-amber-400';
      case 'low': return 'text-blue-400';
      default: return 'text-cyan-400';
    }
  };

  // Limit dropdown to newest 5 items
  const dropdownItems = notifications.slice(0, 5);

  return (
    <header
      className={`fixed top-0 right-0 z-30 h-16 glass border-b border-slate-800/80 transition-all duration-300 flex items-center justify-between px-4 md:px-6 ${isCollapsed ? 'lg:left-20 left-0' : 'lg:left-64 left-0'
        }`}
    >
      <button
        onClick={toggleMobileSidebar}
        className="md:hidden p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
      >
        <Menu size={20} />
      </button>
      {/* Command Palette Trigger */}
      <button
        onClick={() => setPaletteOpen(true)}
        className="hidden md:flex relative items-center gap-2.5 w-72 bg-slate-900/80 border border-slate-800 hover:border-cyan-500/40 rounded-lg pl-3 pr-3 py-1.5 text-xs text-slate-500 hover:text-slate-300 transition-all duration-200 group"
        title="Open Command Palette (Ctrl+K)"
      >
        <Search className="w-3.5 h-3.5 flex-shrink-0 group-hover:text-cyan-400 transition-colors" />
        <span className="flex-1 text-left truncate">Search or run a command…</span>
        <kbd className="flex items-center gap-0.5 px-1.5 py-0.5 text-[9px] rounded border border-slate-700/80 text-slate-600 font-mono group-hover:border-cyan-500/30 group-hover:text-slate-400 transition-colors">
          <Command className="w-2.5 h-2.5" />K
        </kbd>
      </button>

      {/* Command Palette Overlay */}
      <CommandPalette open={paletteOpen} onClose={() => setPaletteOpen(false)} />

      {/* Right Action Widgets */}
      <div className="flex items-center gap-2 md:gap-4">
        {/* System Health Pill */}
        <div className="hidden sm:flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium">
          <Activity className="w-3.5 h-3.5 animate-pulse" />
          <span>Engine Live</span>
        </div>

        {/* Notifications Dropdown */}
        <div className="relative">
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="relative p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 transition-colors"
          >
            <Bell size={18} />
            {unreadCount > 0 && (
              <>
                <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-red-500 animate-ping" />
                <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-red-500" />
              </>
            )}
          </button>

          {showNotifications && (
            <div className="absolute right-0 mt-2 w-80 glass rounded-xl shadow-2xl border border-slate-800 p-3 z-50 animate-fade-in-up">
              <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800">
                <span className="text-xs font-semibold text-slate-200 uppercase tracking-wider">Live Alerts</span>
                {unreadCount > 0 && (
                  <span
                    onClick={() => markAllRead()}
                    className="text-[10px] text-cyan-400 hover:text-cyan-300 cursor-pointer transition-colors"
                  >
                    Mark all read
                  </span>
                )}
              </div>

              <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                {dropdownItems.length === 0 ? (
                  <div className="text-center py-6 text-slate-500 text-xs">
                    No new alerts.
                  </div>
                ) : (
                  dropdownItems.map(n => {
                    const id = n._id || n.id;
                    return (
                      <div
                        key={id}
                        onClick={() => {
                          if (!n.is_read) {
                            markRead(id);
                          }
                          if (n.action_url) {
                            navigate(n.action_url);
                            setShowNotifications(false);
                          }
                        }}
                        className={`p-2.5 rounded-lg transition-all duration-300 border cursor-pointer ${n.is_read
                          ? 'bg-slate-950/40 border-slate-900/60 opacity-60'
                          : 'bg-slate-900/80 hover:bg-slate-800/80 border-slate-800/60 shadow-md shadow-slate-950/20'
                          }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className={`text-xs font-semibold ${getSeverityColor(n.severity)}`}>
                            {n.title}
                          </span>
                          <span className="text-[10px] text-slate-500">{formatRelativeTime(n.created_at)}</span>
                        </div>
                        <p className="text-[11px] text-slate-400 mt-1 line-clamp-2">{n.message}</p>
                        {n.action_required && !n.is_read && (
                          <div className="mt-1.5 flex items-center justify-end">
                            <span className="px-1.5 py-0.5 rounded text-[8px] font-bold bg-amber-500/10 border border-amber-500/30 text-amber-400 uppercase tracking-widest">
                              Action Required
                            </span>
                          </div>
                        )}
                      </div>
                    );
                  })
                )}
              </div>

              <div className="mt-2 pt-2 border-t border-slate-800 text-center">
                <button
                  onClick={() => {
                    navigate('/notifications');
                    setShowNotifications(false);
                  }}
                  className="text-xs text-cyan-400 hover:text-cyan-300 font-medium transition-colors"
                >
                  View All Notifications
                </button>
              </div>
            </div>
          )}
        </div>

        {/* User Profile Pill */}
        <div className="flex items-center gap-2 md:gap-3 pl-2 md:pl-3 border-l border-slate-800">
          <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 font-bold text-xs">
            {user?.full_name ? user.full_name.charAt(0) : 'A'}
          </div>
          <div className="hidden md:flex flex-col">
            <span className="text-xs font-semibold text-slate-200">{user?.full_name || 'Fraud Analyst'}</span>
            <span className="text-[10px] text-slate-400 flex items-center gap-1">
              <Shield size={10} className="text-cyan-400" /> {user?.role || 'Analyst'}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}
