import React from 'react';
import { Card, Badge } from '../ui';
import { Activity } from 'lucide-react';

const getBadgeVariant = (statusVal) => {
  if (!statusVal) return 'neutral';
  const val = String(statusVal).trim().toLowerCase();

  const successValues = ['healthy', 'connected', 'running', 'loaded', 'ready', 'online', 'operational'];
  const warningValues = ['warning', 'degraded', 'slow', 'pending'];
  const dangerValues = ['disconnected', 'offline', 'failed', 'stopped', 'error', 'unavailable'];

  if (successValues.includes(val)) return 'success';
  if (warningValues.includes(val)) return 'warning';
  if (dangerValues.includes(val)) return 'danger';
  return 'neutral';
};

export function SystemStatus({ status = {} }) {
  const {
    uptime,
    database,
    api,
    ml_engine,
    model_service
  } = status;

  return (
    <Card
      title="System Status"
      subtitle="Real-time infrastructure monitoring"
    >
      <div className="space-y-4">
        {/* Uptime */}
        <div className="flex items-center justify-between p-3 rounded-lg bg-slate-900/80 border border-slate-800/80">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
              <Activity size={18} />
            </div>
            <div>
              <div className="text-xs font-semibold text-slate-200">System Uptime</div>
              <div className="text-[11px] text-slate-500">Time since last restart</div>
            </div>
          </div>
          <div className="text-right">
            <div className="text-sm font-bold text-slate-100 font-mono">{uptime || '0d 0h'}</div>
            <Badge variant={getBadgeVariant('Operational')}>Operational</Badge>
          </div>
        </div>

        {/* Core Services */}
        <div className="space-y-3">

          <div className="flex items-center justify-between p-3 rounded-lg bg-slate-900/80 border border-slate-800/80">
            <span className="text-sm text-slate-300">Database</span>
            <Badge variant={getBadgeVariant(database)}>{database}</Badge>
          </div>

          <div className="flex items-center justify-between p-3 rounded-lg bg-slate-900/80 border border-slate-800/80">
            <span className="text-sm text-slate-300">API Gateway</span>
            <Badge variant={getBadgeVariant(api)}>{api}</Badge>
          </div>

          <div className="flex items-center justify-between p-3 rounded-lg bg-slate-900/80 border border-slate-800/80">
            <span className="text-sm text-slate-300">ML Engine</span>
            <Badge variant={getBadgeVariant(ml_engine)}>{ml_engine}</Badge>
          </div>

          <div className="flex items-center justify-between p-3 rounded-lg bg-slate-900/80 border border-slate-800/80">
            <span className="text-sm text-slate-300">Model Service</span>
            <Badge variant={getBadgeVariant(model_service)}>{model_service}</Badge>
          </div>

        </div>

      </div>
    </Card>
  );
}
