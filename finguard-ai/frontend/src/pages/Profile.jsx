import React from 'react';
import { DashboardLayout } from '../layouts/DashboardLayout';
import { Card, Button, Input, Badge } from '../components/ui';
import { useAuth } from '../context/AuthContext';
import { User, Shield, Mail, Calendar } from 'lucide-react';

export function Profile() {
  const { user } = useAuth();

  return (
    <DashboardLayout>
      <div className="pb-2 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <User className="w-6 h-6 text-cyan-400" />
          <h1 className="text-2xl font-bold text-slate-100 tracking-tight">User Account Profile</h1>
        </div>
        <p className="text-xs text-slate-400 mt-1">Manage personal credentials and security role attributes.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card glass className="flex flex-col items-center text-center p-6 md:col-span-1">
          <div className="w-20 h-20 rounded-2xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center text-slate-950 font-bold text-2xl mb-4 shadow-lg shadow-cyan-500/20">
            {user?.full_name ? user.full_name.charAt(0) : 'A'}
          </div>
          <h3 className="text-lg font-bold text-slate-100">{user?.full_name || 'Senior Analyst'}</h3>
          <span className="text-xs text-slate-400 font-mono mt-0.5">{user?.email || 'analyst@finguard.ai'}</span>
          
          <div className="mt-4">
            <Badge variant="info">{user?.role || 'Fraud Analyst'}</Badge>
          </div>
        </Card>

        <Card title="Account Information" subtitle="System identity details" className="md:col-span-2 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input label="Full Name" defaultValue={user?.full_name || 'Senior Fraud Analyst'} icon={User} />
            <Input label="Email Address" defaultValue={user?.email || 'analyst@finguard.ai'} icon={Mail} />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input label="Security Role" defaultValue={user?.role || 'Fraud Analyst'} disabled icon={Shield} />
            <Input label="Account Created" defaultValue="2026-01-15 10:00 UTC" disabled icon={Calendar} />
          </div>
          <Button variant="primary" className="mt-2">Update Profile</Button>
        </Card>
      </div>
    </DashboardLayout>
  );
}
