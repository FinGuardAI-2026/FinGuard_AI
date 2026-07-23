import React from 'react';
import { Card, Badge } from '../ui';
import { TrendingUp, ShieldAlert, AlertTriangle, CheckCircle } from 'lucide-react';

export function TodaysPredictions({ predictions = {} }) {
  const { total, high_risk, medium_risk, low_risk, blocked } = predictions;

  const stats = [
    {
      label: 'Total Predictions',
      value: total || 0,
      icon: TrendingUp,
      color: 'cyan',
      bgColor: 'bg-cyan-500/10',
      textColor: 'text-cyan-400'
    },
    {
      label: 'High Risk',
      value: high_risk || 0,
      icon: ShieldAlert,
      color: 'red',
      bgColor: 'bg-red-500/10',
      textColor: 'text-red-400'
    },
    {
      label: 'Medium Risk',
      value: medium_risk || 0,
      icon: AlertTriangle,
      color: 'amber',
      bgColor: 'bg-amber-500/10',
      textColor: 'text-amber-400'
    },
    {
      label: 'Low Risk',
      value: low_risk || 0,
      icon: CheckCircle,
      color: 'emerald',
      bgColor: 'bg-emerald-500/10',
      textColor: 'text-emerald-400'
    },
    {
      label: 'Blocked',
      value: blocked || 0,
      icon: ShieldAlert,
      color: 'purple',
      bgColor: 'bg-purple-500/10',
      textColor: 'text-purple-400'
    }
  ];

  return (
    <Card
      title="Today's Predictions"
      subtitle="Real-time AI fraud detection results"
    >
      <div className="grid grid-cols-2 gap-3">
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <div
              key={index}
              className="p-4 rounded-lg bg-slate-900/80 border border-slate-800/80 hover:border-slate-700 transition-all"
            >
              <div className="flex items-center justify-between mb-2">
                <div className={`p-2 rounded-lg ${stat.bgColor} ${stat.textColor}`}>
                  <Icon size={18} />
                </div>
                <Badge variant="neutral">{stat.label}</Badge>
              </div>
              <div className="text-2xl font-bold text-slate-100 font-mono">
                {stat.value.toLocaleString()}
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
