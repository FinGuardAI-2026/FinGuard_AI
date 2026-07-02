import React, { useState } from 'react';
import { DashboardLayout } from '../layouts/DashboardLayout';
import { Card, Button, Input } from '../components/ui';
import { Settings as SettingsIcon, Key, Sliders, Bell } from 'lucide-react';

export function Settings() {
  const [saved, setSaved] = useState(false);

  const handleSave = (e) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <DashboardLayout>
      <div className="pb-2 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <SettingsIcon className="w-6 h-6 text-cyan-400" />
          <h1 className="text-2xl font-bold text-slate-100 tracking-tight">System & Engine Configuration</h1>
        </div>
        <p className="text-xs text-slate-400 mt-1">Manage API keys, model decision thresholds, and notifications.</p>
      </div>

      {saved && (
        <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold">
          Configuration changes saved successfully.
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-6">
        {/* Gemini API Key */}
        <Card title="Google Gemini API Configuration" subtitle="API credential for generating automated markdown intelligence reports">
          <Input
            label="Gemini API Key"
            type="password"
            defaultValue="AIzaSyA889210_DEMO_KEY_FINGUARD"
            icon={Key}
            helperText="Stored securely in environment variables."
          />
        </Card>

        {/* Risk Threshold Sliders */}
        <Card title="Risk Engine Calibration Thresholds" subtitle="Adjust decision boundaries for automated risk band classification">
          <div className="space-y-4 text-xs">
            <div>
              <div className="flex justify-between text-slate-300 font-semibold mb-1">
                <span>Low / Medium Threshold (Score: 30)</span>
              </div>
              <input type="range" min="10" max="40" defaultValue="30" className="w-full accent-cyan-400" />
            </div>
            <div>
              <div className="flex justify-between text-slate-300 font-semibold mb-1">
                <span>Medium / High Threshold (Score: 60)</span>
              </div>
              <input type="range" min="41" max="75" defaultValue="60" className="w-full accent-amber-400" />
            </div>
            <div>
              <div className="flex justify-between text-slate-300 font-semibold mb-1">
                <span>High / Critical Threshold (Score: 85)</span>
              </div>
              <input type="range" min="76" max="95" defaultValue="85" className="w-full accent-red-400" />
            </div>
          </div>
        </Card>

        <Button type="submit" variant="primary" className="py-2.5 px-6 font-bold">
          Save System Preferences
        </Button>
      </form>
    </DashboardLayout>
  );
}
