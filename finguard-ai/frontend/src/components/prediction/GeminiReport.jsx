import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import {
  FileText,
  ShieldAlert,
  UserCheck,
  Briefcase,
  Bell,
  Copy,
  Check
} from 'lucide-react';

export function GeminiReport({ reports }) {
  const [activeTab, setActiveTab] = useState('fraud_investigation');
  const [copied, setCopied] = useState(false);

  if (!reports) return null;

  const tabs = [
    { id: 'fraud_investigation', label: 'Investigation Case', icon: ShieldAlert },
    { id: 'analyst_summary', label: 'Analyst Brief', icon: UserCheck },
    { id: 'executive_summary', label: 'Executive Summary', icon: Briefcase },
    { id: 'customer_notification', label: 'Customer Notice', icon: Bell },
  ];

  const handleCopy = async () => {
    if (!reports?.[activeTab]) return;
    try {
      await navigator.clipboard.writeText(reports[activeTab]);
      setCopied(true);
      setTimeout(() => {
        setCopied(false);
      }, 2000);
    } catch (err) {
      console.error("Failed to copy report:", err);
    }
  };

  return (
    <div className="mt-6 border-t border-slate-800 pt-6">
      <div className="flex items-center gap-2 mb-4">
        <FileText className="w-5 h-5 text-cyan-400" />
        <h3 className="text-base font-semibold text-slate-100">Gemini AI Intelligence Reports</h3>
      </div>

      {/* Tabs Header */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 border-b border-slate-800">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold whitespace-nowrap transition-all ${isActive
                  ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 shadow-lg shadow-cyan-500/10'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
            >
              <Icon size={14} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Report Content Panel */}
      <div className="mt-4">
        <div className="flex justify-end mb-3">
          <button
            onClick={handleCopy}
            className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition-colors"
          >
            {copied ? (
              <>
                <Check size={14} className="text-emerald-400" />
                Copied
              </>
            ) : (
              <>
                <Copy size={14} />
                Copy Report
              </>
            )}
          </button>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800/80 max-h-96 overflow-y-auto markdown-body">
          {reports[activeTab] ? (
            <ReactMarkdown>{reports[activeTab]}</ReactMarkdown>
          ) : (
            <p className="text-xs text-slate-500 italic">
              No report content available for this tab.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
