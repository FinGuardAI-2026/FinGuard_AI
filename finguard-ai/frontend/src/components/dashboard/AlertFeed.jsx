import React from 'react';
import { Card, Badge } from '../ui';
import { ShieldAlert, AlertTriangle, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

function getRelativeTime(timestamp) {
  if (!timestamp) return 'Unknown time';
  const now = new Date();
  const time = new Date(timestamp);

  if (isNaN(time.getTime())) return 'Unknown time';

  const diff = Math.floor((now - time) / 1000);

  if (diff < 60) return `${diff} sec ago`;

  if (diff < 3600)
    return `${Math.floor(diff / 60)} min ago`;

  if (diff < 86400)
    return `${Math.floor(diff / 3600)} hr ago`;

  return `${Math.floor(diff / 86400)} day ago`;
}

export function AlertFeed({ alerts = [] }) {
  const navigate = useNavigate();
  const safeAlerts = Array.isArray(alerts) ? alerts : [];

  return (
    <Card
      title="Live Risk Alerts"
      subtitle="Latest high-risk transactions detected"
      action={
        <button onClick={() => navigate('/transactions')} className="text-xs text-cyan-400 hover:underline flex items-center gap-1">
          View All <ArrowRight size={12} />
        </button>
      }
    >
      <div className="space-y-3">
        {safeAlerts.slice(0, 4).map((alert, index) => (
          <div
            key={alert?.transaction_id || index}
            onClick={() => navigate('/transactions')}
            className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800/80 hover:border-slate-700 hover:bg-slate-800/40 transition-all cursor-pointer flex items-center justify-between"          >
            <div className="flex items-center gap-3">
              <div
                className={`p-2 rounded-lg ${alert?.risk_level === "Critical"
                  ? "bg-red-500/10 text-red-400"
                  : alert?.risk_level === "High"
                    ? "bg-orange-500/10 text-orange-400"
                    : alert?.risk_level === "Medium"
                      ? "bg-yellow-500/10 text-yellow-400"
                      : "bg-cyan-500/10 text-cyan-400"
                  }`}
              >
                {alert?.risk_level === "Critical" ? (
                  <ShieldAlert size={16} />
                ) : alert?.risk_level === "High" ? (
                  <ShieldAlert size={16} />
                ) : (
                  <AlertTriangle size={18} />
                )}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-slate-200 font-mono">{alert?.transaction_id || 'N/A'}</span>
                  <span className="text-[11px] text-slate-500">{alert?.merchant_name || 'Unknown Merchant'}</span>
                </div>
                <span className="text-[11px] text-slate-500">
                  {getRelativeTime(alert?.transaction_time)}
                </span>              </div>
            </div>

            <div className="text-right">
              <div className="text-xs font-bold text-slate-100 font-mono">{new Intl.NumberFormat("en-US", {
                style: "currency",
                currency: "USD"
              }).format((alert?.amount !== undefined && alert?.amount !== null && !isNaN(Number(alert?.amount))) ? Number(alert?.amount) : 0)}</div>
              <Badge
                variant={
                  alert?.risk_level === "Critical"
                    ? "danger"
                    : alert?.risk_level === "High"
                      ? "warning"
                      : alert?.risk_level === "Medium"
                        ? "warning"
                        : "success"
                }
              >
                Score {alert?.risk_score !== undefined && alert?.risk_score !== null ? alert.risk_score : 0}
              </Badge>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
