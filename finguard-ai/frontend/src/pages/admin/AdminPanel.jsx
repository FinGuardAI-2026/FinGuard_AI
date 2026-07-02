import React, { useState } from 'react';
import { DashboardLayout } from '../../layouts/DashboardLayout';
import { ManageUsers } from './ManageUsers';
import { AuditLogs } from './AuditLogs';
import { SystemHealth } from './SystemHealth';
import { ShieldAlert, Users, FileText, Activity } from 'lucide-react';

export function AdminPanel() {
  const [activeTab, setActiveTab] = useState('users');

  const tabs = [
    { id: 'users', label: 'Manage Users', icon: Users },
    { id: 'logs', label: 'Audit Logs', icon: FileText },
    { id: 'health', label: 'System & Model Health', icon: Activity },
  ];

  return (
    <DashboardLayout>
      <div className="pb-2 border-b border-slate-800 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-6 h-6 text-amber-400" />
            <h1 className="text-2xl font-bold text-slate-100 tracking-tight">System Governance & Admin Panel</h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Privileged administrative control center for user access, audit compliance, and system health.
          </p>
        </div>
      </div>

      {/* Admin Sub-tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
        {tabs.map(tab => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition-all ${
                isActive
                  ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30 shadow-lg shadow-amber-500/10'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <Icon size={16} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab Panel Render */}
      <div className="mt-4 animate-fade-in">
        {activeTab === 'users' && <ManageUsers />}
        {activeTab === 'logs' && <AuditLogs />}
        {activeTab === 'health' && <SystemHealth />}
      </div>
    </DashboardLayout>
  );
}
