import React from 'react';
import { Card, Badge } from '../ui';
import { Monitor, Smartphone, Globe } from 'lucide-react';

function getRelativeTime(timestamp) {
  const now = new Date();
  const time = new Date(timestamp);
  const diff = Math.floor((now - time) / 1000);

  if (diff < 60) return `${diff} sec ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)} min ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)} hr ago`;
  return `${Math.floor(diff / 86400)} day ago`;
}

function getDeviceIcon(device) {
  switch (device?.toLowerCase()) {
    case 'mobile':
    case 'smartphone':
      return Smartphone;
    case 'desktop':
    case 'laptop':
      return Monitor;
    default:
      return Globe;
  }
}

export function RecentLogins({ logins = [] }) {
  return (
    <Card
      title="Recent Logins"
      subtitle="Latest authentication activity"
    >
      <div className="space-y-3">
        {logins.length === 0 ? (
          <div className="text-center py-8 text-slate-500 text-sm">
            No recent login activity
          </div>
        ) : (
          logins.map((login, index) => {
            const DeviceIcon = getDeviceIcon(login.device);
            return (
              <div
                key={index}
                className="p-3 rounded-lg bg-slate-900/80 border border-slate-800/80 hover:border-slate-700 transition-all flex items-center justify-between group"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400 group-hover:bg-cyan-500/20 transition-colors">
                    <DeviceIcon size={18} />
                  </div>
                  <div>
                    <div className="text-xs font-semibold text-slate-200">{login.user_name || 'Unknown User'}</div>
                    <div className="text-[11px] text-slate-500 mt-0.5">
                      {login.device} • {login.ip_address}                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-[11px] text-slate-400">{getRelativeTime(login.timestamp)}</div>
                  <Badge
                    variant={login.status === "Success" ? "success" : "danger"}
                    className="mt-1"
                  >
                    {login.status}
                  </Badge>
                </div>
              </div>
            );
          })
        )}
      </div>
    </Card>
  );
}
