import React from 'react';
import { Card, Badge } from '../../components/ui';
import { FileCode } from 'lucide-react';

export function AuditLogs() {
  const logs = [
    { id: 'log_101', action: 'PREDICT_RUN', user: 'analyst@finguard.ai', ip: '192.168.1.1', time: '2026-06-28 01:25:12 UTC', status: 'SUCCESS' },
    { id: 'log_100', action: 'USER_LOGIN', user: 'admin@finguard.ai', ip: '203.0.113.42', time: '2026-06-28 01:10:05 UTC', status: 'SUCCESS' },
    { id: 'log_099', action: 'MODEL_CONFIG_UPDATE', user: 'admin@finguard.ai', ip: '203.0.113.42', time: '2026-06-27 23:45:00 UTC', status: 'SUCCESS' }
  ];

  return (
    <Card title="System Audit Logs" subtitle="Immutable security telemetry trail of all administrative actions">
      <div className="overflow-x-auto">
        <table className="fg-table">
          <thead>
            <tr>
              <th>Log ID</th>
              <th>Action Event</th>
              <th>Triggered By</th>
              <th>IP Address</th>
              <th>Timestamp</th>
              <th>Result</th>
            </tr>
          </thead>
          <tbody>
            {logs.map(l => (
              <tr key={l.id}>
                <td className="font-mono text-cyan-400 font-bold">{l.id}</td>
                <td className="font-semibold text-slate-200"><FileCode size={12} className="inline mr-1" /> {l.action}</td>
                <td className="text-slate-300">{l.user}</td>
                <td className="font-mono text-slate-400">{l.ip}</td>
                <td className="text-slate-400">{l.time}</td>
                <td><Badge variant="success">{l.status}</Badge></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
