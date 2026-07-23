import React, { useState, useEffect } from 'react';
import { DashboardLayout } from '../layouts/DashboardLayout';
import { StatCard } from '../components/dashboard/StatCard';
import { AlertFeed } from '../components/dashboard/AlertFeed';
import { RecentLogins } from '../components/dashboard/RecentLogins';
import { APIHealth } from '../components/dashboard/APIHealth';
import { TodaysPredictions } from '../components/dashboard/TodaysPredictions';
import { SystemStatus } from '../components/dashboard/SystemStatus';
import { SkeletonStatCard, SkeletonChart, SkeletonFeed } from '../components/dashboard/SkeletonLoader';
import { FraudTrendChart } from '../components/charts/FraudTrendChart';
import { RiskTrendChart } from '../components/charts/RiskTrendChart';
import { CountryChart } from '../components/charts/CountryChart';
import { PaymentMethodChart } from '../components/charts/PaymentMethodChart';
import { MerchantCategoryChart } from '../components/charts/MerchantCategoryChart';
import { analyticsService } from '../services/analytics';
import {
  Receipt,
  ShieldAlert,
  Percent,
  PieChart as PieIcon,
  Clock,
  AlertTriangle,
  ArrowUpRight,
  BarChart3,
  Activity,
  Globe2,
  Server
} from 'lucide-react'; import { useNavigate } from 'react-router-dom';

export function Dashboard() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [statsError, setStatsError] = useState(false);
  const [fraudTrend, setFraudTrend] = useState([]);
  const [riskTrend, setRiskTrend] = useState([]);
  const [countries, setCountries] = useState([]);
  const [paymentMethods, setPaymentMethods] = useState([]);
  const [merchantCategories, setMerchantCategories] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [recentLogins, setRecentLogins] = useState([]);
  const [apiHealth, setApiHealth] = useState([]);
  const [todaysPredictions, setTodaysPredictions] = useState({});
  const [systemStatus, setSystemStatus] = useState({});

  useEffect(() => {
    const loadDashboard = async () => {
      try {
        try {
          const dashboardStats = await analyticsService.getDashboardStats();
          setStats(dashboardStats);
        } catch (e) {
          console.error('Failed to load dashboard stats:', e);
          setStatsError(true);
        }

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

        // Load new components data
        try {
          const loginsData = await analyticsService.getRecentLogins();
          setRecentLogins(loginsData);
        } catch {
          // 
        }

        try {
          const healthData = await analyticsService.getAPIHealth();
          setApiHealth(healthData);
        } catch {
          //
        }

        try {
          const todayPred = await analyticsService.getTodaysPredictions();
          setTodaysPredictions(todayPred);
        } catch {
          //
        }

        try {
          const sysStatus = await analyticsService.getSystemStatus();
          setSystemStatus(sysStatus);
        } catch {
          //
        }

      } catch (error) {
        console.error("Failed to load dashboard:", error);
      } finally {
        setLoading(false);
      }
    };

    loadDashboard();
  }, []);

  return (
    <DashboardLayout>

      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-2 border-b border-slate-800">        <div>
        <h1 className="text-2xl font-bold text-slate-100 tracking-tight">Enterprise Risk Executive Overview</h1>
        <p className="text-xs text-slate-400 mt-1">Real-time fraud surveillance telemetry and active AI model metrics.</p>
      </div>
        <button
          onClick={() => navigate('/prediction')}
          className="w-full md:w-auto inline-flex justify-center items-center gap-2 px-4 py-2 ..."        >
          <span>Run AI Risk Scan</span>
          <ArrowUpRight size={16} />
        </button>
      </div>

      {/* 6 Required Dashboard Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-4">
        {loading ? (
          <>
            <SkeletonStatCard />
            <SkeletonStatCard />
            <SkeletonStatCard />
            <SkeletonStatCard />
            <SkeletonStatCard />
            <SkeletonStatCard />
          </>
        ) : statsError ? (
          <div className="col-span-2 lg:col-span-6 flex items-center gap-3 px-4 py-3 rounded-xl border border-red-500/20 bg-red-500/5 text-red-400 text-xs">
            <AlertTriangle size={16} className="flex-shrink-0" />
            <span>Unable to load summary statistics. Other dashboard sections may still be available.</span>
          </div>
        ) : (
          <>
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
              value={`${(() => {
                const { low = 0, medium = 0, high = 0, critical = 0 } = stats.riskDistribution || {};
                const total = low + medium + high + critical;
                return total > 0 ? ((low / total) * 100).toFixed(1) : '0.0';
              })()}% Low`}
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
          </>
        )}
      </div>


      {/* Fraud Analytics */}

      <div className="flex items-center gap-2 mb-4">
        <BarChart3 className="w-4 h-4 text-cyan-400" />
        <h2 className="text-base font-semibold text-white">
          Fraud Analytics
        </h2>
      </div>

      {/* Fraud Trend + Live Alerts */}

      <div className="mt-8 grid grid-cols-1 lg:grid-cols-3 gap-6">

        <div className="lg:col-span-2">
          {loading ? (
            <SkeletonChart />
          ) : (
            <FraudTrendChart data={fraudTrend} />
          )}
        </div>

        <div>
          {loading ? (
            <SkeletonFeed count={5} />
          ) : (
            <AlertFeed alerts={alerts} />
          )}
        </div>

      </div>

      {/* Risk Trend */}

      <div className="mt-6">

        {loading ? (
          <SkeletonChart />
        ) : (
          <RiskTrendChart data={riskTrend} />
        )}

      </div>

      {/* New Dashboard Components Row */}
      <div className="flex items-center gap-2 mb-4">
        <Activity className="w-4 h-4 text-emerald-400" />
        <h2 className="text-base font-semibold text-white">
          Operations Overview
        </h2>
      </div>
      <div className="mt-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {loading ? (
          <>
            <SkeletonFeed count={3} />
            <SkeletonChart />
            <SkeletonChart />
          </>
        ) : (
          <>
            <RecentLogins logins={recentLogins} />
            <TodaysPredictions predictions={todaysPredictions} />
            <SystemStatus status={systemStatus} />
          </>
        )}
      </div>


      {/* Secondary Charts Grid with New Components */}
      <div className="flex items-center gap-2 mb-4">
        <Globe2 className="w-4 h-4 text-amber-400" />
        <h2 className="text-base font-semibold text-white">
          Business Insights
        </h2>
      </div>
      <div className="mt-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {loading ? (
          <>
            <SkeletonChart />
            <SkeletonChart />
            <SkeletonChart />
          </>
        ) : (
          <>
            <CountryChart data={countries} />
            <PaymentMethodChart data={paymentMethods} />
            <MerchantCategoryChart data={merchantCategories} />
          </>
        )}
      </div>

      {/* API Health */}
      <div className="flex items-center gap-2 mb-4">
        <Server className="w-4 h-4 text-red-400" />
        <h2 className="text-base font-semibold text-white">
          Infrastructure Health
        </h2>
      </div>
      <div className="mt-8"></div>
      <div>
        {loading ? <SkeletonFeed count={4} /> : <APIHealth endpoints={apiHealth} />}
      </div>
    </DashboardLayout>
  );
}
