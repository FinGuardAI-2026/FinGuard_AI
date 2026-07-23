import React, { useState, useEffect, useCallback } from 'react';
import { adminService } from '../../services/admin';
import { Card, Badge, Button, Input, Modal, Spinner } from '../../components/ui';
import { formatDateTime } from '../../utils/dateFormatter';
import {
  Search,
  Download,
  ChevronLeft,
  ChevronRight,
  Eye,
  Copy,
  Check,
  FileCode,
  Printer
} from 'lucide-react';

export function AuditLogs() {
  const [logs, setLogs] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [actionFilter, setActionFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  // Pagination
  const [page, setPage] = useState(1);
  const limit = 15;

  // Selected Log Details
  const [selectedLog, setSelectedLog] = useState(null);
  const [copiedId, setCopiedId] = useState(null);

  const fetchLogs = useCallback(async () => {
    try {
      setLoading(true);
      const params = {
        limit,
        offset: (page - 1) * limit,
        query: searchQuery || undefined,
        action: actionFilter || undefined,
        status_filter: statusFilter || undefined
      };
      const result = await adminService.listAuditLogs(params);
      setLogs(result.logs);
      setTotal(result.total);
    } catch (err) {
      console.error('Failed to load compliance audit logs:', err);
    } finally {
      setLoading(false);
    }
  }, [page, searchQuery, actionFilter, statusFilter]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchLogs();
  };

  const handleSearchChange = (e) => {
    setSearchQuery(e.target.value);
  };

  const handleClearFilters = () => {
    setSearchQuery('');
    setActionFilter('');
    setStatusFilter('');
    setPage(1);
    // Reloads logs automatically
    setTimeout(() => fetchLogs(), 0);
  };

  const handleCopyRequestId = (reqId) => {
    navigator.clipboard.writeText(reqId);
    setCopiedId(reqId);
    setTimeout(() => setCopiedId(null), 2000);
  };

  // Browser parser helper
  const formatBrowser = (userAgent) => {
    if (!userAgent) return 'System / Daemon';
    const ua = userAgent.toLowerCase();
    let os = 'Unknown OS';
    let browser = 'Browser';

    if (ua.includes('windows')) os = 'Windows';
    else if (ua.includes('macintosh') || ua.includes('mac os')) os = 'macOS';
    else if (ua.includes('iphone') || ua.includes('ipad')) os = 'iOS';
    else if (ua.includes('android')) os = 'Android';
    else if (ua.includes('linux')) os = 'Linux';

    if (ua.includes('chrome') && !ua.includes('chromium')) browser = 'Chrome';
    else if (ua.includes('firefox')) browser = 'Firefox';
    else if (ua.includes('safari') && !ua.includes('chrome')) browser = 'Safari';
    else if (ua.includes('edge') || ua.includes('edg')) browser = 'Edge';

    return `${browser} on ${os}`;
  };

  // ── Client-side Export Methods ────────────────────────────────────────────

  const convertToCSV = (data) => {
    const headers = ['Log ID', 'Action Event', 'Triggered By', 'IP Address', 'Browser / Client', 'Endpoint Route', 'Request ID', 'Timestamp', 'Status', 'Details'];
    const rows = data.map(l => [
      l.id,
      l.action,
      l.performed_by,
      l.ip_address,
      l.browser ? l.browser.replace(/"/g, '""') : '',
      l.endpoint,
      l.request_id,
      l.timestamp,
      l.status,
      l.details ? l.details.replace(/"/g, '""') : ''
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map(r => r.map(val => `"${val}"`).join(','))
    ].join('\r\n');

    return csvContent;
  };

  const handleExportCSV = async () => {
    try {
      // Fetch larger batch of logs for exporting (up to 500 logs)
      const data = await adminService.listAuditLogs({ limit: 500 });
      const csv = convertToCSV(data.logs);
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.setAttribute('href', url);
      link.setAttribute('download', `finguard_compliance_audit_${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch {
      alert('Failed to export CSV report.');
    }
  };

  const handleExportExcel = async () => {
    try {
      // Excel works perfectly opening a tab-separated values or UTF-8 CSV
      const data = await adminService.listAuditLogs({ limit: 500 });
      const csv = convertToCSV(data.logs);
      const blob = new Blob([csv], { type: 'application/vnd.ms-excel;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.setAttribute('href', url);
      link.setAttribute('download', `finguard_compliance_audit_${new Date().toISOString().split('T')[0]}.xls`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch {
      alert('Failed to export Excel report.');
    }
  };

  const handleExportPDF = async () => {
    try {
      const data = await adminService.listAuditLogs({ limit: 50 });

      // Open a printable window
      const printWindow = window.open('', '_blank');
      if (!printWindow) {
        alert('Please allow popups to export PDF printouts.');
        return;
      }

      const htmlContent = `
        <html>
          <head>
            <title>Compliance Audit Logs - FinGuard AI</title>
            <style>
              body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 10px; color: #1e293b; padding: 20px; }
              header { border-bottom: 2px solid #0f172a; padding-bottom: 10px; margin-bottom: 20px; }
              h1 { font-size: 16px; margin: 0; color: #0f172a; }
              p.meta { margin: 5px 0 0; color: #64748b; font-size: 8px; }
              table { width: 100%; border-collapse: collapse; margin-top: 10px; }
              th { background-color: #f1f5f9; text-align: left; font-weight: bold; border-bottom: 1px solid #cbd5e1; padding: 6px; }
              td { padding: 6px; border-bottom: 1px solid #e2e8f0; vertical-align: top; word-break: break-all; }
              .status-success { color: #10b981; font-weight: bold; }
              .status-failed { color: #ef4444; font-weight: bold; }
              .mono { font-family: monospace; }
            </style>
          </head>
          <body>
            <header>
              <h1>FinGuard AI Compliance Audit Trail Report</h1>
              <p class="meta">Exported on: ${formatDateTime(new Date())} • Total Rows: ${data.logs.length}</p>
            </header>
            <table>
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Action</th>
                  <th>Performed By</th>
                  <th>IP Address</th>
                  <th>Request ID</th>
                  <th>Result</th>
                  <th>Description</th>
                </tr>
              </thead>
              <tbody>
                ${data.logs.map(l => `
                  <tr>
                    <td>${l.timestamp ? formatDateTime(l.timestamp) : 'N/A'}</td>
                    <td><b>${l.action}</b></td>
                    <td>${l.performed_by}</td>
                    <td class="mono">${l.ip_address}</td>
                    <td class="mono">${l.request_id ? l.request_id.substring(0, 8) : ''}...</td>
                    <td class="${l.status === 'SUCCESS' ? 'status-success' : 'status-failed'}">${l.status}</td>
                    <td>${l.details || ''}</td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
            <script>
              window.onload = function() {
                window.print();
                window.close();
              }
            </script>
          </body>
        </html>
      `;

      printWindow.document.write(htmlContent);
      printWindow.document.close();
    } catch {
      alert('Failed to export PDF.');
    }
  };

  const getActionBadgeVariant = (action) => {
    if (action.includes('DELETE')) return 'danger';
    if (action.includes('CREATE') || action.includes('EDIT')) return 'warning';
    if (action.includes('LOGIN')) return 'success';
    return 'info';
  };

  const totalPages = Math.ceil(total / limit);

  return (
    <Card
      title="Compliance Audit Trails"
      subtitle="SOC2 and PCI-DSS compliant telemetry logs detailing every system administrative action."
      action={
        <div className="flex flex-col sm:flex-row gap-2 w-full sm:w-auto">
          <Button variant="secondary" className="w-full sm:w-auto" size="sm" onClick={handleExportCSV}>
            <Download size={12} className="mr-1.5" /> CSV
          </Button>
          <Button variant="secondary" className="w-full sm:w-auto" size="sm" onClick={handleExportExcel}>
            <Download size={12} className="mr-1.5" /> Excel
          </Button>
          <Button variant="secondary" className="w-full sm:w-auto" size="sm" onClick={handleExportPDF}>
            <Printer size={12} className="mr-1.5" /> PDF Print
          </Button>
        </div>
      }
    >
      {/* Filters Form */}
      <form onSubmit={handleSearchSubmit} className="grid grid-cols-1 sm:grid-cols-4 gap-3 mb-4">
        <Input
          placeholder="Search logs by keyword..."
          value={searchQuery}
          onChange={handleSearchChange}
          icon={Search}
          className="w-full"
        />

        <select
          className="fg-input"
          value={actionFilter}
          onChange={(e) => { setActionFilter(e.target.value); setPage(1); }}
        >
          <option value="">All Action Events</option>
          <option value="USER_LOGIN">USER_LOGIN</option>
          <option value="USER_CREATE">USER_CREATE</option>
          <option value="USER_EDIT">USER_EDIT</option>
          <option value="USER_DELETE">USER_DELETE</option>
          <option value="PASSWORD_RESET">PASSWORD_RESET</option>
          <option value="SESSION_REVOKE">SESSION_REVOKE</option>
          <option value="RBAC_MATRIX_UPDATE">RBAC_MATRIX_UPDATE</option>
        </select>

        <select
          className="fg-input"
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
        >
          <option value="">All Results</option>
          <option value="SUCCESS">SUCCESS</option>
          <option value="FAILED">FAILED</option>
        </select>

        <div className="flex flex-col sm:flex-row gap-2">          <Button variant="primary" type="submit" className="flex-1">
          Apply Filters
        </Button>
          <Button variant="secondary" className="w-full sm:w-auto" onClick={handleClearFilters} type="button" title="Clear filters">
            Clear
          </Button>
        </div>
      </form>

      {/* Audit Logs Table */}
      {loading && logs.length === 0 ? (
        <div className="flex justify-center items-center py-20">
          <Spinner size="lg" />
        </div>
      ) : (
        <div className="space-y-4">
          <div className="overflow-x-auto border border-slate-800 rounded-xl">
            <table className="fg-table">
              <thead>
                <tr>
                  <th>Timestamp (IST)</th>
                  <th>Action</th>
                  <th>Investigator</th>
                  <th>IP Address</th>
                  <th>Browser / Client</th>
                  <th className="w-36">Request ID</th>
                  <th>Status</th>
                  <th className="text-right">Action</th>
                </tr>
              </thead>
              <tbody>
                {logs.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="text-center py-10 text-xs text-slate-500">
                      No compliance logs found matching your filters.
                    </td>
                  </tr>
                ) : (
                  logs.map(l => (
                    <tr key={l.id} className="hover:bg-slate-800/10 transition-colors">
                      <td className="text-slate-400 font-mono text-[11px] whitespace-nowrap">
                        {l.timestamp ? formatDateTime(l.timestamp) : 'N/A'}
                      </td>
                      <td>
                        <Badge variant={getActionBadgeVariant(l.action)} className="text-[9px]">
                          <FileCode size={9} className="mr-1 inline" /> {l.action}
                        </Badge>
                      </td>
                      <td className="text-slate-200 font-medium">{l.performed_by}</td>
                      <td className="font-mono text-slate-400 text-xs">{l.ip_address}</td>
                      <td className="text-slate-400 text-xs whitespace-nowrap overflow-hidden text-ellipsis max-w-[140px]">
                        {formatBrowser(l.browser)}
                      </td>
                      <td>
                        <div className="flex items-center gap-1">
                          <span className="font-mono text-cyan-400/80 text-[10px] uppercase">
                            {l.request_id ? `${l.request_id.substring(0, 8)}...` : 'n/a'}
                          </span>
                          {l.request_id && (
                            <button
                              onClick={() => handleCopyRequestId(l.request_id)}
                              className="p-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white"
                              title="Copy full Request ID"
                            >
                              {copiedId === l.request_id ? <Check size={10} className="text-emerald-400" /> : <Copy size={10} />}
                            </button>
                          )}
                        </div>
                      </td>
                      <td>
                        <Badge variant={l.status === 'SUCCESS' ? 'success' : 'danger'} className="text-[9px]">
                          {l.status}
                        </Badge>
                      </td>
                      <td className="text-right">
                        <button
                          onClick={() => setSelectedLog(l)}
                          className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-all"
                          title="View raw details"
                        >
                          <Eye size={12} />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pt-2">
              <span className="text-[10px] text-slate-400">
                Showing page <span className="text-slate-200 font-semibold">{page}</span> of <span className="text-slate-200 font-semibold">{totalPages}</span> (Total logs: {total})
              </span>
              <div className="flex justify-center sm:justify-end items-center gap-1.5 flex-wrap">
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={page === 1}
                  onClick={() => setPage(prev => Math.max(prev - 1, 1))}
                >
                  <ChevronLeft size={14} className="mr-1" /> Prev
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={page === totalPages}
                  onClick={() => setPage(prev => Math.min(prev + 1, totalPages))}
                >
                  Next <ChevronRight size={14} className="ml-1" />
                </Button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Raw Audit Log Details Modal */}
      <Modal isOpen={selectedLog !== null} onClose={() => setSelectedLog(null)} title="Compliance Telemetry Record Details" maxWidth="max-w-xl">
        {selectedLog && (
          <div className="space-y-4 text-xs">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-slate-500 font-bold uppercase block text-[10px]">Action Event</span>
                <span className="text-slate-200 font-semibold text-sm mt-0.5 block">{selectedLog.action}</span>
              </div>
              <div>
                <span className="text-slate-500 font-bold uppercase block text-[10px]">Result State</span>
                <Badge variant={selectedLog.status === 'SUCCESS' ? 'success' : 'danger'} className="mt-1">
                  {selectedLog.status}
                </Badge>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-slate-800">
              <div>
                <span className="text-slate-500 font-bold uppercase block text-[10px]">Triggered By</span>
                <span className="text-slate-200 font-mono mt-0.5 block">{selectedLog.performed_by}</span>
              </div>
              <div>
                <span className="text-slate-500 font-bold uppercase block text-[10px]">Timestamp (IST)</span>
                <span className="text-slate-200 font-mono mt-0.5 block">
                  {selectedLog.timestamp ? formatDateTime(selectedLog.timestamp) : 'N/A'}
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-slate-800">
              <div>
                <span className="text-slate-500 font-bold uppercase block text-[10px]">Client IP Address</span>
                <span className="text-slate-200 font-mono mt-0.5 block">{selectedLog.ip_address}</span>
              </div>
              <div>
                <span className="text-slate-500 font-bold uppercase block text-[10px]">API Endpoint Router</span>
                <span className="text-slate-200 font-mono mt-0.5 block">{selectedLog.endpoint}</span>
              </div>
            </div>

            <div className="pt-2 border-t border-slate-800">
              <span className="text-slate-500 font-bold uppercase block text-[10px] mb-1">X-Request-ID Header</span>
              <div className="flex items-center gap-2 p-2 rounded bg-slate-900 border border-slate-800 font-mono text-cyan-400">
                <span className="flex-1 break-all">{selectedLog.request_id || 'n/a'}</span>
                {selectedLog.request_id && (
                  <button
                    onClick={() => handleCopyRequestId(selectedLog.request_id)}
                    className="p-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white"
                    title="Copy Request ID"
                  >
                    {copiedId === selectedLog.request_id ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
                  </button>
                )}
              </div>
            </div>

            <div className="pt-2 border-t border-slate-800">
              <span className="text-slate-500 font-bold uppercase block text-[10px] mb-1">Client User Agent</span>
              <p className="p-2 rounded bg-slate-900 border border-slate-800 text-slate-300 font-mono break-words">
                {selectedLog.browser || 'System'}
              </p>
            </div>

            <div className="pt-2 border-t border-slate-800">
              <span className="text-slate-500 font-bold uppercase block text-[10px] mb-1">Action Description</span>
              <p className="p-3 rounded bg-slate-900 border border-slate-800 text-slate-300 font-semibold leading-relaxed">
                {selectedLog.details || 'No action summary available.'}
              </p>
            </div>

            <div className="flex pt-3 border-t border-slate-800">
              <Button variant="secondary" className="w-full sm:w-auto"
                onClick={() => setSelectedLog(null)}>
                Dismiss
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </Card>
  );
}
