import React from 'react';
import { Card } from '../ui';
import { TrendingUp, TrendingDown } from 'lucide-react';

export function StatCard({ title, value, change, isNegativeGood = false, icon: Icon, color = 'cyan' }) {
  const isPositive = change && change.startsWith('+');
  const isGood = isNegativeGood ? !isPositive : isPositive;

  const colorStyles = {
    cyan: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
    red: 'bg-red-500/10 text-red-400 border-red-500/20',
    amber: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    green: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    purple: 'bg-purple-500/10 text-purple-400 border-purple-500/20'
  };

  return (
    <Card glass className="relative overflow-hidden group hover:border-slate-700 transition-all">
      <div className="flex items-start justify-between">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">{title}</span>
          <div className="text-2xl font-bold text-slate-100 font-mono mt-2 tracking-tight">{value}</div>
        </div>
        {Icon && (
          <div className={`p-2.5 rounded-xl border ${colorStyles[color]} transition-transform group-hover:scale-110`}>
            <Icon size={22} />
          </div>
        )}
      </div>

      {change && (
        <div className="mt-3 flex items-center gap-1.5 text-xs">
          <span className={`inline-flex items-center gap-0.5 font-medium px-1.5 py-0.5 rounded ${
            isGood ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'
          }`}>
            {isPositive ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
            {change}
          </span>
          <span className="text-slate-500">vs last 30d</span>
        </div>
      )}
    </Card>
  );
}
