import React, { useState, useEffect } from 'react';
import { DashboardLayout } from '../layouts/DashboardLayout';
import { StatCard } from '../components/dashboard/StatCard';
import { AlertFeed } from '../components/dashboard/AlertFeed';
import { FraudTrendChart } from '../components/charts/FraudTrendChart';
import { RiskTrendChart } from '../components/charts/RiskTrendChart';
import { CountryChart } from '../components/charts/CountryChart';
import { PaymentMethodChart } from '../components/charts/PaymentMethodChart';
import { MerchantCategoryChart } from '../components/charts/MerchantCategoryChart';
import { analyticsService } from '../services/analytics';
import { Receipt, ShieldAlert, Percent, PieChart as PieIcon, Clock, AlertTriangle, ArrowUpRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export function Dashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [fraudTrend, setFraudTrend] = useState([]);
  const [riskTrend, setRiskTrend] = useState([]);
  const [countries, setCountries] = useState([]);
  const [paymentMethods, setPaymentMethods] = useState([]);
  const [merchantCategories, setMerchantCategories] = useState([]);
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    const loadDashboard = async () => {
      try {
        const dashboardStats = await analyticsService.getDashboardStats();
        setStats(dashboardStats);

        const fraudTrendData = await analyticsService.getFraudTrendData();
        setFraudTrend(fraudTrendData);

        const riskTrendData = await analyticsService.getRiskTrendData();
        setRiskTrend(riskTrendData);

        const countries = await analyticsService.getCountryDistribution();
        setCountries(countries);

        const paymentMethods = await analyticsService.getPaymentMethodData();
        setPaymentMethods(paymentMethods);

        const merchantCategories = await analyticsService.getMerchantCategoryData();
        setMerchantCategories(merchantCategories);

        const alerts = await analyticsService.getLiveAlerts();
        setAlerts(alerts);

      } catch (error) {
        console.error("Failed to load dashboard:", error);
      }
    };

    loadDashboard();
  }, []);

  if (!stats) return null;

  return (
    <DashboardLayout>
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 tracking-tight">Enterprise Risk Executive Overview</h1>
          <p className="text-xs text-slate-400 mt-1">Real-time fraud surveillance telemetry and active AI model metrics.</p>
        </div>
        <button
          onClick={() => navigate('/prediction')}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 text-xs font-bold transition-all shadow-lg shadow-cyan-500/20"
        >
          <span>Run AI Risk Scan</span>
          <ArrowUpRight size={16} />
        </button>
      </div>

      {/* 6 Required Dashboard Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-6 gap-4">
        <StatCard
          title="Total Txns"
          value={stats.totalTransactions.toLocaleString()}
          change={stats.totalTransactionsChange}
          icon={Receipt}
          color="cyan"
        />
        <StatCard
          title="Fraud Cases"
          value={stats.fraudTransactions.toLocaleString()}
          change={stats.fraudTransactionsChange}
          isNegativeGood
          icon={ShieldAlert}
          color="red"
        />
        <StatCard
          title="Fraud % Rate"
          value={`${stats.fraudPercentage}%`}
          change={stats.fraudPercentageChange}
          isNegativeGood
          icon={Percent}
          color="amber"
        />
        <StatCard
          title="Risk Distribution"
          value={`${stats.riskDistribution.low}% Low`}
          icon={PieIcon}
          color="green"
        />
        <StatCard
          title="Pending Cases"
          value={stats.pendingCases}
          icon={Clock}
          color="purple"
        />
        <StatCard
          title="Critical Cases"
          value={stats.criticalCases}
          icon={AlertTriangle}
          color="red"
        />
      </div>

      {/* Grid: Main Charts & Live Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <FraudTrendChart data={fraudTrend} />
          <RiskTrendChart data={riskTrend} />
        </div>
        <div>
          <AlertFeed alerts={alerts} />        </div>
      </div>

      {/* Secondary Charts Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <CountryChart data={countries} />
        <PaymentMethodChart data={paymentMethods} />
        <MerchantCategoryChart data={merchantCategories} />
      </div>
    </DashboardLayout>
  );
}
