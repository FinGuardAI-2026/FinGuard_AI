import React from 'react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Card } from '../ui';

export function PaymentMethodChart({ data }) {
  return (
    <Card title="Payment Channel Distribution" subtitle="Share of transaction volume by payment rail">
      <div className="h-72 w-full pt-2">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={90}
              paddingAngle={4}
              dataKey="value"
              animationDuration={1000}
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} stroke="rgba(15,23,42,0.8)" strokeWidth={2} />
              ))}
            </Pie>
            <Tooltip 
              contentStyle={{
                backgroundColor: '#0f172a',
                border: '1px solid #334155',
                borderRadius: '8px',
                fontSize: '12px'
              }}
              itemStyle={{ color: '#e2e8f0' }}
              formatter={(val) => [`${val}%`, 'Share']} 
            />
            <Legend 
              verticalAlign="bottom" 
              height={36} 
              iconType="circle"
              wrapperStyle={{ fontSize: '11px' }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
