import React from 'react';

export function RiskGauge({ score = 0, level = 'Low' }) {
  // Clamp score
  const clamped = Math.min(Math.max(score, 0), 100);
  const radius = 70;
  const circumference = Math.PI * radius; // Half arc
  const strokeDashoffset = circumference - (clamped / 100) * circumference;

  const levelColors = {
    Low: '#10b981',
    Medium: '#f59e0b',
    High: '#f97316',
    Critical: '#ef4444'
  };

  const currentColor = levelColors[level] || '#06b6d4';

  return (
    <div className="flex flex-col items-center justify-center relative py-4">
      <svg className="w-48 h-28 transform -rotate-180" viewBox="0 0 180 100">
        {/* Background Track */}
        <path
          d="M 15 90 A 75 75 0 0 1 165 90"
          className="gauge-track"
          strokeWidth="14"
          strokeLinecap="round"
        />
        {/* Filled Arc */}
        <path
          d="M 15 90 A 75 75 0 0 1 165 90"
          className="gauge-fill"
          stroke={currentColor}
          strokeWidth="14"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
        />
      </svg>
      <div className="absolute top-12 flex flex-col items-center">
        <span className="text-3xl font-bold font-mono text-slate-100">{clamped.toFixed(1)}</span>
        <span className="text-[10px] font-semibold uppercase tracking-widest text-slate-400 mt-0.5">Risk Score</span>
      </div>
      <div className="mt-2">
        <span className={`inline-block px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider risk-${level.toLowerCase()}`}>
          {level} Risk
        </span>
      </div>
    </div>
  );
}
