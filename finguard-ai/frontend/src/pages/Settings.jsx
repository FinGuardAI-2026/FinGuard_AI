import React, { useState, useEffect } from 'react';
import { DashboardLayout } from '../layouts/DashboardLayout';
import { Card, Button, Input, Badge, Spinner } from '../components/ui';
import { useAuth } from '../context/AuthContext';
import { authService } from '../services/auth';
import {
  Settings as SettingsIcon,
  Sun,
  Moon,
  Palette,
  Lock,
  Bell,
  Mail,
  Monitor,
  Sliders,
  Shield,
  Smartphone,
  Trash2,
  Key,
  Eye,
  EyeOff,
  CheckCircle,
  AlertTriangle,
  Check,
  Globe,
  LogOut,
  ChevronRight,
  Info,
  Zap,
  Activity,
} from 'lucide-react';

// ── Reusable Toggle Component ─────────────────────────────────────────────────
function Toggle({ enabled, onChange, id }) {
  return (
    <button
      id={id}
      role="switch"
      aria-checked={enabled}
      onClick={() => onChange(!enabled)}
      className={`relative w-11 h-6 flex items-center rounded-full p-0.5 cursor-pointer transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-cyan-500/40 focus:ring-offset-2 focus:ring-offset-slate-900 ${enabled
        ? 'bg-cyan-500 shadow-lg shadow-cyan-500/30'
        : 'bg-slate-700'
        }`}
    >
      <span
        className={`block w-5 h-5 rounded-full shadow-md transition-all duration-300 ${enabled ? 'translate-x-5 bg-slate-950' : 'translate-x-0 bg-slate-400'
          }`}
      />
    </button>
  );
}

// ── Section Header ────────────────────────────────────────────────────────────
function SectionHeader({ icon: Icon, title, subtitle, color = 'text-cyan-400' }) {
  return (
    <div className="flex items-center gap-3 pb-4 border-b border-slate-800/80">
      <div className="p-2 rounded-lg bg-slate-800/60 border border-slate-700/60">
        <Icon className={`w-4 h-4 ${color}`} />
      </div>
      <div>
        <h2 className="text-sm font-bold text-slate-100">{title}</h2>
        {subtitle && <p className="text-[11px] text-slate-400 mt-0.5">{subtitle}</p>}
      </div>
    </div>
  );
}

// ── Settings Preference Row ───────────────────────────────────────────────────
function PrefRow({ icon: Icon, title, description, children, iconColor = 'text-slate-400' }) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 py-3.5 px-1 border-b border-slate-800/50 last:border-0 group hover:bg-slate-800/10 rounded-lg transition-colors -mx-1">
      <div className="flex items-center gap-3">
        {Icon && (
          <div className={`p-1.5 rounded-md bg-slate-800/60 ${iconColor}`}>
            <Icon className="w-3.5 h-3.5" />
          </div>
        )}
        <div>
          <p className="text-xs font-semibold text-slate-200">{title}</p>
          {description && <p className="text-[10px] text-slate-500 mt-0.5 leading-relaxed">{description}</p>}
        </div>
      </div>
      <div className="self-end sm:self-auto flex-shrink-0 sm:ml-4">{children}</div>
    </div>
  );
}

// ── Slider with Live Value ────────────────────────────────────────────────────
function ThresholdSlider({ label, value, min, max, step = 1, onChange, color = 'accent-cyan-400', trackColor }) {
  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="text-xs font-semibold text-slate-300">{label}</span>
        <span className={`text-xs font-bold font-mono px-2 py-0.5 rounded border ${trackColor}`}>
          {value}
        </span>
      </div>
      <div className="relative">
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          className={`w-full h-2 rounded-full appearance-none cursor-pointer ${color} bg-slate-800 focus:outline-none`}
          style={{ accentColor: undefined }}
        />
      </div>
      <div className="flex justify-between text-[9px] text-slate-600 font-mono">
        <span>{min}</span>
        <span>{max}</span>
      </div>
    </div>
  );
}

