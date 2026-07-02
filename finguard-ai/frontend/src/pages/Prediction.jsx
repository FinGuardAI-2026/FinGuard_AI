import React, { useState } from 'react';
import { DashboardLayout } from '../layouts/DashboardLayout';
import { PredictionForm } from '../components/prediction/PredictionForm';
import { PredictionResult } from '../components/prediction/PredictionResult';
import { predictionService } from '../services/prediction';
import { Sparkles, History, Info } from 'lucide-react';

export function Prediction() {
  const [predictionResult, setPredictionResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [history, setHistory] = useState([]);

  const handlePredict = async (payload) => {
    setIsLoading(true);
    try {
      const res = await predictionService.predict(payload);
      setPredictionResult(res);
      setHistory(prev => [res, ...prev.slice(0, 4)]);
    } catch (err) {
      console.error('Prediction failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="pb-2 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Sparkles className="w-6 h-6 text-cyan-400" />
          <h1 className="text-2xl font-bold text-slate-100 tracking-tight">AI Prediction Engine</h1>
        </div>
        <p className="text-xs text-slate-400 mt-1">
          Simulate online financial transactions through the multi-stage XGBoost, SHAP & Gemini pipeline.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Input Form */}
        <div className="lg:col-span-5">
          <PredictionForm onSubmit={handlePredict} isLoading={isLoading} />
        </div>

        {/* Right Column: Result Panel or Placeholder */}
        <div className="lg:col-span-7">
          {predictionResult ? (
            <PredictionResult result={predictionResult} />
          ) : (
            <div className="h-full min-h-[400px] glass rounded-xl border border-dashed border-slate-800 flex flex-col items-center justify-center p-8 text-center">
              <div className="w-16 h-16 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-500 mb-4">
                <Info size={32} />
              </div>
              <h3 className="text-base font-semibold text-slate-300">Awaiting Transaction Parameters</h3>
              <p className="text-xs text-slate-500 max-w-sm mt-1">
                Fill in the form on the left or load a preset scenario to run real-time inference, SHAP attributions, and Gemini reports.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* History Log Bar */}
      {history.length > 0 && (
        <div className="mt-8 pt-6 border-t border-slate-800">
          <div className="flex items-center gap-2 mb-3">
            <History className="w-4 h-4 text-slate-400" />
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Session Prediction History</h3>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
            {history.map((h, i) => (
              <div
                key={i}
                onClick={() => setPredictionResult(h)}
                className={`p-3 rounded-lg bg-slate-900/60 border hover:bg-slate-800/50 cursor-pointer transition-colors flex items-center justify-between ${
                  h.prediction === 'FRAUD' ? 'border-red-500/30' : 'border-emerald-500/30'
                }`}
              >
                <div>
                  <span className="text-xs font-bold text-slate-200 font-mono block">{h.transaction_id}</span>
                  <span className="text-[11px] text-slate-500">{h.model_version}</span>
                </div>
                <span className={`text-xs font-bold ${h.prediction === 'FRAUD' ? 'text-red-400' : 'text-emerald-400'}`}>
                  {h.prediction}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </DashboardLayout>
  );
}
