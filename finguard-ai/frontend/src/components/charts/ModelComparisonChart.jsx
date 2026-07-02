import React from "react";
import { Card, Badge } from "../ui";
import { Trophy, Cpu, Timer, Activity } from "lucide-react";

export function ModelComparisonChart({ data }) {
  if (!data || data.length === 0) {
    return (
      <Card
        title="ML Model Benchmark Comparison"
        subtitle="Live benchmark metrics from trained models"
      >
        <div className="py-12 text-center text-slate-400">
          No model performance data available.
        </div>
      </Card>
    );
  }

  const bestAccuracy = data.reduce((a, b) =>
    a.Accuracy > b.Accuracy ? a : b
  );

  const bestROC = data.reduce((a, b) =>
    a.ROC_AUC > b.ROC_AUC ? a : b
  );

  const fastestTraining = data.reduce((a, b) =>
    a.training_time_s < b.training_time_s ? a : b
  );

  const fastestInference = data.reduce((a, b) =>
    a.inference_time_per_sample_ms < b.inference_time_per_sample_ms ? a : b
  );

  const formatModel = (name) =>
    name
      .replaceAll("_", " ")
      .replace(/\b\w/g, c => c.toUpperCase());

  return (
    <Card
      title="ML Model Benchmark Comparison"
      subtitle="Live benchmark metrics from trained models"
    >
      <div className="overflow-x-auto">

        <table className="min-w-full text-sm">

          <thead className="border-b border-slate-700">

            <tr className="text-slate-400">

              <th className="text-left py-3">Model</th>

              <th>Accuracy</th>

              <th>Precision</th>

              <th>Recall</th>

              <th>F1</th>

              <th>ROC-AUC</th>

            </tr>

          </thead>

          <tbody>

            {data.map((model) => (

              <tr
                key={model.metric}
                className="border-b border-slate-800 hover:bg-slate-800/30"
              >

                <td className="py-3 font-semibold text-slate-200">

                  {formatModel(model.metric)}

                </td>

                <td className="text-center">{model.Accuracy}%</td>

                <td className="text-center">{model.Precision}%</td>

                <td className="text-center">{model.Recall}%</td>

                <td className="text-center">{model.F1}%</td>

                <td className="text-center">{model.ROC_AUC}%</td>

              </tr>

            ))}

          </tbody>

        </table>

      </div>

      <div className="grid md:grid-cols-2 gap-3 mt-6">

        <div className="flex items-center gap-3 p-3 rounded-lg bg-slate-900">

          <Trophy className="text-yellow-400" size={20} />

          <div>

            <div className="text-xs text-slate-400">
              Best Accuracy
            </div>

            <div className="font-semibold text-slate-100">
              {formatModel(bestAccuracy.metric)}
            </div>

          </div>

          <Badge variant="success">
            {bestAccuracy.Accuracy}%
          </Badge>

        </div>

        <div className="flex items-center gap-3 p-3 rounded-lg bg-slate-900">

          <Activity className="text-cyan-400" size={20} />

          <div>

            <div className="text-xs text-slate-400">
              Best ROC-AUC
            </div>

            <div className="font-semibold text-slate-100">
              {formatModel(bestROC.metric)}
            </div>

          </div>

          <Badge variant="primary">
            {bestROC.ROC_AUC}%
          </Badge>

        </div>

        <div className="flex items-center gap-3 p-3 rounded-lg bg-slate-900">

          <Timer className="text-green-400" size={20} />

          <div>

            <div className="text-xs text-slate-400">
              Fastest Training
            </div>

            <div className="font-semibold text-slate-100">
              {formatModel(fastestTraining.metric)}
            </div>

          </div>

          <Badge variant="secondary">
            {fastestTraining.training_time_s?.toFixed(2) ?? "N/A"} s
          </Badge>

        </div>

        <div className="flex items-center gap-3 p-3 rounded-lg bg-slate-900">

          <Cpu className="text-purple-400" size={20} />

          <div>

            <div className="text-xs text-slate-400">
              Fastest Inference
            </div>

            <div className="font-semibold text-slate-100">
              {formatModel(fastestInference.metric)}
            </div>

          </div>

          <Badge variant="secondary">
            {fastestInference.inference_time_per_sample_ms?.toFixed(4) ?? "N/A"} ms          
          </Badge>

        </div>

      </div>

    </Card>
  );
}