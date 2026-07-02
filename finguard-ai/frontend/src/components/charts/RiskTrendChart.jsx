import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Card } from '../ui';

export function RiskTrendChart({ data }) {
  return (
    <Card title="Monthly Risk Level Bands" subtitle="Distribution of transactions across Low, Medium, High & Critical risk bands">
      <div className="h-72 w-full pt-2">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis />
            <Tooltip />
            <Legend verticalAlign="top" height={36} />
            <Line type="monotone" dataKey="Low" stroke="#10b981" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="Medium" stroke="#f59e0b" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="High" stroke="#f97316" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="Critical" stroke="#ef4444" strokeWidth={2} dot={true} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
