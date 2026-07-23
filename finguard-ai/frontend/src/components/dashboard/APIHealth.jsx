import React from 'react';
import { Card, Badge } from '../ui';
import { CheckCircle, XCircle, AlertCircle } from 'lucide-react';

export function APIHealth({ endpoints = [] }) {
  const getStatusIcon = (status) => {
    switch (status?.toLowerCase()) {
      case 'healthy':
      case 'operational':
        return CheckCircle;
      case 'degraded':
      case 'warning':
        return AlertCircle;
      case 'down':
      case 'error':
        return XCircle;
      default:
        return AlertCircle;
    }
  };

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'healthy':
      case 'operational':
        return 'text-emerald-400';
      case 'degraded':
      case 'warning':
        return 'text-amber-400';
      case 'down':
      case 'error':
        return 'text-red-400';
      default:
        return 'text-slate-400';
    }
  };

  const getStatusBadge = (status) => {
    switch (status?.toLowerCase()) {
      case 'healthy':
      case 'operational':
        return 'success';
      case 'degraded':
      case 'warning':
        return 'warning';
      case 'down':
      case 'error':
        return 'danger';
      default:
        return 'neutral';
    }
  };

  return (
    <Card
      title="API Health"
      subtitle="Service endpoint status monitoring"
    >
      <div className="space-y-2">
        {endpoints.length === 0 ? (
          <div className="text-center py-8 text-slate-500 text-sm">
            No endpoint data available
          </div>
        ) : (
          endpoints.map((endpoint, index) => {
            const StatusIcon = getStatusIcon(endpoint.status);
            return (
              <div
                key={index}
                className="p-3 rounded-lg bg-slate-900/80 border border-slate-800/80 hover:border-slate-700 transition-all flex items-center justify-between"
              >
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg bg-slate-800 ${getStatusColor(endpoint.status)}`}>
                    <StatusIcon size={18} />
                  </div>
                  <div>
                    <div className="text-xs font-semibold text-slate-200">{endpoint.name}</div>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="text-[11px] text-slate-400">
                    {endpoint.latency_ms !== undefined && endpoint.latency_ms !== null ? `${endpoint.latency_ms}ms` : '-- ms'}
                  </div>
                  <Badge variant={getStatusBadge(endpoint.status)}>
                    {endpoint.status}
                  </Badge>
                </div>
              </div>
            );
          })
        )}
      </div>
    </Card>
  );
}
