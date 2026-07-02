import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Card } from '../ui';

export function CountryChart({ data }) {
  return (
    <Card title="Geographic Fraud Vulnerability" subtitle="Transaction volume & fraud incident rate by country">
      <div className="h-72 w-full pt-2">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="country" />
            <YAxis />
            <Tooltip
              formatter={(value, name) => [
                name === 'fraudRate' ? `${value}%` : value.toLocaleString(),
                name === 'fraudRate' ? 'Fraud Rate' : 'Transactions'
              ]}
            />
            <Bar dataKey="transactions" fill="#3b82f6" radius={[4, 4, 0, 0]}>
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