// ── Main Settings Component ───────────────────────────────────────────────────
export function Settings() {
  const { user } = useAuth();

  // ── Active section tab ─────────────────────────────────────────────────────
  const [activeSection, setActiveSection] = useState('appearance');

  // ── Loading/save states ────────────────────────────────────────────────────
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [saveMsg, setSaveMsg] = useState('');
  const [saveError, setSaveError] = useState('');

  // ── Appearance ─────────────────────────────────────────────────────────────
  const [theme, setTheme] = useState('dark');
  const [density, setDensity] = useState('comfortable');
  const [fontScale, setFontScale] = useState('normal');

  // ── Notifications ──────────────────────────────────────────────────────────
  const [notifications, setNotifications] = useState({
    email_alerts: true,
    browser_notifications: true,
    fraud_alerts: true,
    system_updates: false,
    weekly_digest: true,
    critical_only: false,
  });

  // ── Prediction Thresholds ──────────────────────────────────────────────────
  const [thresholds, setThresholds] = useState({
    low_medium: 30,
    medium_high: 60,
    high_critical: 85,
    confidence_min: 70,
  });

  // ── Security / Password ────────────────────────────────────────────────────
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showOld, setShowOld] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [passMsg, setPassMsg] = useState('');
  const [passError, setPassError] = useState('');
  const [passLoading, setPassLoading] = useState(false);

  // ── Sessions ───────────────────────────────────────────────────────────────
  const [sessions, setSessions] = useState([]);
  const [sessionMsg, setSessionMsg] = useState('');
  const [centerData, setCenterData] = useState(null);

  // ── Load settings from backend ────────────────────────────────────────────
  useEffect(() => {
    async function load() {
      try {
        const data = await authService.getAccountCenter();
        setCenterData(data);
        if (data?.user?.preferences) {
          const prefs = data.user.preferences;
          if (prefs.theme) setTheme(prefs.theme);
          if (prefs.notifications) setNotifications(n => ({ ...n, ...prefs.notifications }));
          if (prefs.thresholds) setThresholds(t => ({ ...t, ...prefs.thresholds }));
        }
        if (data?.user?.sessions) setSessions(data.user.sessions);
      } catch (err) {
        console.error('Settings load error:', err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [user]);

  // ── Flash message helper ───────────────────────────────────────────────────
  const flashSuccess = (msg) => {
    setSaveMsg(msg);
    setSaveError('');
    setTimeout(() => setSaveMsg(''), 3500);
  };
  const flashError = (msg) => {
    setSaveError(msg);
    setSaveMsg('');
    setTimeout(() => setSaveError(''), 4000);
  };

  // ── Save Appearance ────────────────────────────────────────────────────────
  const handleSaveAppearance = async () => {
    setSaving(true);
    try {
      await authService.updateProfileDetails({
        preferences: { theme, density, fontScale }
      });
      flashSuccess('Appearance preferences saved.');
    } catch {
      flashError('Failed to save appearance settings.');
    } finally {
      setSaving(false);
    }
  };

  // ── Toggle Notification ────────────────────────────────────────────────────
  const handleToggleNotification = async (key) => {
    const original = { ...notifications };
    const updated = { ...notifications, [key]: !notifications[key] };
    setNotifications(updated);
    try {
      await authService.updateProfileDetails({ preferences: { notifications: updated } });
    } catch {
      setNotifications(original);
      flashError('Failed to save notification preferences.');
    }
  };

  // ── Save Thresholds ────────────────────────────────────────────────────────
  const handleSaveThresholds = async () => {
    setSaving(true);
    try {
      await authService.updateProfileDetails({ preferences: { thresholds } });
      flashSuccess('Prediction thresholds updated successfully.');
    } catch {
      flashError('Failed to save thresholds.');
    } finally {
      setSaving(false);
    }
  };

  // ── Change Password ────────────────────────────────────────────────────────
  const handleChangePassword = async (e) => {
    e.preventDefault();
    setPassMsg('');
    setPassError('');

    if (!oldPassword || !newPassword || !confirmPassword) {
      setPassError('All fields are required.');
      return;
    }
    if (newPassword !== confirmPassword) {
      setPassError('New passwords do not match.');
      return;
    }
    if (newPassword.length < 8) {
      setPassError('Password must be at least 8 characters.');
      return;
    }
    setPassLoading(true);
    try {
      await authService.changePassword(oldPassword, newPassword);
      setPassMsg('Password changed successfully.');
      setOldPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err) {
      setPassError(err?.response?.data?.detail || 'Failed to change password.');
    } finally {
      setPassLoading(false);
    }
  };

  // ── Revoke session ─────────────────────────────────────────────────────────
  const handleRevokeSession = async (sessionId) => {
    if (!confirm('Terminate this active device session?')) return;
    const prev = [...sessions];
    setSessions(s => s.filter(x => x.session_id !== sessionId));
    try {
      await authService.revokeSession(sessionId);
      setSessionMsg('Session revoked successfully.');
      setTimeout(() => setSessionMsg(''), 3000);
    } catch {
      setSessions(prev);
      alert('Failed to revoke session.');
    }
  };

  const handleRevokeAll = async () => {
    if (!confirm('Log out all other active devices?')) return;
    try {
      await authService.revokeAllSessions();
      setSessionMsg('All other devices logged out.');
      const data = await authService.getAccountCenter();
      setSessions(data?.user?.sessions || []);
      setTimeout(() => setSessionMsg(''), 3000);
    } catch {
      alert('Failed to revoke all sessions.');
    }
  };

  // ── Relative time ──────────────────────────────────────────────────────────
  const getRelTime = (d) => {
    if (!d) return 'Never';
    const diff = Date.now() - new Date(d).getTime();
    const m = Math.floor(diff / 60000);
    if (m < 1) return 'just now';
    if (m < 60) return `${m}m ago`;
    const h = Math.floor(m / 60);
    if (h < 24) return `${h}h ago`;
    return `${Math.floor(h / 24)}d ago`;
  };

  // ── Password strength ──────────────────────────────────────────────────────
  const getPasswordStrength = (pw) => {
    if (!pw) return { score: 0, label: '', color: '' };
    let score = 0;
    if (pw.length >= 8) score++;
    if (pw.length >= 12) score++;
    if (/[A-Z]/.test(pw)) score++;
    if (/[0-9]/.test(pw)) score++;
    if (/[^A-Za-z0-9]/.test(pw)) score++;
    if (score <= 1) return { score, label: 'Weak', color: 'bg-red-500' };
    if (score <= 2) return { score, label: 'Fair', color: 'bg-amber-500' };
    if (score <= 3) return { score, label: 'Good', color: 'bg-yellow-400' };
    if (score <= 4) return { score, label: 'Strong', color: 'bg-emerald-500' };
    return { score, label: 'Very Strong', color: 'bg-cyan-500' };
  };
  const pwStrength = getPasswordStrength(newPassword);

  // ── Sidebar nav items ──────────────────────────────────────────────────────
  const sections = [
    { id: 'appearance', label: 'Appearance', icon: Palette, color: 'text-purple-400' },
    { id: 'security', label: 'Security', icon: Lock, color: 'text-amber-400' },
    { id: 'notifications', label: 'Notifications', icon: Bell, color: 'text-cyan-400' },
    { id: 'thresholds', label: 'Prediction Threshold', icon: Sliders, color: 'text-emerald-400' },
    { id: 'sessions', label: 'Session Management', icon: Monitor, color: 'text-blue-400' },
  ];

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex flex-col items-center justify-center py-24">
          <Spinner size="lg" />
          <p className="text-slate-400 text-xs mt-4 font-mono animate-pulse">Loading Settings...</p>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      {/* ── Page Header ──────────────────────────────────────────────────── */}
      <div className="pb-4 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-gradient-to-br from-cyan-500/20 to-indigo-500/10 border border-cyan-500/20">
            <SettingsIcon className="w-5 h-5 text-cyan-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-100 tracking-tight">System Settings</h1>
            <p className="text-xs text-slate-400 mt-0.5">
              Manage your workspace appearance, security, and notification preferences.
            </p>
          </div>
        </div>
      </div>

      {/* ── Global flash messages ─────────────────────────────────────────── */}
      {saveMsg && (
        <div className="flex items-center gap-2 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold animate-fade-in-up">
          <CheckCircle className="w-4 h-4 flex-shrink-0" />
          {saveMsg}
        </div>
      )}
      {saveError && (
        <div className="flex items-center gap-2 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-semibold animate-fade-in-up">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          {saveError}
        </div>
      )}

      {/* ── Main Layout: Sidebar + Content ───────────────────────────────── */}
      <div className="flex flex-col lg:flex-row gap-6 items-start">
        {/* ── Settings Sidebar Nav ──────────────────────────────────────── */}
        <aside className="w-full lg:w-56 flex-shrink-0 lg:sticky lg:top-24">
          <nav className="glass rounded-xl border border-slate-800/60 p-2 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-1 gap-2 lg:space-y-0.5 shadow-xl">
            {sections.map((sec) => {
              const Icon = sec.icon;
              const isActive = activeSection === sec.id;
              return (
                <button
                  key={sec.id}
                  id={`settings-nav-${sec.id}`}
                  onClick={() => setActiveSection(sec.id)}
                  className={`w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-xs font-semibold transition-all duration-200 text-left ${isActive
                    ? `bg-slate-800/80 border border-slate-700/60 ${sec.color} shadow-sm`
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40 border border-transparent'
                    }`}
                >
                  <Icon className={`w-3.5 h-3.5 flex-shrink-0 ${isActive ? sec.color : ''}`} />
                  <span>{sec.label}</span>
                  {isActive && <ChevronRight className="w-3 h-3 ml-auto" />}
                </button>
              );
            })}
          </nav>

          {/* Quick info card */}
          <div className="hidden lg:block mt-4 p-3 rounded-xl bg-slate-900/60 border border-slate-800/60 space-y-1.5">
            <p className="text-[9px] font-bold uppercase tracking-widest text-slate-500">Signed in as</p>
            <p className="text-xs font-semibold text-slate-300 truncate">{user?.full_name || 'FinGuard Analyst'}</p>
            <p className="text-[10px] font-mono text-slate-500 truncate">{user?.email}</p>
            <Badge variant={user?.role === 'Admin' ? 'danger' : 'info'} className="text-[9px] mt-1">
              {user?.role || 'Analyst'}
            </Badge>
          </div>
        </aside>

        {/* ── Settings Content Area ─────────────────────────────────────── */}
        <div className="flex-1 min-w-0 space-y-0">

          {/* ════════════════════════════════════════════════════════════
              SECTION 1 — APPEARANCE
          ════════════════════════════════════════════════════════════ */}
          {activeSection === 'appearance' && (
            <div className="space-y-4 animate-fade-in-up">
              <Card>
                <SectionHeader
                  icon={Palette}
                  title="Appearance & Theme"
                  subtitle="Customize the visual style of your FinGuard workspace."
                  color="text-purple-400"
                />
                <div className="mt-5 space-y-6">

                  {/* Theme Selection */}
                  <div className="space-y-3">
                    <label className="fg-label">Color Theme</label>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {/* Dark Theme */}
                      <button
                        id="theme-dark"
                        onClick={() => setTheme('dark')}
                        className={`relative p-4 rounded-xl border-2 transition-all duration-200 text-left group ${theme === 'dark'
                          ? 'border-cyan-500 bg-cyan-500/5 shadow-lg shadow-cyan-500/10'
                          : 'border-slate-800 hover:border-slate-700 bg-slate-900/40'
                          }`}
                      >
                        {theme === 'dark' && (
                          <span className="absolute top-2.5 right-2.5 w-5 h-5 rounded-full bg-cyan-500 flex items-center justify-center">
                            <Check className="w-3 h-3 text-slate-950" />
                          </span>
                        )}
                        {/* Mini dark UI preview */}
                        <div className="w-full h-16 rounded-lg bg-slate-950 border border-slate-800 mb-3 overflow-hidden">
                          <div className="h-3 bg-slate-900 border-b border-slate-800 flex items-center gap-1 px-2">
                            <div className="w-1.5 h-1.5 rounded-full bg-slate-700" />
                            <div className="w-8 h-1 rounded bg-slate-800" />
                          </div>
                          <div className="flex gap-1 p-1.5">
                            <div className="w-8 h-8 rounded bg-slate-900 border border-slate-800" />
                            <div className="flex-1 space-y-1 py-0.5">
                              <div className="h-1.5 rounded bg-slate-800 w-3/4" />
                              <div className="h-1.5 rounded bg-slate-900 w-1/2" />
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Moon className="w-3.5 h-3.5 text-indigo-400" />
                          <div>
                            <p className="text-xs font-bold text-slate-200">Dark Theme</p>
                            <p className="text-[10px] text-slate-500">Reduced eye strain</p>
                          </div>
                        </div>
                      </button>

                      {/* Light Theme */}
                      <button
                        id="theme-light"
                        onClick={() => setTheme('light')}
                        className={`relative p-4 rounded-xl border-2 transition-all duration-200 text-left group ${theme === 'light'
                          ? 'border-cyan-500 bg-cyan-500/5 shadow-lg shadow-cyan-500/10'
                          : 'border-slate-800 hover:border-slate-700 bg-slate-900/40'
                          }`}
                      >
                        {theme === 'light' && (
                          <span className="absolute top-2.5 right-2.5 w-5 h-5 rounded-full bg-cyan-500 flex items-center justify-center">
                            <Check className="w-3 h-3 text-slate-950" />
                          </span>
                        )}
                        {/* Mini light UI preview */}
                        <div className="w-full h-16 rounded-lg bg-slate-100 border border-slate-300 mb-3 overflow-hidden">
                          <div className="h-3 bg-white border-b border-slate-200 flex items-center gap-1 px-2">
                            <div className="w-1.5 h-1.5 rounded-full bg-slate-300" />
                            <div className="w-8 h-1 rounded bg-slate-200" />
                          </div>
                          <div className="flex gap-1 p-1.5">
                            <div className="w-8 h-8 rounded bg-white border border-slate-200" />
                            <div className="flex-1 space-y-1 py-0.5">
                              <div className="h-1.5 rounded bg-slate-200 w-3/4" />
                              <div className="h-1.5 rounded bg-slate-100 w-1/2" />
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Sun className="w-3.5 h-3.5 text-amber-400" />
                          <div>
                            <p className="text-xs font-bold text-slate-200">Light Theme</p>
                            <p className="text-[10px] text-slate-500">Bright workspace mode</p>
                          </div>
                        </div>
                      </button>
                    </div>

                    {theme === 'light' && (
                      <div className="flex items-center gap-2 p-3 rounded-lg bg-amber-500/5 border border-amber-500/15 text-amber-400/80 text-[11px]">
                        <Info className="w-3.5 h-3.5 flex-shrink-0" />
                        Light theme will apply on next workspace reload.
                      </div>
                    )}
                  </div>

                  {/* Density */}
                  <div className="space-y-2">
                    <label className="fg-label">Layout Density</label>
                    <div className="flex flex-wrap gap-2">
                      {['compact', 'comfortable', 'spacious'].map((d) => (
                        <button
                          key={d}
                          id={`density-${d}`}
                          onClick={() => setDensity(d)}
                          className={`px-3 py-1.5 text-[10px] font-bold uppercase rounded-lg border transition-all ${density === d
                            ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30'
                            : 'text-slate-400 hover:text-slate-200 border-slate-800 bg-slate-900/40 hover:border-slate-700'
                            }`}
                        >
                          {d}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Font Scale */}
                  <div className="space-y-2">
                    <label className="fg-label">Font Scale</label>
                    <div className="flex flex-wrap gap-2">
                      {['small', 'normal', 'large'].map((f) => (
                        <button
                          key={f}
                          id={`font-${f}`}
                          onClick={() => setFontScale(f)}
                          className={`px-3 py-1.5 text-[10px] font-bold uppercase rounded-lg border transition-all ${fontScale === f
                            ? 'bg-purple-500/10 text-purple-400 border-purple-500/30'
                            : 'text-slate-400 hover:text-slate-200 border-slate-800 bg-slate-900/40 hover:border-slate-700'
                            }`}
                        >
                          {f}
                        </button>
                      ))}
                    </div>
                  </div>

                </div>
              </Card>

              <div className="flex justify-end">
                <Button
                  id="save-appearance"
                  variant="primary"
                  onClick={handleSaveAppearance}
                  isLoading={saving}
                  className="w-full sm:w-auto px-6 font-bold"                >
                  Save Appearance
                </Button>
              </div>
            </div>
          )}

          {/* ════════════════════════════════════════════════════════════
              SECTION 2 — SECURITY
          ════════════════════════════════════════════════════════════ */}
          {activeSection === 'security' && (
            <div className="space-y-4 animate-fade-in-up">
              <Card>
                <SectionHeader
                  icon={Lock}
                  title="Change Password"
                  subtitle="Update your security credentials. Minimum 8 characters required."
                  color="text-amber-400"
                />

                <form onSubmit={handleChangePassword} className="mt-5 space-y-4">
                  {/* Old Password */}
                  <div className="relative">
                    <Input
                      id="old-password"
                      label="Current Password"
                      type={showOld ? 'text' : 'password'}
                      value={oldPassword}
                      onChange={(e) => setOldPassword(e.target.value)}
                      icon={Key}
                      placeholder="Enter current password"
                    />
                    <button
                      type="button"
                      onClick={() => setShowOld(!showOld)}
                      className="absolute right-3 top-[34px] text-slate-500 hover:text-slate-300 transition-colors"
                    >
                      {showOld ? <EyeOff size={14} /> : <Eye size={14} />}
                    </button>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {/* New Password */}
                    <div className="space-y-1.5">
                      <div className="relative">
                        <Input
                          id="new-password"
                          label="New Password"
                          type={showNew ? 'text' : 'password'}
                          value={newPassword}
                          onChange={(e) => setNewPassword(e.target.value)}
                          icon={Lock}
                          placeholder="Enter new password"
                        />
                        <button
                          type="button"
                          onClick={() => setShowNew(!showNew)}
                          className="absolute right-3 top-[34px] text-slate-500 hover:text-slate-300 transition-colors"
                        >
                          {showNew ? <EyeOff size={14} /> : <Eye size={14} />}
                        </button>
                      </div>
                      {/* Strength meter */}
                      {newPassword && (
                        <div className="space-y-1">
                          <div className="flex gap-1">
                            {[1, 2, 3, 4, 5].map((i) => (
                              <div
                                key={i}
                                className={`h-1 flex-1 rounded-full transition-all duration-300 ${i <= pwStrength.score ? pwStrength.color : 'bg-slate-800'
                                  }`}
                              />
                            ))}
                          </div>
                          <p className="text-[10px] text-slate-500">
                            Strength:{' '}
                            <span className={`font-bold ${pwStrength.score <= 1 ? 'text-red-400' :
                              pwStrength.score <= 2 ? 'text-amber-400' :
                                pwStrength.score <= 3 ? 'text-yellow-400' :
                                  pwStrength.score <= 4 ? 'text-emerald-400' : 'text-cyan-400'
                              }`}>
                              {pwStrength.label}
                            </span>
                          </p>
                        </div>
                      )}
                    </div>

                    {/* Confirm Password */}
                    <div className="relative">
                      <Input
                        id="confirm-password"
                        label="Confirm New Password"
                        type={showConfirm ? 'text' : 'password'}
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        icon={Shield}
                        placeholder="Confirm new password"
                        error={confirmPassword && newPassword !== confirmPassword ? 'Passwords do not match' : ''}
                      />
                      <button
                        type="button"
                        onClick={() => setShowConfirm(!showConfirm)}
                        className="absolute right-3 top-[34px] text-slate-500 hover:text-slate-300 transition-colors"
                      >
                        {showConfirm ? <EyeOff size={14} /> : <Eye size={14} />}
                      </button>
                    </div>
                  </div>

                  {/* Password requirements hint */}
                  <div className="p-3 rounded-lg bg-slate-900/50 border border-slate-800/60 grid grid-cols-1 sm:grid-cols-2 gap-1.5">                    {[
                    { label: 'Min 8 characters', met: newPassword.length >= 8 },
                    { label: 'Uppercase letter', met: /[A-Z]/.test(newPassword) },
                    { label: 'Number included', met: /[0-9]/.test(newPassword) },
                    { label: 'Special character', met: /[^A-Za-z0-9]/.test(newPassword) },
                  ].map((req) => (
                    <div key={req.label} className={`flex items-center gap-1.5 text-[10px] font-medium ${req.met ? 'text-emerald-400' : 'text-slate-500'}`}>
                      <div className={`w-3.5 h-3.5 rounded-full flex items-center justify-center flex-shrink-0 border ${req.met ? 'bg-emerald-500/10 border-emerald-500/30' : 'border-slate-700'}`}>
                        {req.met && <Check className="w-2 h-2" />}
                      </div>
                      {req.label}
                    </div>
                  ))}
                  </div>

                  {passMsg && (
                    <div className="flex items-center gap-2 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold">
                      <CheckCircle className="w-4 h-4" /> {passMsg}
                    </div>
                  )}
                  {passError && (
                    <div className="flex items-center gap-2 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-semibold">
                      <AlertTriangle className="w-4 h-4" /> {passError}
                    </div>
                  )}

                  <Button
                    id="change-password-submit"
                    type="submit"
                    variant="primary"
                    isLoading={passLoading}
                    className="w-full sm:w-auto font-bold px-6"                  >
                    <Lock className="w-3.5 h-3.5 mr-1.5" />
                    Update Password
                  </Button>
                </form>
              </Card>

              {/* Security status card */}
              <Card>
                <SectionHeader
                  icon={Shield}
                  title="Security Overview"
                  subtitle="Your current security posture and recommendations."
                  color="text-amber-400"
                />
                <div className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-3">                  {[
                  { label: 'Security Score', value: `${centerData?.security_score || 60}%`, color: (centerData?.security_score || 60) >= 80 ? 'text-emerald-400' : 'text-amber-400', icon: Shield },
                  { label: 'Active Sessions', value: sessions.length, color: 'text-blue-400', icon: Monitor },
                  { label: '2FA Status', value: 'Disabled', color: 'text-slate-400', icon: Smartphone },
                ].map((item) => (
                  <div key={item.label} className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/60 text-center">
                    <item.icon className={`w-5 h-5 mx-auto mb-1.5 ${item.color}`} />
                    <div className={`text-lg font-extrabold ${item.color}`}>{item.value}</div>
                    <div className="text-[9px] font-semibold text-slate-500 uppercase tracking-wider mt-0.5">{item.label}</div>
                  </div>

                ))}
                </div>
              </Card>
            </div>
          )}

          {/* ════════════════════════════════════════════════════════════
              SECTION 3 — NOTIFICATIONS
          ════════════════════════════════════════════════════════════ */}
          {activeSection === 'notifications' && (
            <div className="space-y-4 animate-fade-in-up">
              {/* Email Alerts */}
              <Card>
                <SectionHeader
                  icon={Mail}
                  title="Email Alerts"
                  subtitle="Configure when FinGuard sends email notifications to your inbox."
                  color="text-cyan-400"
                />
                <div className="mt-4">
                  <PrefRow
                    icon={Mail}
                    title="Email Alerts"
                    description="Receive fraud risk summaries and threshold breach alerts via email."
                    iconColor="text-cyan-400"
                  >
                    <Toggle
                      id="toggle-email-alerts"
                      enabled={notifications.email_alerts}
                      onChange={() => handleToggleNotification('email_alerts')}
                    />
                  </PrefRow>
                  <PrefRow
                    icon={Zap}
                    title="Fraud Detection Alerts"
                    description="Instant alerts when transactions exceed critical risk thresholds."
                    iconColor="text-red-400"
                  >
                    <Toggle
                      id="toggle-fraud-alerts"
                      enabled={notifications.fraud_alerts}
                      onChange={() => handleToggleNotification('fraud_alerts')}
                    />
                  </PrefRow>
                  <PrefRow
                    icon={Activity}
                    title="Weekly Digest"
                    description="Weekly summary of fraud patterns, reports, and analytics."
                    iconColor="text-emerald-400"
                  >
                    <Toggle
                      id="toggle-weekly-digest"
                      enabled={notifications.weekly_digest}
                      onChange={() => handleToggleNotification('weekly_digest')}
                    />
                  </PrefRow>
                  <PrefRow
                    icon={Globe}
                    title="System & Update Announcements"
                    description="Platform updates, maintenance windows, and feature releases."
                    iconColor="text-slate-400"
                  >
                    <Toggle
                      id="toggle-system-updates"
                      enabled={notifications.system_updates}
                      onChange={() => handleToggleNotification('system_updates')}
                    />
                  </PrefRow>
                </div>
              </Card>

              {/* Browser Notifications */}
              <Card>
                <SectionHeader
                  icon={Monitor}
                  title="Browser Notifications"
                  subtitle="Real-time in-browser push notifications for live workspace events."
                  color="text-blue-400"
                />
                <div className="mt-4">
                  <PrefRow
                    icon={Bell}
                    title="Browser Notifications"
                    description="Push popup banners for fraud detection and live system events."
                    iconColor="text-blue-400"
                  >
                    <Toggle
                      id="toggle-browser-notifications"
                      enabled={notifications.browser_notifications}
                      onChange={() => handleToggleNotification('browser_notifications')}
                    />
                  </PrefRow>
                  <PrefRow
                    icon={AlertTriangle}
                    title="Critical Alerts Only"
                    description="Limit notifications to high and critical severity events only."
                    iconColor="text-amber-400"
                  >
                    <Toggle
                      id="toggle-critical-only"
                      enabled={notifications.critical_only}
                      onChange={() => handleToggleNotification('critical_only')}
                    />
                  </PrefRow>
                </div>

                {/* Permission hint */}
                <div className="mt-3 flex items-start gap-2 p-3 rounded-lg bg-blue-500/5 border border-blue-500/15 text-blue-400/70 text-[11px]">
                  <Info className="w-3.5 h-3.5 flex-shrink-0" />
                  Browser must grant notification permissions for push alerts to work. Click the lock icon in your address bar to manage permissions.
                </div>
              </Card>

              {/* Notification status summary */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="p-4 rounded-xl glass border border-slate-800/60 text-center">
                  <div className="text-2xl font-extrabold text-cyan-400">
                    {Object.values(notifications).filter(Boolean).length}
                  </div>
                  <div className="text-[9px] font-bold text-slate-500 uppercase tracking-wider mt-1">Enabled Channels</div>
                </div>
                <div className="p-4 rounded-xl glass border border-slate-800/60 text-center">
                  <div className="text-2xl font-extrabold text-slate-400">
                    {Object.values(notifications).filter(v => !v).length}
                  </div>
                  <div className="text-[9px] font-bold text-slate-500 uppercase tracking-wider mt-1">Muted Channels</div>
                </div>
              </div>
            </div>
          )}

          {/* ════════════════════════════════════════════════════════════
              SECTION 4 — PREDICTION THRESHOLDS
          ════════════════════════════════════════════════════════════ */}
          {activeSection === 'thresholds' && (
            <div className="space-y-4 animate-fade-in-up">
              <Card>
                <SectionHeader
                  icon={Sliders}
                  title="Prediction Threshold Configuration"
                  subtitle="Calibrate decision boundaries for automated risk band classification. Changes affect live AI prediction scoring."
                  color="text-emerald-400"
                />

                {/* Visual risk band display */}
                <div className="mt-5 mb-6">
                  <div className="h-4 rounded-full overflow-hidden flex shadow-inner">
                    <div
                      className="bg-gradient-to-r from-emerald-500 to-emerald-400 transition-all duration-500 flex items-center justify-center"
                      style={{ width: `${thresholds.low_medium}%` }}
                    >
                      {thresholds.low_medium > 10 && <span className="text-[8px] font-extrabold text-slate-950 tracking-wider">LOW</span>}
                    </div>
                    <div
                      className="bg-gradient-to-r from-amber-500 to-orange-400 transition-all duration-500 flex items-center justify-center"
                      style={{ width: `${thresholds.medium_high - thresholds.low_medium}%` }}
                    >
                      {(thresholds.medium_high - thresholds.low_medium) > 10 && <span className="text-[8px] font-extrabold text-slate-950 tracking-wider">MEDIUM</span>}
                    </div>
                    <div
                      className="bg-gradient-to-r from-orange-500 to-red-400 transition-all duration-500 flex items-center justify-center"
                      style={{ width: `${thresholds.high_critical - thresholds.medium_high}%` }}
                    >
                      {(thresholds.high_critical - thresholds.medium_high) > 10 && <span className="text-[8px] font-extrabold text-slate-950 tracking-wider">HIGH</span>}
                    </div>
                    <div
                      className="bg-gradient-to-r from-red-600 to-red-500 transition-all duration-500 flex items-center justify-center flex-1"
                    >
                      <span className="text-[8px] font-extrabold text-white tracking-wider">CRITICAL</span>
                    </div>
                  </div>
                  <div className="flex justify-between text-[9px] text-slate-600 font-mono mt-1.5">
                    <span>0</span>
                    <span>{thresholds.low_medium}</span>
                    <span>{thresholds.medium_high}</span>
                    <span>{thresholds.high_critical}</span>
                    <span>100</span>
                  </div>
                </div>

                <div className="space-y-6">
                  <ThresholdSlider
                    label="Low → Medium Threshold"
                    value={thresholds.low_medium}
                    min={5}
                    max={thresholds.medium_high - 5}
                    onChange={(v) => setThresholds(t => ({ ...t, low_medium: v }))}
                    trackColor="text-emerald-400 bg-emerald-500/10 border-emerald-500/20"
                  />
                  <ThresholdSlider
                    label="Medium → High Threshold"
                    value={thresholds.medium_high}
                    min={thresholds.low_medium + 5}
                    max={thresholds.high_critical - 5}
                    onChange={(v) => setThresholds(t => ({ ...t, medium_high: v }))}
                    trackColor="text-amber-400 bg-amber-500/10 border-amber-500/20"
                  />
                  <ThresholdSlider
                    label="High → Critical Threshold"
                    value={thresholds.high_critical}
                    min={thresholds.medium_high + 5}
                    max={98}
                    onChange={(v) => setThresholds(t => ({ ...t, high_critical: v }))}
                    trackColor="text-red-400 bg-red-500/10 border-red-500/20"
                  />
                  <ThresholdSlider
                    label="Minimum Confidence Score"
                    value={thresholds.confidence_min}
                    min={50}
                    max={99}
                    onChange={(v) => setThresholds(t => ({ ...t, confidence_min: v }))}
                    trackColor="text-blue-400 bg-blue-500/10 border-blue-500/20"
                  />
                </div>

                {/* Risk band legend */}
                <div className="mt-6 grid grid-cols-2 sm:grid-cols-4 gap-2">
                  {[
                    { band: 'Low', range: `0 – ${thresholds.low_medium}`, color: 'text-emerald-400 border-emerald-500/20 bg-emerald-500/5' },
                    { band: 'Medium', range: `${thresholds.low_medium} – ${thresholds.medium_high}`, color: 'text-amber-400 border-amber-500/20 bg-amber-500/5' },
                    { band: 'High', range: `${thresholds.medium_high} – ${thresholds.high_critical}`, color: 'text-orange-400 border-orange-500/20 bg-orange-500/5' },
                    { band: 'Critical', range: `${thresholds.high_critical} – 100`, color: 'text-red-400 border-red-500/20 bg-red-500/5' },
                  ].map((b) => (
                    <div key={b.band} className={`p-2.5 rounded-lg border text-center ${b.color}`}>
                      <div className="text-[9px] font-extrabold uppercase tracking-widest">{b.band}</div>
                      <div className="text-xs font-bold font-mono mt-1">{b.range}</div>
                    </div>
                  ))}
                </div>
              </Card>

              <div className="flex flex-col-reverse sm:flex-row sm:items-center sm:justify-between gap-3">
                <button
                  onClick={() => setThresholds({ low_medium: 30, medium_high: 60, high_critical: 85, confidence_min: 70 })}
                  className="w-full sm:w-auto text-center sm:text-left text-xs text-slate-500 hover:text-slate-300 transition-colors font-medium"                >
                  Reset to defaults
                </button>
                <Button
                  id="save-thresholds"
                  variant="primary"
                  onClick={handleSaveThresholds}
                  isLoading={saving}
                  className="w-full sm:w-auto px-6 font-bold"                >
                  <Sliders className="w-3.5 h-3.5 mr-1.5" />
                  Apply Thresholds
                </Button>
              </div>
            </div>
          )}

          {/* ════════════════════════════════════════════════════════════
              SECTION 5 — SESSION MANAGEMENT
          ════════════════════════════════════════════════════════════ */}
          {activeSection === 'sessions' && (
            <div className="space-y-4 animate-fade-in-up">
              <Card>
                <SectionHeader
                  icon={Monitor}
                  title="Session Management"
                  subtitle="Monitor and revoke active login sessions across all your devices."
                  color="text-blue-400"
                />

                {sessionMsg && (
                  <div className="mt-4 flex items-center gap-2 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold">
                    <CheckCircle className="w-4 h-4" /> {sessionMsg}
                  </div>
                )}

                <div className="mt-5">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
                    <div>
                      <span className="text-xs font-bold text-slate-300">
                        {sessions.length} Active Session{sessions.length !== 1 ? 's' : ''}
                      </span>
                      <p className="text-[10px] text-slate-500 mt-0.5">
                        Includes your current device session.
                      </p>
                    </div>
                    {sessions.length > 1 && (
                      <Button
                        id="revoke-all-sessions"
                        variant="danger"
                        size="sm"
                        onClick={handleRevokeAll}
                        className="w-full sm:w-auto text-[10px] font-bold uppercase tracking-wide"                      >
                        <LogOut className="w-3.5 h-3.5 mr-1.5" />
                        Revoke All Others
                      </Button>
                    )}
                  </div>

                  <div className="space-y-2">
                    {sessions.length === 0 ? (
                      <div className="py-12 text-center text-slate-500 text-xs">
                        <Monitor className="w-10 h-10 mx-auto mb-3 opacity-20" />
                        No active sessions found.
                      </div>
                    ) : (
                      sessions.map((sess, idx) => {
                        const isCurrent = sess.user_agent === navigator.userAgent || idx === 0;
                        return (
                          <div
                            key={sess.session_id || idx}
                            className={`p-4 rounded-xl border flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 transition-all ${isCurrent
                              ? 'bg-cyan-500/5 border-cyan-500/20 shadow-sm shadow-cyan-500/5'
                              : 'bg-slate-900/50 border-slate-800/60 hover:border-slate-700/60'
                              }`}
                          >
                            <div className="flex items-start gap-3">
                              <div className={`p-2.5 rounded-lg flex-shrink-0 border ${isCurrent ? 'bg-cyan-500/10 border-cyan-500/20' : 'bg-slate-800/60 border-slate-700/60'}`}>
                                {sess.device_type === 'Mobile' ? (
                                  <Smartphone className={`w-4 h-4 ${isCurrent ? 'text-cyan-400' : 'text-slate-400'}`} />
                                ) : (
                                  <Monitor className={`w-4 h-4 ${isCurrent ? 'text-cyan-400' : 'text-slate-400'}`} />
                                )}
                              </div>
                              <div>
                                <div className="flex items-center gap-2 flex-wrap">
                                  <span className="text-xs font-bold text-slate-200">
                                    {sess.browser || 'Unknown Browser'} on {sess.os || 'Unknown OS'}
                                  </span>
                                  {isCurrent && (
                                    <Badge variant="success" className="text-[8px] py-0 px-1.5 font-extrabold">
                                      Current Session
                                    </Badge>
                                  )}
                                </div>
                                <div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-3 mt-1 text-[10px] text-slate-500 font-mono break-all">                                  <span>IP: {sess.ip_address || 'Unknown'}</span>
                                  <span>•</span>
                                  <span>{sess.location || 'Unknown Location'}</span>
                                </div>
                                <div className="flex items-center gap-3 mt-0.5 text-[9px] text-slate-600">
                                  <span>Started: {sess.created_at ? getRelTime(sess.created_at) : 'Unknown'}</span>
                                  {sess.last_active && (
                                    <>
                                      <span>•</span>
                                      <span>Active: {getRelTime(sess.last_active)}</span>
                                    </>
                                  )}
                                </div>
                              </div>
                            </div>

                            {!isCurrent && (
                              <button
                                onClick={() => handleRevokeSession(sess.session_id)}
                                className="flex-shrink-0 flex items-center gap-1.5 text-[10px] px-3 py-1.5 rounded-lg border border-red-500/20 hover:border-red-500/40 text-red-400 hover:bg-red-500/5 transition-all font-bold self-start sm:self-center"
                              >
                                <Trash2 size={12} />
                                Revoke
                              </button>
                            )}
                          </div>
                        );
                      })
                    )}
                  </div>
                </div>
              </Card>

              {/* Security tip */}
              <div className="p-4 rounded-xl bg-blue-500/5 border border-blue-500/15 flex items-start gap-3">                <Info className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <p className="text-xs font-semibold text-blue-300">Security Tip</p>
                  <p className="text-[11px] text-slate-400 leading-relaxed">
                    Revoke any sessions from devices or locations you don&apos;t recognize. If you see suspicious activity, change your password immediately and revoke all other sessions.                  </p>
                </div>
              </div>
            </div>
          )}

        </div>
      </div>
    </DashboardLayout>
  );
}
