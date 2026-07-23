import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Card } from '../ui';

export function MerchantCategoryChart({ data }) {
  return (
    <Card title="Merchant Category Risk Profiling" subtitle="Genuine vs Fraudulent transaction volumes across MCC groups">
      <div className="h-72 w-full pt-2">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart layout="vertical" data={data} margin={{ top: 10, right: 20, left: 40, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis 
              type="number" 
              tick={{ fill: '#94a3b8', fontSize: 11 }}
              stroke="#475569"
            />
            <YAxis 
              dataKey="category" 
              type="category" 
              tick={{ fontSize: 11, fill: '#94a3b8' }}
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
              height={36}
              wrapperStyle={{ fontSize: '11px' }}
            />
            <Bar 
              dataKey="genuine" 
              stackId="a" 
              fill="#10b981" 
              name="Genuine Volume"
              animationDuration={1000}
            />
            <Bar 
              dataKey="fraud" 
              stackId="a" 
              fill="#ef4444" 
              name="Fraud Volume"
              animationDuration={1000}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
