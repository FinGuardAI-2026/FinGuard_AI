import React from 'react';
import { Card, Badge } from '../ui';
import { RiskGauge } from './RiskGauge';
import { GeminiReport } from './GeminiReport';
import { ShieldCheck, ShieldAlert, AlertTriangle, Cpu, Clock, CheckCircle2 } from 'lucide-react';

export function PredictionResult({ result }) {
  if (!result) return null;

  const isFraud = result.prediction === 'FRAUD';

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Primary Status Header Card */}
      <Card className={`border-2 ${isFraud ? 'border-red-500/40 bg-red-950/20 glow-red' : 'border-emerald-500/40 bg-emerald-950/20 glow-green'}`}>
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className={`p-3.5 rounded-2xl ${isFraud ? 'bg-red-500/20 text-red-400' : 'bg-emerald-500/20 text-emerald-400'}`}>
              {isFraud ? <ShieldAlert size={36} /> : <ShieldCheck size={36} />}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-bold text-slate-100">{result.prediction} PREDICTION</h2>
                <Badge variant={isFraud ? 'danger' : 'success'}>
                  {result.confidence_score}% Confidence
                </Badge>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Transaction ID: <span className="font-mono text-cyan-400">{result.transaction_id}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4 text-xs text-slate-400 border-t md:border-t-0 md:border-l border-slate-800 pt-3 md:pt-0 md:pl-6">
            <div className="flex items-center gap-1.5">
              <Cpu size={14} className="text-cyan-400" />
              <span>{result.model_version}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Clock size={14} className="text-cyan-400" />
              <span>{result.processing_time_ms} ms</span>
            </div>
          </div>
        </div>
      </Card>

      {/* Grid: Risk Score Gauge vs Recommended Action */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card title="Calibrated Risk Score" subtitle="Composite score fusing ML, SHAP & Business Rules">
          <RiskGauge score={result.risk_assessment.risk_score} level={result.risk_assessment.risk_level} />
          
          <div className="mt-4 pt-4 border-t border-slate-800 grid grid-cols-3 gap-2 text-center text-xs">
            <div className="p-2 rounded bg-slate-900/60 border border-slate-800">
              <span className="text-slate-500 block text-[10px]">ML Prob</span>
              <span className="font-mono font-bold text-slate-200">{result.fraud_probability}%</span>
            </div>
            <div className="p-2 rounded bg-slate-900/60 border border-slate-800">
              <span className="text-slate-500 block text-[10px]">SHAP Mag</span>
              <span className="font-mono font-bold text-slate-200">{result.risk_assessment.score_breakdown.shap_contribution} pts</span>
            </div>
            <div className="p-2 rounded bg-slate-900/60 border border-slate-800">
              <span className="text-slate-500 block text-[10px]">Rules Penalty</span>
              <span className="font-mono font-bold text-slate-200">{result.risk_assessment.score_breakdown.rule_contribution} pts</span>
            </div>
          </div>
        </Card>

        <Card title="Action Recommendation" subtitle="Automated protocol decision derived from policy">
          <div className={`p-4 rounded-xl border mb-4 ${
            isFraud ? 'bg-red-500/10 border-red-500/30 text-red-200' : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-200'
          }`}>
            <div className="flex items-start gap-2.5">
              {isFraud ? <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" /> : <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5" />}
              <p className="text-xs font-medium leading-relaxed">
                {result.risk_assessment.investigation_recommendation}
              </p>
            </div>
          </div>

          <div className="space-y-2">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">Triggered Policy Rules:</span>
            {result.risk_assessment.triggered_rules && result.risk_assessment.triggered_rules.length > 0 ? (
              <ul className="space-y-1.5">
                {result.risk_assessment.triggered_rules.map((rule, idx) => (
                  <li key={idx} className="text-xs text-amber-400 bg-amber-500/10 border border-amber-500/20 px-2.5 py-1 rounded flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                    {rule}
                  </li>
                ))}
              </ul>
            ) : (
              <span className="text-xs text-slate-500 italic">No business rule penalties triggered.</span>
            )}
          </div>
        </Card>
      </div>

      {/* SHAP Feature Summary Section */}
      <Card title="SHAP Feature Explanation" subtitle="Top Neural Network attribution drivers for this transaction">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <span className="text-xs font-semibold text-red-400 uppercase tracking-wider mb-2 block">Risk Driver Attributions (+)</span>
            <ul className="space-y-2">
              {result.shap_explanation.narrative_risk_drivers && result.shap_explanation.narrative_risk_drivers.length > 0 ? (
                result.shap_explanation.narrative_risk_drivers.map((driver, idx) => (
                  <li key={idx} className="text-xs text-slate-300 p-2 rounded bg-slate-900/60 border border-slate-800">
                    {driver}
                  </li>
                ))
              ) : (
                <li className="text-xs text-slate-500 italic">No significant positive risk drivers detected.</li>
              )}
            </ul>
          </div>

          <div>
            <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-2 block">Mitigating Attributions (-)</span>
            <ul className="space-y-2">
              {result.shap_explanation.narrative_mitigating_factors && result.shap_explanation.narrative_mitigating_factors.length > 0 ? (
                result.shap_explanation.narrative_mitigating_factors.map((factor, idx) => (
                  <li key={idx} className="text-xs text-slate-300 p-2 rounded bg-slate-900/60 border border-slate-800">
                    {factor}
                  </li>
                ))
              ) : (
                <li className="text-xs text-slate-500 italic">No significant mitigating factors detected.</li>
              )}
            </ul>
          </div>
        </div>

        {/* Top 5 Features Table */}
        {result.top_features && result.top_features.length > 0 && (
          <div className="mt-4 pt-4 border-t border-slate-800">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 block">Top Feature Attributions Matrix</span>
            <div className="overflow-x-auto">
              <table className="fg-table">
                <thead>
                  <tr>
                    <th>Rank</th>
                    <th>Feature</th>
                    <th>Feature Value</th>
                    <th>SHAP Impact</th>
                  </tr>
                </thead>
                <tbody>
                  {result.top_features.map((f) => (
                    <tr key={f.rank}>
                      <td className="font-mono text-cyan-400">#{f.rank}</td>
                      <td className="font-semibold text-slate-200">{f.feature}</td>
                      <td className="font-mono text-slate-400">{f.feature_value}</td>
                      <td className={`font-mono font-bold ${f.shap_value >= 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                        {f.shap_value >= 0 ? `+${f.shap_value}` : f.shap_value}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </Card>

      {/* Gemini AI Reports */}
      {result.gemini_reports && <GeminiReport reports={result.gemini_reports} />}
    </div>
  );
}
