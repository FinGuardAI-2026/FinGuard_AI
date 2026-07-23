import React from 'react';

export function SkeletonStatCard() {
  return (
    <div className="rounded-xl p-5 border border-slate-800 bg-slate-900/50 animate-pulse">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="h-3 bg-slate-800 rounded w-20 mb-3"></div>
          <div className="h-7 bg-slate-800 rounded w-24"></div>
        </div>
        <div className="h-10 w-10 bg-slate-800 rounded-xl"></div>
      </div>
      <div className="mt-3 h-4 bg-slate-800 rounded w-16"></div>
    </div>
  );
}

export function SkeletonChart({ height = 'h-72' }) {
  return (
    <div className={`rounded-xl p-5 border border-slate-800 bg-slate-900/50 animate-pulse ${height}`}>
      <div className="h-4 bg-slate-800 rounded w-1/3 mb-4"></div>
      <div className="h-3 bg-slate-800 rounded w-1/2 mb-2"></div>
      <div className="h-full bg-slate-800/50 rounded-lg mt-4"></div>
    </div>
  );
}

export function SkeletonListItem() {
  return (
    <div className="p-3 rounded-lg bg-slate-900/50 border border-slate-800 animate-pulse flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="h-10 w-10 bg-slate-800 rounded-lg"></div>
        <div>
          <div className="h-3 bg-slate-800 rounded w-24 mb-2"></div>
          <div className="h-2 bg-slate-800 rounded w-32"></div>
        </div>
      </div>
      <div className="h-6 w-16 bg-slate-800 rounded"></div>
    </div>
  );
}

export function SkeletonFeed({ count = 5 }) {
  return (
    <div className="rounded-xl p-5 border border-slate-800 bg-slate-900/50 animate-pulse">
      <div className="h-4 bg-slate-800 rounded w-1/3 mb-4"></div>
      <div className="space-y-3">
        {Array.from({ length: count }).map((_, i) => (
          <SkeletonListItem key={i} />
        ))}
      </div>
    </div>
  );
}
