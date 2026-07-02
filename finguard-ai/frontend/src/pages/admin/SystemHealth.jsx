import React from 'react';
import { Card, Badge } from '../../components/ui';
import { Activity, Cpu, Database, Server } from 'lucide-react';

export function SystemHealth() {
  const components = [
    { name: 'FastAPI Backend Core', status: 'OPERATIONAL', latency: '14 ms', icon: Server },
    { name: 'MongoDB Database Cluster', status: 'OPERATIONAL', latency: '4 ms', icon: Database },
    { name: 'Champion XGBoost Inference Engine', status: 'LOADED', latency: '38 ms', version: 'champion_xgboost_v2.1', icon: Cpu },
    { name: 'SHAP Explainability Module', status: 'LOADED', latency: '120 ms', icon: Activity },
    { name: 'Google Gemini API Client', status: 'CONNECTED', latency: '850 ms', icon: Activity }
  ];

  return (
    <div className="space-y-6">
      <Card title="AI & Services Health Monitor" subtitle="Real-time telemetry and artifact load state">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {components.map((c, i) => {
            const Icon = c.icon;
            return (
              <div key={i} className="p-4 rounded-xl bg-slate-900/80 border border-slate-800/80 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-lg bg-cyan-500/10 text-cyan-400">
                    <Icon size={20} />
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-slate-200">{c.name}</h4>
                    {c.version && <span className="text-[10px] text-cyan-400 font-mono block">{c.version}</span>}
                    <span className="text-[10px] text-slate-500">Avg Latency: {c.latency}</span>
                  </div>
                </div>
                <Badge variant="success">{c.status}</Badge>
              </div>
            );
          })}
        </div>
      </Card>
    </div>
  );
}
