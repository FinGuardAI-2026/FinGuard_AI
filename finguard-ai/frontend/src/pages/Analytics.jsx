import React, { useState, useEffect } from 'react';
import { DashboardLayout } from '../layouts/DashboardLayout';
import { ModelComparisonChart } from '../components/charts/ModelComparisonChart';
import { SHAPFeatureChart } from '../components/charts/SHAPFeatureChart';
import { FraudTrendChart } from '../components/charts/FraudTrendChart';
import { MerchantCategoryChart } from '../components/charts/MerchantCategoryChart';
import { analyticsService } from '../services/analytics';
import { BarChart3, Cpu, Layers } from 'lucide-react';

export function Analytics() {
  const [modelBenchmark, setModelBenchmark] = useState([]);
  const [shapImportance, setShapImportance] = useState([]);
  const [fraudTrend, setFraudTrend] = useState([]);
  const [merchantCat, setMerchantCat] = useState([]);

  useEffect(() => {
    const loadAnalytics = async () => {

      const benchmark =
        await analyticsService.getModelComparisonData();

      setModelBenchmark(benchmark);

      const shap =
        await analyticsService.getSHAPGlobalImportance();

      setShapImportance(shap);

      const fraud =
        await analyticsService.getFraudTrendData();

      setFraudTrend(fraud);

      const merchants =
        await analyticsService.getMerchantCategoryData();

      setMerchantCat(merchants);
    };

    loadAnalytics();
  }, []);

  return (
    <DashboardLayout>
      <div className="pb-2 border-b border-slate-800 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-cyan-400" />
            <h1 className="text-2xl font-bold text-slate-100 tracking-tight">Advanced Model Analytics</h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Deep neural feature importance metrics, benchmark ROC-AUC curve matrices, and SHAP attributions.
          </p>
        </div>
      </div>

      {/* Primary Analytics Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ModelComparisonChart data={modelBenchmark} />
        <SHAPFeatureChart data={shapImportance} />
      </div>

      {/* Secondary Analytics Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <FraudTrendChart data={fraudTrend} />
        <MerchantCategoryChart data={merchantCat} />
      </div>

      {/* Model Spec Card */}
      <div className="p-4 rounded-xl glass border border-slate-800 grid grid-cols-1 md:grid-cols-3 gap-4 text-xs text-slate-400">
        <div className="flex items-start gap-3">
          <Cpu className="w-5 h-5 text-cyan-400 flex-shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-slate-200 block">Champion Model Artifact</span>
            <span className="font-mono text-[11px]">champion_xgboost_v2.1.joblib</span>
          </div>
        </div>
        <div className="flex items-start gap-3">
          <Layers className="w-5 h-5 text-cyan-400 flex-shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-slate-200 block">Feature Dimension Space</span>
            <span>30 Features (Time, V1-V28, Amount)</span>
          </div>
        </div>
        <div className="flex items-start gap-3">
          <BarChart3 className="w-5 h-5 text-cyan-400 flex-shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-slate-200 block">Evaluation Metric Target</span>
            <span>PR-AUC (Precision-Recall AUC = 0.942)</span>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
