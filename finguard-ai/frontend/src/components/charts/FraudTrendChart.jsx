import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Card } from '../ui';

export function FraudTrendChart({ data }) {
  return (
    <Card title="30-Day Fraud Trend" subtitle="Daily transaction volume vs flagged fraudulent cases">
      <div className="h-60 w-full pt-1">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4}/>
                <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.05}/>
              </linearGradient>
              <linearGradient id="colorFraud" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.5}/>
                <stop offset="95%" stopColor="#ef4444" stopOpacity={0.05}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis 
              dataKey="date" 
              tick={{ fill: '#94a3b8', fontSize: 11 }}
              stroke="#475569"
            />
            <YAxis 
              yAxisId="left" 
              tick={{ fill: '#94a3b8', fontSize: 11 }}
              stroke="#475569"
            />
            <YAxis 
              yAxisId="right" 
              orientation="right" 
              tick={{ fill: '#94a3b8', fontSize: 11 }}
              stroke="#475569"
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#0f172a',
                border: '1px solid #334155',
                borderRadius: '8px',
                fontSize: '12px'
              }}
              itemStyle={{ color: '#e2e8f0' }}
            />
            <Legend 
              verticalAlign="top" 
              height={24}
              wrapperStyle={{ fontSize: '11px' }}
            />
            <Area 
              yAxisId="left" 
              type="monotone" 
              dataKey="Total" 
              stroke="#06b6d4" 
              strokeWidth={2}
              fillOpacity={1} 
              fill="url(#colorTotal)" 
              name="Total Transactions"
              animationDuration={1000}
            />
            <Area 
              yAxisId="right" 
              type="monotone" 
              dataKey="Fraud" 
              stroke="#ef4444" 
              strokeWidth={2}
              fillOpacity={1} 
              fill="url(#colorFraud)" 
              name="Fraud Cases"
              animationDuration={1000}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
