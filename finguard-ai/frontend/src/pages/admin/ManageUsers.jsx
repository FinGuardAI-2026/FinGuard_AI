import React from 'react';
import { Card, Badge, Button } from '../../components/ui';
import { UserPlus, Trash2, Shield } from 'lucide-react';

export function ManageUsers() {
  const users = [
    { id: 'usr_1', name: 'System Administrator', email: 'admin@finguard.ai', role: 'Admin', status: 'ACTIVE' },
    { id: 'usr_2', name: 'Senior Fraud Analyst', email: 'analyst@finguard.ai', role: 'Fraud Analyst', status: 'ACTIVE' },
    { id: 'usr_3', name: 'Junior Investigator', email: 'junior@finguard.ai', role: 'Fraud Analyst', status: 'ACTIVE' }
  ];

  return (
    <Card title="User Access Management" subtitle="Manage provisioned accounts and RBAC role assignments" action={
      <Button variant="primary" size="sm"><UserPlus size={14} className="mr-1" /> Add User</Button>
    }>
      <div className="overflow-x-auto">
        <table className="fg-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Role</th>
              <th>Status</th>
              <th className="text-right">Action</th>
            </tr>
          </thead>
          <tbody>
            {users.map(u => (
              <tr key={u.id}>
                <td className="font-semibold text-slate-200">{u.name}</td>
                <td className="font-mono text-slate-400">{u.email}</td>
                <td>
                  <Badge variant={u.role === 'Admin' ? 'danger' : 'info'}>
                    <Shield size={10} className="mr-1 inline" /> {u.role}
                  </Badge>
                </td>
                <td><Badge variant="success">{u.status}</Badge></td>
                <td className="text-right">
                  <button className="p-1 text-slate-500 hover:text-red-400"><Trash2 size={16} /></button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
