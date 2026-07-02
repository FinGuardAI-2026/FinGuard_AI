import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Card } from '../ui';

export function MerchantCategoryChart({ data }) {
  return (
    <Card title="Merchant Category Risk Profiling" subtitle="Genuine vs Fraudulent transaction volumes across MCC groups">
      <div className="h-72 w-full pt-2">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart layout="vertical" data={data} margin={{ top: 10, right: 20, left: 40, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" />
            <YAxis dataKey="category" type="category" tick={{ fontSize: 11 }} />
            <Tooltip />
            <Legend verticalAlign="top" height={36} />
            <Bar dataKey="genuine" stackId="a" fill="#10b981" name="Genuine Volume" />
            <Bar dataKey="fraud" stackId="a" fill="#ef4444" name="Fraud Volume" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
