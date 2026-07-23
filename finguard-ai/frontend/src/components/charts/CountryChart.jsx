import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Card } from '../ui';

export function CountryChart({ data }) {
  return (
    <Card title="Geographic Fraud Vulnerability" subtitle="Transaction volume & fraud incident rate by country">
      <div className="h-72 w-full pt-2">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis 
              dataKey="country" 
              tick={{ fill: '#94a3b8', fontSize: 11 }}
              stroke="#475569"
            />
            <YAxis 
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
              formatter={(value, name) => [
                name === 'fraudRate' ? `${value}%` : value.toLocaleString(),
                name === 'fraudRate' ? 'Fraud Rate' : 'Transactions'
              ]}
            />
            <Bar 
              dataKey="transactions" 
              radius={[4, 4, 0, 0]}
              animationDuration={1000}
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.fraudRate > 5 ? '#ef4444' : '#06b6d4'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
