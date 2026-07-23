import React, { useState, useEffect } from 'react';
import { adminService } from '../../services/admin';
import { Card, Badge, Spinner } from '../../components/ui';
import { formatDate } from "../../utils/dateFormatter";
import {
  Server,
  Database,
  Cpu,
  Activity,
  // CheckCircle2,
  // AlertCircle,
  Clock,
  HardDrive,
  // Settings,
  RefreshCw
} from 'lucide-react';

export function SystemHealth() {
  const [telemetry, setTelemetry] = useState(null);
  const [loading, setLoading] = useState(true);
  const [apiResponseTime, setApiResponseTime] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  // const [error, setError] = useState(null);

  const fetchTelemetry = async () => {
    const tStart = performance.now();

    try {
      // setError(null);

      const data = await adminService.getSystemTelemetry();
      setTelemetry(data);

      const duration = Math.round(performance.now() - tStart);
      setApiResponseTime(duration);

    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTelemetry();
  }, []);

  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => {
      fetchTelemetry();
    }, 5000);
    return () => clearInterval(interval);
  }, [autoRefresh]);

  const components = [
    {
      name: 'FastAPI Backend Core',
      status: 'OPERATIONAL',
      latency: apiResponseTime ? `${apiResponseTime} ms` : '-- ms',
      icon: Server,
      desc: 'Central governance server gateway'
    },
    {
      name: 'MongoDB Database Cluster',
      status: telemetry?.database?.status || 'OPERATIONAL',
      latency: telemetry?.database?.ping_ms
        ? `${telemetry.database.ping_ms} ms`
        : '-- ms',
      icon: Database,
      desc: 'Persistent analytics and security storage'
    },
    {
      name: 'Champion XGBoost Inference Engine',
      status: telemetry?.ai_models?.xgboost?.status || 'LOADED',
      latency: telemetry?.ai_models?.xgboost?.latency_ms
        ? `${telemetry.ai_models.xgboost.latency_ms} ms`
        : '-- ms',
      version: 'champion_xgboost_v2.1',
      icon: Cpu,
      desc: 'Real-time transaction risk evaluation'
    },
    {
      name: 'SHAP Explainability Module',
      status: telemetry?.ai_models?.shap?.status || 'LOADED',
      latency: telemetry?.ai_models?.shap?.latency_ms
        ? `${telemetry.ai_models.shap.latency_ms} ms`
        : '-- ms',
      icon: Activity,
      desc: 'Local feature impact explanation generator'
    },
    {
      name: 'Google Gemini API Client',
      status: telemetry?.ai_models?.gemini?.status || 'CONNECTED',
      latency: telemetry?.ai_models?.gemini?.latency_ms
        ? `${telemetry.ai_models.gemini.latency_ms} ms`
        : '-- ms',
      icon: Activity,
      desc: 'Deep reasoning LLM incident reporter'
    }
  ];

  const getHealthBadge = (status) => {
    if (status === 'OPERATIONAL' || status === 'LOADED' || status === 'CONNECTED') {
      return <Badge variant="success">Healthy</Badge>;
    }
    if (status === 'DEGRADED') {
      return <Badge variant="warning">Degraded</Badge>;
    }
    return <Badge variant="danger">Offline</Badge>;
  };

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex justify-between items-center bg-slate-900/50 border border-slate-800 p-3 rounded-xl">
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <Activity size={14} className="text-cyan-400" />
          <span>Real-time polling: every 5 seconds</span>
        </div>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-xs text-slate-300 select-none cursor-pointer">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded border-slate-700 bg-slate-900 text-cyan-500 focus:ring-cyan-500/50 w-3.5 h-3.5"
            />
            <span>Auto Refresh</span>
          </label>
          <button
            onClick={fetchTelemetry}
            className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-all text-xs flex items-center gap-1.5"
          >
            <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />
            <span>Refetch</span>
          </button>
        </div>
      </div>

      {loading && !telemetry ? (
        <div className="flex justify-center py-20">
          <Spinner size="lg" />
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          {/* Telemetry and metrics */}
          <div className="lg:col-span-2 space-y-6">
            <Card title="Infrastructure & AI Engine Latencies" subtitle="Response performance indicators across components">
              <div className="space-y-3.5 mt-2">
                {components.map((c, i) => {
                  const Icon = c.icon;
                  return (
                    <div key={i} className="p-4 rounded-xl bg-slate-950/80 border border-slate-800/80 flex items-center justify-between hover:border-slate-700/80 transition-all group">
                      <div className="flex items-center gap-3.5">
                        <div className="p-3 rounded-lg bg-cyan-500/10 text-cyan-400 group-hover:bg-cyan-500/20 transition-all">
                          <Icon size={18} />
                        </div>
                        <div>
                          <h4 className="text-xs font-bold text-slate-200">{c.name}</h4>
                          {c.version && <span className="text-[10px] text-cyan-400 font-mono block mt-0.5">{c.version}</span>}
                          <p className="text-[10px] text-slate-500 mt-0.5">{c.desc}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <span className="text-xs font-mono font-bold text-slate-300 block mb-1">{c.latency}</span>
                        {getHealthBadge(c.status)}
                      </div>
                    </div>
                  );
                })}
              </div>
            </Card>
          </div>

          {/* Machine Load & Deployment Specs */}
          <div className="space-y-6">

            {/* Machine Load Cards */}
            <Card title="Governed Resources Load" subtitle="Hardware resource parameters (FastAPI host server)">
              <div className="space-y-4 mt-2">

                {/* CPU */}
                <div>
                  <div className="flex justify-between items-center text-[10px] text-slate-400 mb-1">
                    <span className="flex items-center gap-1.5"><Cpu size={12} /> Processor Utilisation</span>
                    <span className="font-mono text-slate-200 font-bold">{telemetry?.system_load?.cpu_utilization || 0}%</span>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-1.5">
                    <div
                      className="bg-cyan-500 h-1.5 rounded-full transition-all duration-500"
                      style={{ width: `${telemetry?.system_load?.cpu_utilization || 0}%` }}
                    />
                  </div>
                </div>

                {/* RAM */}
                <div>
                  <div className="flex justify-between items-center text-[10px] text-slate-400 mb-1">
                    <span className="flex items-center gap-1.5"><Server size={12} /> Memory Allocation</span>
                    <span className="font-mono text-slate-200 font-bold">{telemetry?.system_load?.memory_utilization || 0}%</span>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-1.5">
                    <div
                      className="bg-purple-500 h-1.5 rounded-full transition-all duration-500"
                      style={{ width: `${telemetry?.system_load?.memory_utilization || 0}%` }}
                    />
                  </div>
                </div>

                {/* DISK */}
                <div>
                  <div className="flex justify-between items-center text-[10px] text-slate-400 mb-1">
                    <span className="flex items-center gap-1.5"><HardDrive size={12} /> SSD Write Capacity</span>
                    <span className="font-mono text-slate-200 font-bold">{telemetry?.system_load?.disk_utilization || 0}%</span>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-1.5">
                    <div
                      className="bg-amber-500 h-1.5 rounded-full transition-all duration-500"
                      style={{ width: `${telemetry?.system_load?.disk_utilization || 0}%` }}
                    />
                  </div>
                </div>

              </div>
            </Card>

            {/* Deployment Info Card */}
            <Card title="Console Deployment Specs" subtitle="Metadata detailing the hosting infrastructure environment">
              <div className="space-y-3.5 mt-2 text-[10px]">

                <div className="flex items-center justify-between py-1.5 border-b border-slate-800">
                  <span className="text-slate-500 uppercase font-bold">Execution Mode</span>
                  <Badge variant="info">{telemetry?.deployment?.environment || 'Production'}</Badge>
                </div>

                <div className="flex items-center justify-between py-1.5 border-b border-slate-800">
                  <span className="text-slate-500 uppercase font-bold">System Version</span>
                  <span className="font-mono text-slate-200 font-semibold">{telemetry?.deployment?.version || 'N/A'}</span>
                </div>

                <div className="flex items-center justify-between py-1.5 border-b border-slate-800">
                  <span className="text-slate-500 uppercase font-bold">Server Host Uptime</span>
                  <span className="font-semibold text-slate-200 flex items-center gap-1.5">
                    <Clock size={12} className="text-cyan-400" /> {telemetry?.deployment?.uptime || 'N/A'}
                  </span>
                </div>

                <div className="flex items-center justify-between py-1.5">
                  <span className="text-slate-500 uppercase font-bold">Build Timestamp</span>
                  <span className="font-mono text-slate-300">
                    {telemetry?.deployment?.build_timestamp
                      ? formatDate(telemetry.deployment.build_timestamp)
                      : 'N/A'}
                  </span>
                </div>

              </div>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
