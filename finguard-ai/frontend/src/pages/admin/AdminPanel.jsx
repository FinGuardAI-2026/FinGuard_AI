import React, { useState, useEffect, useCallback } from 'react';
import { DashboardLayout } from '../../layouts/DashboardLayout';
import { ManageUsers } from './ManageUsers';
import { AuditLogs } from './AuditLogs';
import { SystemHealth } from './SystemHealth';
import { adminService } from '../../services/admin';
import { Card, Badge, Button, Spinner } from '../../components/ui';
import {
  ShieldAlert,
  Users,
  FileText,
  Activity,
  Key,
  LayoutDashboard,
  Bell,
  CheckCircle,
  Database,
  Cpu,
  RefreshCw,
  Info,
  AlertTriangle
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend
} from 'recharts';

const browserColors = {
  Chrome: "#06b6d4",
  Firefox: "#8b5cf6",
  Safari: "#3b82f6",
  Edge: "#f59e0b",
  Opera: "#ef4444",
  Unknown: "#64748b"
};

export function AdminPanel() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [telemetry, setTelemetry] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [loading, setLoading] = useState(true);
  const [matrix, setMatrix] = useState({});
  const [savingMatrix, setSavingMatrix] = useState(false);
  const [activityTrendData, setActivityTrendData] = useState([]);
  const [browserDistributionData, setBrowserDistributionData] = useState([]);

  // Default permissions mapping
  const availablePermissions = [
    { key: 'view_transactions', label: 'View Transactions telemetry' },
    { key: 'investigate_cases', label: 'Create & update case outcomes' },
    { key: 'view_analytics', label: 'View global fraud analytics charts' },
    { key: 'manage_users', label: 'Provision, suspend, reset, and delete user profiles' },
    { key: 'view_audit_logs', label: 'Access raw governance audit records' },
    { key: 'export_audit_logs', label: 'Export compliance logs (CSV, Excel, PDF)' },
    { key: 'manage_rbac', label: 'Modify role-permission execution matrix' },
    { key: 'view_system_telemetry', label: 'View host stats, server load, and latency' }
  ];

  const fetchGovernanceData = useCallback(async () => {
    try {
      setLoading(true);

      const telData = await adminService.getSystemTelemetry();

      setTelemetry(telData);

      const trendData = await adminService.getActivityTrend();
      setActivityTrendData(trendData);

      const browserData = await adminService.getBrowserDistribution();

      const formattedBrowserData = browserData.map(item => ({
        ...item,
        color: browserColors[item.name] || browserColors.Unknown
      }));

      setBrowserDistributionData(formattedBrowserData);

      const notifData = await adminService.getAdminNotifications();
      setNotifications(notifData);

      const matrixData = await adminService.getPermissionMatrix();
      setMatrix(matrixData);

    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchGovernanceData();
  }, [fetchGovernanceData]);

  const handleTogglePermission = (role, permissionKey) => {
    setMatrix(prev => {
      const currentRolePerms = prev[role] || [];
      const updated = currentRolePerms.includes(permissionKey)
        ? currentRolePerms.filter(k => k !== permissionKey)
        : [...currentRolePerms, permissionKey];
      return {
        ...prev,
        [role]: updated
      };
    });
  };

  const handleSaveMatrix = async () => {
    try {
      setSavingMatrix(true);
      await adminService.updatePermissionMatrix(matrix);
      alert('Permission Matrix successfully saved.');
    } catch (err) {
      console.error('Failed to update Permission Matrix:', err);
      alert('Failed to update Permission Matrix.');
    } finally {
      setSavingMatrix(false);
    }
  };

  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'users', label: 'Manage Users', icon: Users },
    { id: 'logs', label: 'Audit Trails', icon: FileText },
    { id: 'matrix', label: 'Permission Matrix', icon: Key },
    { id: 'health', label: 'System Telemetry', icon: Activity },
  ];

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'warning': return 'text-amber-400 bg-amber-500/10 border-amber-500/20';
      case 'danger': return 'text-red-400 bg-red-500/10 border-red-500/20';
      case 'success': return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
      default: return 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20';
    }
  };

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'warning': return <AlertTriangle size={14} className="text-amber-400" />;
      case 'danger': return <ShieldAlert size={14} className="text-red-400" />;
      case 'success': return <CheckCircle size={14} className="text-emerald-400" />;
      default: return <Info size={14} className="text-cyan-400" />;
    }
  };

  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload || payload.length === 0) {
      return null;
    }

    return (
      <div className="bg-slate-900 border border-slate-700 rounded-lg p-3 shadow-xl">
        <p className="text-xs font-semibold text-slate-200 mb-2">
          📅 {label}
        </p>

        <p className="text-xs text-cyan-400">
          Transactions : {payload[0].value}
        </p>

        <p className="text-xs text-violet-400">
          Fraud Cases : {payload[1].value}
        </p>
      </div>
    );
  };

  return (
    <DashboardLayout>
      <div className="pb-3 border-b border-slate-800 flex items-center justify-between relative">
        <div>
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-6 h-6 text-cyan-400" />
            <h1 className="text-2xl font-bold text-slate-100 tracking-tight">Enterprise Governance Console</h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Privileged administrative control center for user access, audit compliance, security alerts, and system health.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => fetchGovernanceData()}
            className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition-all"
            title="Refresh statistics"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          </button>

          {/* Admin Notifications Trigger */}
          <div className="relative">
            <button
              onClick={() => setShowNotifications(!showNotifications)}
              className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition-all relative"
            >
              <Bell size={16} />
              {notifications.length > 0 && (
                <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-[10px] text-white flex items-center justify-center rounded-full font-bold">
                  {notifications.length}
                </span>
              )}
            </button>

            {showNotifications && (
              <div className="absolute right-0 mt-2 w-80 rounded-xl glass border border-slate-700 shadow-2xl z-50 p-4 animate-fade-in bg-slate-950/95">
                <div className="flex items-center justify-between pb-2 border-b border-slate-800 mb-3">
                  <h4 className="text-xs font-bold text-slate-200">Governance Alerts</h4>
                  <Badge variant="neutral">{notifications.length} New</Badge>
                </div>
                <div className="space-y-2.5 max-h-60 overflow-y-auto pr-1">
                  {notifications.length === 0 ? (
                    <p className="text-[10px] text-slate-500 text-center py-4">No active system alerts.</p>
                  ) : (
                    notifications.map((n, i) => (
                      <div key={i} className={`p-2.5 rounded-lg border text-[11px] flex gap-2 ${getSeverityColor(n.severity)}`}>
                        <div className="mt-0.5">{getSeverityIcon(n.severity)}</div>
                        <div>
                          <p className="font-semibold">{n.title}</p>
                          <p className="text-[10px] text-slate-400 mt-0.5 leading-relaxed">{n.message}</p>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Console Sub-tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-3 mt-3 overflow-x-auto">
        {tabs.map(tab => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition-all whitespace-nowrap ${isActive
                ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 shadow-lg shadow-cyan-500/10'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
            >
              <Icon size={14} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab Panels */}
      <div className="mt-4 animate-fade-in">
        {loading && activeTab === 'dashboard' ? (
          <div className="flex items-center justify-center py-20">
            <Spinner size="lg" />
          </div>
        ) : (
          <>
            {activeTab === 'dashboard' && (
              <div className="space-y-6">
                {/* KPI Cards Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  <Card glass className="relative overflow-hidden group">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="text-[10px] uppercase font-bold text-slate-500">Active Investigators</p>
                        <h3 className="text-2xl font-bold text-slate-200 mt-1">
                          {telemetry?.sessions?.total_users || 0}
                        </h3>
                      </div>
                      <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400">
                        <Users size={16} />
                      </div>
                    </div>
                    <p className="text-[10px] text-slate-400 mt-2">
                      <span className="text-red-400 font-semibold">{telemetry?.sessions?.suspended_users || 0}</span> accounts suspended
                    </p>
                  </Card>

                  <Card glass>
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="text-[10px] uppercase font-bold text-slate-500">Active Device Sessions</p>
                        <h3 className="text-2xl font-bold text-slate-200 mt-1">
                          {telemetry?.sessions?.active_sessions || 0}
                        </h3>
                      </div>
                      <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400">
                        <Cpu size={16} />
                      </div>
                    </div>
                    <p className="text-[10px] text-slate-400 mt-2">Across all authenticated clients</p>
                  </Card>

                  <Card glass>
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="text-[10px] uppercase font-bold text-slate-500">Database Ping Latency</p>
                        <h3 className="text-2xl font-bold text-slate-200 mt-1">
                          {telemetry?.database?.ping_ms || 0.0} <span className="text-xs text-slate-500">ms</span>
                        </h3>
                      </div>
                      <div className="p-2 rounded-lg bg-purple-500/10 text-purple-400">
                        <Database size={16} />
                      </div>
                    </div>
                    <p className="text-[10px] text-emerald-400 mt-2 flex items-center gap-1">
                      <CheckCircle size={10} /> Status: {telemetry?.database?.status || 'CONNECTED'}
                    </p>
                  </Card>

                  <Card glass>
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="text-[10px] uppercase font-bold text-slate-500">Governance Security Score</p>
                        <h3 className="text-2xl font-bold text-emerald-400">
                          {telemetry?.governance_score ?? 0}%
                        </h3>
                      </div>
                      <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
                        <CheckCircle size={16} />
                      </div>
                    </div>
                    <p className="text-[10px] text-slate-400 mt-2">Based on audit trail completion</p>
                  </Card>
                </div>

                {/* Analytics Charts */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {/* Activity trend (2 cols) */}
                  <div className="lg:col-span-2">
                    <Card
                      title="Fraud Detection Activity"
                      subtitle="Daily transactions and fraud cases (Last 7 Days)"
                    >
                      <div className="h-72 w-full mt-2">
                        <ResponsiveContainer width="100%" height="100%">
                          <AreaChart data={activityTrendData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                            <defs>
                              <linearGradient id="colorLogins" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.2} />
                                <stop offset="95%" stopColor="#06b6d4" stopOpacity={0} />
                              </linearGradient>
                              <linearGradient id="colorTelemetry" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.2} />
                                <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                              </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                            <XAxis dataKey="date" stroke="#64748b" fontSize={10} />
                            <YAxis stroke="#64748b" fontSize={10} />
                            <Tooltip
                              content={<CustomTooltip />}
                            />                            <Legend wrapperStyle={{ fontSize: 10, color: '#94a3b8' }} />
                            <Area
                              type="linear"
                              dataKey="transactions"
                              name="Transactions"
                              stroke="#06b6d4"
                              fill="url(#colorLogins)"
                            />                            <Area
                              type="linear"
                              dataKey="fraud"
                              name="Fraud Cases"
                              stroke="#8b5cf6"
                              fill="url(#colorTelemetry)"
                            />                          </AreaChart>
                        </ResponsiveContainer>
                      </div>
                    </Card>
                  </div>

                  {/* Browser/OS distribution (1 col) */}
                  <div>
                    <Card title="Active Client Devices" subtitle="Distribution of browsers used by investigators">
                      <div className="h-72 w-full mt-2 flex flex-col justify-between">
                        <div className="h-48">
                          <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                              <Pie
                                data={browserDistributionData}
                                cx="50%"
                                cy="50%"
                                innerRadius={50}
                                outerRadius={70}
                                paddingAngle={4}
                                dataKey="value"
                              >
                                {browserDistributionData.map((entry, index) => (
                                  <Cell key={`cell-${index}`} fill={entry.color} />
                                ))}
                              </Pie>
                              <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }} itemStyle={{ fontSize: 10 }} />
                            </PieChart>
                          </ResponsiveContainer>
                        </div>
                        <div className="grid grid-cols-2 gap-2 text-[10px] text-slate-400 mt-2 px-2">
                          {browserDistributionData.map((b, i) => (
                            <div key={i} className="flex items-center gap-1.5">
                              <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: b.color }} />
                              <span>{b.name} ({b.value})</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </Card>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'users' && <ManageUsers />}

            {activeTab === 'logs' && <AuditLogs />}

            {activeTab === 'matrix' && (
              <Card
                title="Granular RBAC Permission Matrix"
                subtitle="Map fine-grained app capabilities directly to investigator roles (future RBAC expansions)"
                action={
                  <Button
                    variant="primary"
                    size="sm"
                    isLoading={savingMatrix}
                    onClick={handleSaveMatrix}
                  >
                    Save Permission Matrix
                  </Button>
                }
              >
                <div className="overflow-x-auto mt-4">
                  <table className="fg-table border border-slate-800">
                    <thead>
                      <tr>
                        <th>Capability Scope</th>
                        <th className="text-center w-36">System Administrator</th>
                        <th className="text-center w-36">Fraud Analyst</th>
                      </tr>
                    </thead>
                    <tbody>
                      {availablePermissions.map(p => (
                        <tr key={p.key} className="hover:bg-slate-800/20">
                          <td className="py-3">
                            <span className="font-semibold text-slate-200 block text-xs">{p.label}</span>
                            <span className="font-mono text-[9px] text-cyan-400/80">{p.key}</span>
                          </td>
                          <td className="text-center py-3">
                            <input
                              type="checkbox"
                              checked={matrix['Admin']?.includes(p.key) || false}
                              onChange={() => handleTogglePermission('Admin', p.key)}
                              className="w-4 h-4 rounded border-slate-700 bg-slate-900 text-cyan-500 focus:ring-cyan-500/50"
                            />
                          </td>
                          <td className="text-center py-3">
                            <input
                              type="checkbox"
                              checked={matrix['Fraud Analyst']?.includes(p.key) || false}
                              onChange={() => handleTogglePermission('Fraud Analyst', p.key)}
                              className="w-4 h-4 rounded border-slate-700 bg-slate-900 text-cyan-500 focus:ring-cyan-500/50"
                            />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Card>
            )}

            {activeTab === 'health' && <SystemHealth />}
          </>
        )}
      </div>
    </DashboardLayout>
  );
}
