import React from 'react';
import { Card } from '../ui';
import {
  Activity,
  ShieldAlert,
  CheckCircle,
  Gauge,
  Timer,
  TrendingUp
} from "lucide-react";
export function PredictionStatistics({ data = [] }) {
  return (
    <Card
      title="Prediction Statistics"
      subtitle="Real-time prediction overview"
    >
      <div className="grid grid-cols-2 gap-3 mt-3">

        <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
          <p className="text-xs text-slate-400">Today&apos;s Predictions</p>              <Activity size={16} className="text-cyan-400" />
          <p className="text-2xl font-bold text-cyan-400">
            {data.today_total ?? 0}
          </p>
        </div>

        <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
          <p className="text-xs text-slate-400">Fraud</p>
          <ShieldAlert size={16} className="text-red-400" />
          <p className="text-2xl font-bold text-red-400">
            {data.today_fraud ?? 0}
          </p>
        </div>

        <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
          <p className="text-xs text-slate-400">Genuine</p>
          <CheckCircle size={16} className="text-green-400" />
          <p className="text-2xl font-bold text-green-400">
            {data.today_genuine ?? 0}
          </p>
        </div>

        <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
          <p className="text-xs text-slate-400">Avg Risk Score</p>
          <Gauge size={16} className="text-amber-400" />
          <p className="text-2xl font-bold text-amber-400">
            {data.avg_risk_score ?? 0}
          </p>
        </div>

        <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
          <p className="text-xs text-slate-400">Avg Response</p>
          <Timer size={16} className="text-purple-400" />
          <p className="text-2xl font-bold text-purple-400">
            {data.avg_response_ms ?? 0} ms
          </p>
        </div>

        <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
          <p className="text-xs text-slate-400">Today&apos;s Change</p>          <TrendingUp size={16} className="text-sky-400" />
          <p className="text-2xl font-bold text-sky-400">
            {data.today_change_pct ?? 0}%
          </p>
        </div>

      </div>
    </Card>
  );
}
