import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  BrainCircuit,
  Receipt,
  BarChart3,
  FileText,
  Settings,
  User,
  ShieldAlert,
  ChevronLeft,
  ChevronRight,
  LogOut,
  Bell
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useNotifications } from '../../context/NotificationContext';

export function Sidebar({ isCollapsed, toggleSidebar, mobileOpen, closeMobileSidebar }) {
  const { user, logout } = useAuth();
  const { unreadCount } = useNotifications();
  const isAdmin = user?.role === 'Admin';

  const mainNav = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'AI Prediction', path: '/prediction', icon: BrainCircuit },
    { name: 'Transactions', path: '/transactions', icon: Receipt },
    { name: 'Analytics', path: '/analytics', icon: BarChart3 },
    { name: 'Gemini Reports', path: '/reports', icon: FileText },
    { name: 'Notifications', path: '/notifications', icon: Bell },
  ];

  const secondaryNav = [
    { name: 'Settings', path: '/settings', icon: Settings },
    { name: 'Profile', path: '/profile', icon: User },
  ];

  return (
    <aside
      className={`
      fixed top-0 left-0 z-40 h-screen glass border-r border-slate-800/80
      transition-all duration-300 flex flex-col justify-between
      ${isCollapsed ? "lg:w-20" : "lg:w-64"}
      w-64
      ${mobileOpen ? "translate-x-0" : "-translate-x-full"}
      lg:translate-x-0
      `}
    >
      {/* Brand Header */}
      <div>
        <div className="flex items-center justify-between h-16 px-4 border-b border-slate-800/80">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-500/20 flex-shrink-0">
              <ShieldAlert className="w-6 h-6 text-slate-950" />
            </div>
            {(!isCollapsed || mobileOpen) && (
              <div className="flex flex-col">
                <span className="font-bold text-base tracking-wide text-slate-100 font-mono">FinGuard <span className="text-cyan-400">AI</span></span>
                <span className="text-[10px] uppercase tracking-widest text-slate-400 font-semibold">Enterprise Risk</span>
              </div>
            )}
          </div>
          <button
            onClick={toggleSidebar}
            className="hidden lg:block p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
          >
            {isCollapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
          </button>
        </div>

        {/* Main Navigation */}
        <div className="p-3 space-y-1">
          {(!isCollapsed || mobileOpen) && (
            <div className="px-3 py-2 text-[10px] font-semibold uppercase tracking-widest text-slate-500">
              Core Engine
            </div>
          )}
          {mainNav.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={() => {
                  if (closeMobileSidebar) closeMobileSidebar();
                }}
                className={({ isActive }) =>
                  `sidebar-link relative ${isActive ? 'active' : ''} ${isCollapsed ? 'justify-center px-0' : ''}`
                }
                title={isCollapsed ? item.name : undefined}
              >
                <Icon size={20} className="flex-shrink-0" />
                {(!isCollapsed || mobileOpen) && <span>{item.name}</span>}
                {item.path === '/notifications' && unreadCount > 0 && (
                  <span className={`flex items-center justify-center rounded-full bg-red-500 font-bold text-slate-950 leading-none ${isCollapsed ? 'absolute top-1 right-2 w-4.5 h-4.5 text-[8px]' : 'ml-auto w-5 h-5 text-[10px]'
                    }`}>
                    {unreadCount}
                  </span>
                )}
              </NavLink>
            );
          })}

          {/* Admin Panel Link */}
          {isAdmin && (
            <>
              {(!isCollapsed || mobileOpen) && (
                <div className="px-3 pt-4 pb-2 text-[10px] font-semibold uppercase tracking-widest text-amber-400/80">
                  Governance
                </div>
              )}
              <NavLink
                to="/admin"
                onClick={() => {
                  if (closeMobileSidebar) closeMobileSidebar();
                }}
                className={({ isActive }) =>
                  `sidebar-link ${isActive
                    ? "active text-amber-400 bg-amber-500/10 border-amber-400"
                    : "text-amber-400/70 hover:text-amber-300"
                  } ${isCollapsed ? "justify-center px-0" : ""}`
                }
                title={isCollapsed ? "Admin Panel" : undefined}
              >
                <ShieldAlert size={20} className="flex-shrink-0" />
                {(!isCollapsed || mobileOpen) && <span>Admin Panel</span>}
              </NavLink>
            </>
          )}
        </div>
      </div>

      {/* Footer / Account */}
      <div className="p-3 border-t border-slate-800/80 space-y-1">
        {(!isCollapsed || mobileOpen) && (
          <div className="px-3 py-1 text-[10px] font-semibold uppercase tracking-widest text-slate-500">
            System
          </div>
        )}
        {secondaryNav.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={() => {
                if (closeMobileSidebar) closeMobileSidebar();
              }}
              className={({ isActive }) =>
                `sidebar-link ${isActive ? 'active' : ''} ${isCollapsed ? 'justify-center px-0' : ''}`
              }
              title={isCollapsed ? item.name : undefined}
            >
              <Icon size={20} className="flex-shrink-0" />
              {(!isCollapsed || mobileOpen) && <span>{item.name}</span>}
            </NavLink>
          );
        })}

        <button
          onClick={() => {
            logout();
            if (closeMobileSidebar) closeMobileSidebar();
          }} className={`sidebar-link w-full text-red-400 hover:bg-red-500/10 hover:text-red-300 ${isCollapsed ? 'justify-center px-0' : ''}`}
          title={isCollapsed ? 'Logout' : undefined}
        >
          <LogOut size={20} className="flex-shrink-0" />
          {(!isCollapsed || mobileOpen) && <span>Logout</span>}
        </button>
      </div>
    </aside>
  );
}
