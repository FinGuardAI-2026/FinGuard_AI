import React from 'react';

export function AuthLayout({ children }) {
  return (
    <div className="min-h-screen bg-slate-950 bg-mesh-gradient flex items-center justify-center p-4 relative overflow-hidden">
      {/* Ambient background glow orbs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="w-full max-w-md relative z-10 animate-fade-in-up">
        {children}
      </div>
    </div>
  );
}
