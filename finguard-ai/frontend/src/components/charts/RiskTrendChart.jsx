import React from 'react';
import { Card } from '../ui';
import { ShieldCheck, ShieldAlert, AlertTriangle, AlertCircle } from 'lucide-react';
export function RiskTrendChart({ data }) {
  return (
    <Card
      title="Risk Distribution Overview"
      subtitle="Current distribution of detected transaction risk levels"
    >
      <div className="space-y-4">

        {[
          {
            label: "Low",
            value: data?.[0]?.Low || 0,
            color: "bg-emerald-500",
            icon: ShieldCheck,
            text: "text-emerald-400"
          },
          {
            label: "Medium",
            value: data?.[0]?.Medium || 0,
            color: "bg-yellow-500",
            icon: AlertTriangle,
            text: "text-yellow-400"
          },
          {
            label: "High",
            value: data?.[0]?.High || 0,
            color: "bg-orange-500",
            icon: ShieldAlert,
            text: "text-orange-400"
          },
          {
            label: "Critical",
            value: data?.[0]?.Critical || 0,
            color: "bg-red-500",
            icon: AlertCircle,
            text: "text-red-400"
          }
        ].map((risk) => {
          const Icon = risk.icon;

          const total =
            (data?.[0]?.Low || 0) +
            (data?.[0]?.Medium || 0) +
            (data?.[0]?.High || 0) +
            (data?.[0]?.Critical || 0);

          const width = total === 0 ? 0 : (risk.value / total) * 100;

          return (
            <div key={risk.label}>

              <div className="flex justify-between items-center mb-2">

                <div className={`flex items-center gap-2 ${risk.text}`}>
                  <Icon size={16} />
                  <span className="font-medium">{risk.label}</span>
                </div>

                <span className="text-slate-300 font-semibold">
                  {risk.value}
                </span>

              </div>

              <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                <div
                  className={`${risk.color} h-full rounded-full transition-all duration-700`}
                  style={{ width: `${width}%` }}
                />
              </div>

            </div>
          );
        })}

      </div>
    </Card>
  );
}
