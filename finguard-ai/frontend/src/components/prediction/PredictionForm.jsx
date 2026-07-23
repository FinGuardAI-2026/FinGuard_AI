import React, { useState } from 'react';
import { Card, Button, Input } from '../ui';
import { Sparkles, DollarSign } from 'lucide-react';

export function PredictionForm({ onSubmit, isLoading }) {
  // const [showAdvanced, setShowAdvanced] = useState(false);
  const [formData, setFormData] = useState({
    amount: '1250.75',
    transaction_id: `TXN-202606-${Math.floor(1000 + Math.random() * 9000)}`,
    merchant_name: 'Amazon Prime',
    merchant_category: 'RETAIL',
    payment_method: 'CREDIT_CARD',
    transaction_type: 'PURCHASE',
    country: 'USA',
    ip_address: '203.0.113.42',
    device_id: 'DEV-A1B2C3D4',
    generate_reports: true,
    // V1: '-1.359',
    // V2: '-0.072',
    // V3: '2.536',
    // V4: '1.378',
    // V10: '-0.090',
    // V11: '-0.551',
    // V12: '-0.617',
    // V14: '-0.311'
  });

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const amount = parseFloat(formData.amount);

    if (isNaN(amount) || amount <= 0) {
      alert("Transaction amount must be greater than 0.");
      return;
    }
    const payload = {
      ...formData,
      amount: parseFloat(formData.amount) || 0,
      generate_reports: formData.generate_reports
    };
    // Parse V features to numeric floats
    // for (let i = 1; i <= 28; i++) {
    //   const key = `V${i}`;
    //   if (formData[key] !== undefined) {
    //     payload[key] = parseFloat(formData[key]) || 0.0;
    //   }
    // }
    onSubmit(payload);
  };

  const fillSuspiciousPreset = () => {
    setFormData({
      amount: '9999.99',
      transaction_id: `TXN-SUSP-${Math.floor(1000 + Math.random() * 9000)}`,
      merchant_name: 'Unknown Crypto Exchange',
      merchant_category: 'ELECTRONICS',
      payment_method: 'WIRE',
      transaction_type: 'PURCHASE',
      country: 'GERMANY',
      ip_address: '185.220.101.1',
      device_id: 'DEV-UNKNOWN-XYZ',
      generate_reports: true
    });
  };

  const resetForm = () => {
    setFormData({
      amount: '1250.75',
      transaction_id: `TXN-202606-${Math.floor(1000 + Math.random() * 9000)}`,
      merchant_name: 'Amazon Prime',
      merchant_category: 'RETAIL',
      payment_method: 'CREDIT_CARD',
      country: 'USA',
      ip_address: '203.0.113.42',
      device_id: 'DEV-A1B2C3D4',
      generate_reports: true,
      // V1: '-1.359',
      // V2: '-0.072',
      // V3: '2.536',
      // V4: '1.378',
      // V10: '-0.090',
      // V11: '-0.551',
      // V12: '-0.617',
      // V14: '-0.311'
    });
  };

  return (
    <Card title="Transaction Risk Assessment Form" subtitle="Submit metadata and neural vectors to trigger AI prediction pipeline">
      {/* Preset Action Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 p-3 mb-5 rounded-lg bg-slate-900/80 border border-slate-800">
        <span className="text-xs text-slate-400 font-medium">Quick Test Scenarios:</span>
        <div className="flex flex-col sm:flex-row gap-2 w-full sm:w-auto">
          <button
            type="button"
            onClick={() => setFormData({
              amount: '42.50',
              transaction_id: `TXN-LEGIT-${Math.floor(1000 + Math.random() * 9000)}`,
              merchant_name: 'Starbucks Coffee',
              merchant_category: 'FOOD',
              payment_method: 'CREDIT_CARD',
              transaction_type: 'PURCHASE',
              country: 'USA',
              ip_address: '192.168.1.1',
              device_id: 'DEV-KNOWN-001',
              generate_reports: false
            })}
            className="w-full sm:w-auto px-2.5 py-1 text-[11px] rounded bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 font-medium"
          >
            Load Low-Risk
          </button>
          <button
            type="button"
            onClick={fillSuspiciousPreset}
            className="w-full sm:w-auto px-2.5 py-1 text-[11px] rounded bg-red-500/10 text-red-400 hover:bg-red-500/20 font-medium"
          >
            Load High-Risk
          </button>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            label="Transaction Amount ($)"
            name="amount"
            value={formData.amount}
            onChange={handleChange}
            required
            type="number"
            step="0.01"
            icon={DollarSign}
          />
          <Input
            label="Transaction ID"
            name="transaction_id"
            value={formData.transaction_id}
            onChange={handleChange}
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            label="Merchant Name"
            name="merchant_name"
            value={formData.merchant_name}
            onChange={handleChange}
          />
          <div>
            <label className="fg-label">Merchant Category (MCC)</label>
            <select
              name="merchant_category"
              value={formData.merchant_category}
              onChange={handleChange}
              className="fg-input"
            >
              <option value="ELECTRONICS">Electronics</option>
              <option value="FOOD">Food</option>
              <option value="GROCERY">Grocery</option>
              <option value="HEALTH">Health</option>
              <option value="RETAIL">Retail</option>
              <option value="TRAVEL">Travel</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="fg-label">Payment Method</label>
            <select
              name="payment_method"
              value={formData.payment_method}
              onChange={handleChange}
              className="fg-input"
            >
              <option value="CREDIT_CARD">Credit Card</option>
              <option value="DEBIT_CARD">Debit Card</option>
              <option value="UPI">UPI</option>
              <option value="WIRE">Wire Transfer</option>
            </select>
          </div>
          <div>
            <label className="fg-label">Transaction Type</label>
            <select
              name="transaction_type"
              value={formData.transaction_type}
              onChange={handleChange}
              className="fg-input"
            >
              <option value="PURCHASE">Purchase</option>
              <option value="TRANSFER">Transfer</option>
              <option value="WITHDRAWAL">Withdrawal</option>
            </select>
          </div>
          <div>
            <label className="fg-label">Country</label>
            <select
              name="country"
              value={formData.country}
              onChange={handleChange}
              className="fg-input"
            >
              <option value="USA">USA</option>
              <option value="INDIA">India</option>
              <option value="UK">United Kingdom</option>
              <option value="RU">Russia</option>
              <option value="GERMANY">Germany</option>
              <option value="FR">France</option>
            </select>
          </div>
          <Input
            label="IP Address"
            name="ip_address"
            value={formData.ip_address}
            onChange={handleChange}
          />
        </div>

        {/* AI Reports Checkbox Toggle */}
        <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <Sparkles className="w-4 h-4 text-cyan-400" />
            <div>
              <span className="text-xs font-semibold text-slate-200">Generate Gemini AI Reports</span>
              <p className="text-[11px] text-slate-400">Includes investigation, analyst, and executive summaries.</p>
            </div>
          </div>
          <input
            type="checkbox"
            name="generate_reports"
            checked={formData.generate_reports}
            onChange={handleChange}
            className="w-4 h-4 rounded bg-slate-800 border-slate-700 text-cyan-500 focus:ring-cyan-500/40"
          />
        </div>

        {/* Collapsible V-Features Panel */}
        {/* <div className="border-t border-slate-800/80 pt-3">
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center justify-between w-full py-2 text-xs font-semibold text-slate-400 hover:text-slate-200"
          >
            <span className="flex items-center gap-1.5">
              <Shield size={14} className="text-cyan-400" />
              PCA Neural Vectors (V1 - V28)
            </span>
            {showAdvanced ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>

          {showAdvanced && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-3 animate-fade-in">
              {['V1', 'V2', 'V3', 'V4', 'V10', 'V11', 'V12', 'V14'].map((vKey) => (
                <Input
                  key={vKey}
                  label={vKey}
                  name={vKey}
                  value={formData[vKey] || '0.0'}
                  onChange={handleChange}
                  type="number"
                  step="0.001"
                />
              ))}
            </div>
          )}
        </div> */}

        <Button type="submit" variant="primary" isLoading={isLoading} className="w-full py-3 mt-4 text-sm font-bold">
          Run AI Fraud Assessment
        </Button>
        <Button
          type="button"
          variant="secondary"
          onClick={resetForm}
          className="w-full mt-2"
        >
          Reset Form
        </Button>
      </form>
    </Card>
  );
}
