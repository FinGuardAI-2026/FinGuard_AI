import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Card } from '../ui';

export function FraudTrendChart({ data }) {
  return (
    <Card title="30-Day Fraud Trend" subtitle="Daily transaction volume vs flagged fraudulent cases">
      <div className="h-72 w-full pt-2">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#06b6d4" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="colorFraud" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.4}/>
                <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis yAxisId="left" />
            <YAxis yAxisId="right" orientation="right" />
            <Tooltip />
            <Legend verticalAlign="top" height={36} />
            <Area yAxisId="left" type="monotone" dataKey="Total" stroke="#06b6d4" fillOpacity={1} fill="url(#colorTotal)" name="Total Transactions" />
            <Area yAxisId="right" type="monotone" dataKey="Fraud" stroke="#ef4444" fillOpacity={1} fill="url(#colorFraud)" name="Fraud Cases" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
