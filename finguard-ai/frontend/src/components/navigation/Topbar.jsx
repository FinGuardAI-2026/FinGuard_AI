import React, { useState } from 'react';
import { Search, Bell, Shield, Activity, User as UserIcon } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useNavigate } from 'react-router-dom';

export function Topbar({ isCollapsed }) {
  const { user } = useAuth();
  const [showNotifications, setShowNotifications] = useState(false);
  const [search, setSearch] = useState('');

  const notifications = [
    { id: 1, title: 'Critical Risk Alert', desc: 'Transaction TXN-8821 flagged with 91.5 risk score.', time: '2m ago', type: 'critical' },
    { id: 2, title: 'Model Updated', desc: 'Champion XGBoost re-indexing finalized.', time: '1h ago', type: 'info' },
    { id: 3, title: 'High Velocity Detected', desc: 'Device DEV-9941 generated 12 rapid checks.', time: '3h ago', type: 'warning' },
  ];

  return (
    <header
      className={`fixed top-0 right-0 z-30 h-16 glass border-b border-slate-800/80 transition-all duration-300 flex items-center justify-between px-6 ${isCollapsed ? 'left-20' : 'left-64'
        }`}
    >
      {/* Search Bar */}
      <div className="relative w-72">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 w-4 h-4" />
        <input
          type="text"
          placeholder="Global Search (Coming Soon)"
          className="w-full bg-slate-900/80 border border-slate-800 rounded-lg pl-9 pr-4 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 transition-colors cursor-not-allowed opacity-60"
          disabled
        />
      </div>

      {/* Right Action Widgets */}
      <div className="flex items-center gap-4">
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
            <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-red-500 animate-ping" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-red-500" />
          </button>

          {showNotifications && (
            <div className="absolute right-0 mt-2 w-80 glass rounded-xl shadow-2xl border border-slate-800 p-3 z-50 animate-fade-in-up">
              <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800">
                <span className="text-xs font-semibold text-slate-200 uppercase tracking-wider">Live Alerts</span>
                <span className="text-[10px] text-cyan-400 cursor-pointer">Mark all read</span>
              </div>
              <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                {notifications.map(n => (
                  <div key={n.id} className="p-2.5 rounded-lg bg-slate-900/60 hover:bg-slate-800/80 transition-colors border border-slate-800/60">
                    <div className="flex items-center justify-between">
                      <span className={`text-xs font-semibold ${n.type === 'critical' ? 'text-red-400' : n.type === 'warning' ? 'text-amber-400' : 'text-cyan-400'}`}>
                        {n.title}
                      </span>
                      <span className="text-[10px] text-slate-500">{n.time}</span>
                    </div>
                    <p className="text-[11px] text-slate-400 mt-1">{n.desc}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* User Profile Pill */}
        <div className="flex items-center gap-3 pl-3 border-l border-slate-800">
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
