import React, { useState, useEffect } from 'react';
import { DashboardLayout } from '../layouts/DashboardLayout';
import { Card, Badge, Button, Input, Modal } from '../components/ui';
import { transactionService } from '../services/transactions';
import { Search, Filter, RefreshCw, Eye, Download } from 'lucide-react';
import { analyticsService } from "../services/analytics";
import { AIInvestigationPanel } from "../components/reports/AIInvestigationPanel";

export function Transactions() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedTx, setSelectedTx] = useState(null);
  const [investigationReport, setInvestigationReport] = useState(null);
  const [loadingReport, setLoadingReport] = useState(false);

  const [filters, setFilters] = useState({
    merchant: '',
    status: '',
    country: '',
    page: 1,
    page_size: 15
  });

  const fetchTransactions = async () => {
    setLoading(true);
    try {
      const res = await transactionService.listTransactions(filters);
      setData(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTransactions();
  }, [filters.page, filters.status, filters.country]);

  const handleSearch = (e) => {
    e.preventDefault();
    setFilters(prev => ({ ...prev, page: 1 }));
    fetchTransactions();
  };

  return (
    <DashboardLayout>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 tracking-tight">Financial Transactions Journal</h1>
          <p className="text-xs text-slate-400 mt-1">Audit log of all processed settlement events and automated risk classifications.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" size="sm" onClick={fetchTransactions} isLoading={loading}>
            <RefreshCw size={14} className="mr-1" /> Refresh
          </Button>
          <Button variant="outline" size="sm">
            <Download size={14} className="mr-1" /> Export CSV
          </Button>
        </div>
      </div>

      {/* Filter Bar */}
      <Card glass className="p-4">
        <form onSubmit={handleSearch} className="grid grid-cols-1 sm:grid-cols-4 gap-4 items-end">
          <Input
            label="Search Merchant"
            placeholder="e.g. Amazon, Binance..."
            value={filters.merchant}
            onChange={(e) => setFilters(prev => ({ ...prev, merchant: e.target.value }))}
            icon={Search}
          />
          <div>
            <label className="fg-label">Status Filter</label>
            <select
              value={filters.status}
              onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value, page: 1 }))}
              className="fg-input"
            >
              <option value="">All Statuses</option>
              <option value="COMPLETED">COMPLETED</option>
              <option value="PENDING">PENDING</option>
              <option value="FLAGGED">FLAGGED</option>
              <option value="FAILED">FAILED</option>
            </select>
          </div>
          <div>
            <label className="fg-label">Country</label>
            <select
              value={filters.country}
              onChange={(e) => setFilters(prev => ({ ...prev, country: e.target.value, page: 1 }))}
              className="fg-input"
            >
              <option value="">All Countries</option>
              <option value="USA">USA</option>
              <option value="GBR">United Kingdom</option>
              <option value="RU">Russia</option>
              <option value="DEU">Germany</option>
            </select>
          </div>
          <Button type="submit" variant="primary" size="md">
            <Filter size={14} className="mr-1.5" /> Apply Filters
          </Button>
        </form>
      </Card>

      {/* Transactions Table */}
      <Card glass className="overflow-hidden p-0">
        <div className="overflow-x-auto">
          <table className="fg-table">
            <thead>
              <tr>
                <th>Transaction ID</th>
                <th>Merchant</th>
                <th>Amount</th>
                <th>Channel</th>
                <th>Country</th>
                <th>Status</th>
                <th>Prediction</th>
                <th>Risk Score</th>
                <th className="text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i}>
                    <td colSpan={9} className="py-4 px-4"><div className="h-4 skeleton w-full" /></td>
                  </tr>
                ))
              ) : data && data.transactions.length > 0 ? (
                data.transactions.map((tx) => (
                  <tr key={tx._id || tx.transaction_id}>
                    <td className="font-mono text-cyan-400 font-bold">{tx.transaction_id}</td>
                    <td>
                      <div className="font-semibold text-slate-200">{tx.merchant_name}</div>
                      <span className="text-[10px] text-slate-500">{tx.merchant_category}</span>
                    </td>
                    <td className="font-mono font-bold text-slate-100">${tx.amount?.toFixed(2)}</td>
                    <td className="text-slate-400 text-xs">{tx.payment_method}</td>
                    <td className="font-mono text-slate-300">{tx.country}</td>
                    <td>
                      <Badge variant={
                        tx.status === 'COMPLETED' ? 'success' :
                          tx.status === 'FLAGGED' ? 'danger' :
                            tx.status === 'PENDING' ? 'warning' : 'neutral'
                      }>
                        {tx.status}
                      </Badge>
                    </td>
                    <td>
                      <span className={`text-xs font-bold ${tx.prediction === 'FRAUD' ? 'text-red-400' : 'text-emerald-400'}`}>
                        {tx.prediction || 'N/A'}
                      </span>
                    </td>
                    <td className="font-mono text-slate-300">{tx.risk_score ? `${tx.risk_score}` : '-'}</td>
                    <td className="text-right">
                      <button
                        onClick={async () => {
                          setSelectedTx(tx);

                          setLoadingReport(true);

                          try {
                            const report =
                              await analyticsService.getInvestigationReport(
                                tx.transaction_id
                              );

                            setInvestigationReport(report);

                          } catch (err) {
                            console.error(err);
                            setInvestigationReport(null);

                          } finally {
                            setLoadingReport(false);
                          }
                        }}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-cyan-400 hover:bg-slate-800 transition-colors"
                        title="View Details"
                      >
                        <Eye size={16} />
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={9} className="text-center py-8 text-slate-500 text-xs">
                    No transaction records matching criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        {data && (
          <div className="p-4 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
            <span>Showing page {data.page} of {data.total_pages} ({data.total_records} records)</span>
            <div className="flex gap-2">
              <Button
                variant="secondary"
                size="sm"
                disabled={data.page <= 1}
                onClick={() => setFilters(prev => ({ ...prev, page: prev.page - 1 }))}
              >
                Previous
              </Button>
              <Button
                variant="secondary"
                size="sm"
                disabled={data.page >= data.total_pages}
                onClick={() => setFilters(prev => ({ ...prev, page: prev.page + 1 }))}
              >
                Next
              </Button>
            </div>
          </div>
        )}
      </Card>

      {/* Details Modal */}
      <Modal
        isOpen={!!selectedTx}
        onClose={() => {
          setSelectedTx(null);
          setInvestigationReport(null);
        }}
        title="Transaction Telemetry Inspector"
        maxWidth='max-w-6xl'
      >
        {selectedTx && (
          <div className="space-y-4 text-xs">
            <div className="grid grid-cols-2 gap-4 p-3 rounded-lg bg-slate-900 border border-slate-800 font-mono">
              <div>
                <span className="text-slate-500 block text-[10px]">TRANSACTION ID</span>
                <span className="text-cyan-400 font-bold">{selectedTx.transaction_id}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px]">AMOUNT</span>
                <span className="text-slate-100 font-bold">${selectedTx.amount?.toFixed(2)} {selectedTx.currency}</span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2 text-slate-300">
              <div><strong>Merchant:</strong> {selectedTx.merchant_name} ({selectedTx.merchant_category})</div>
              <div><strong>Payment Method:</strong> {selectedTx.payment_method}</div>
              <div><strong>Origin IP:</strong> {selectedTx.ip_address}</div>
              <div><strong>Device ID:</strong> {selectedTx.device_id}</div>
              <div><strong>Geographic Country:</strong> {selectedTx.country}</div>
              <div><strong>Timestamp:</strong> {selectedTx.transaction_time}</div>
            </div>

            {/* AI Investigation Report */}

            <div className="pt-6 border-t border-slate-800">

              {loadingReport ? (

                <div className="text-center py-8 text-slate-400">
                  Generating AI Investigation Report...
                </div>

              ) : investigationReport ? (

                <AIInvestigationPanel report={investigationReport} />

              ) : (

                <div className="text-center py-8 text-slate-500">
                  Investigation report unavailable.
                </div>

              )}

            </div>

            <div className="pt-3 border-t border-slate-800 flex justify-end">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => {
                  setSelectedTx(null);
                  setInvestigationReport(null);
                }}
              >
                Close Inspector
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </DashboardLayout>
  );
}
