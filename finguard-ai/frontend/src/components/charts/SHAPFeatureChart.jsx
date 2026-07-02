import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Card } from '../ui';

export function SHAPFeatureChart({ data }) {
  return (
    <Card title="Global SHAP Feature Importance" subtitle="Mean absolute Shapley attributions across model feature space">
      <div className="h-72 w-full pt-2">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart layout="vertical" data={data} margin={{ top: 10, right: 20, left: 110, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" domain={[0, 0.6]} />
            <YAxis dataKey="feature" type="category" width={180} tick={{ fontSize: 11, fontWeight: 'bold', fill: '#06b6d4' }} />
            <Tooltip formatter={(val) => [val.toFixed(3), 'mean(|SHAP|)']} />
            <Bar dataKey="importance" fill="#06b6d4" radius={[0, 4, 4, 0]}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={index === 0 ? '#ef4444' : index === 1 ? '#f59e0b' : '#06b6d4'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
