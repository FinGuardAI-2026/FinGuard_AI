import React from 'react';
import { Card } from '../ui';

export function AverageResponseTime({ data = [] }) {
  return (
    <Card
      title="Average Response Time"
      subtitle="API latency over time (ms)"
    >
      <div className="grid grid-cols-1 gap-3 mt-3">

        <div className="p-4 rounded-lg bg-slate-900 border border-slate-800">
          <p className="text-xs text-slate-400">Average Response</p>
          <p className="text-3xl font-bold text-purple-400">
            {data.average ?? 0} ms
          </p>
        </div>

        <div className="grid grid-cols-2 gap-3">

          <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
            <p className="text-xs text-slate-400">Minimum</p>
            <p className="text-2xl font-bold text-emerald-400">
              {data.minimum ?? 0} ms
            </p>
          </div>

          <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
            <p className="text-xs text-slate-400">Maximum</p>
            <p className="text-2xl font-bold text-red-400">
              {data.maximum ?? 0} ms
            </p>
          </div>

        </div>

      </div>
    </Card>
  );
}
