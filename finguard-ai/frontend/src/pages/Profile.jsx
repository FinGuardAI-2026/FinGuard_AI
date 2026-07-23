import React, { useState, useEffect } from 'react';
import { DashboardLayout } from '../layouts/DashboardLayout';
import { Card, Button, Input, Badge, Spinner } from '../components/ui';
import { useAuth } from '../context/AuthContext';
// import { useNotifications } from '../context/NotificationContext';
import {
  User,
  Shield,
  Mail,
  Calendar,
  Key,
  LogOut,
  Smartphone,
  Activity,
  FileText,
  Bell,
  CheckCircle,
  AlertTriangle,
  ShieldCheck,
  Cpu,
  Eye,
  Trash2,
  Monitor,
  Check,
  EyeOff
} from 'lucide-react';
import { authService } from '../services/auth';
import { formatDate, formatDateTime } from '../utils/dateFormatter';

const PRESET_GRADIENTS = [
  { name: 'Cyan Glow', class: 'from-cyan-500 to-blue-600 font-bold text-slate-950' },
  { name: 'Purple Neon', class: 'from-purple-500 to-indigo-600 font-bold text-slate-950' },
  { name: 'Emerald Spark', class: 'from-emerald-400 to-teal-600 font-bold text-slate-950' },
  { name: 'Sunset Fusion', class: 'from-orange-500 to-red-600 font-bold text-slate-950' },
  { name: 'Rose Petal', class: 'from-pink-500 to-rose-600 font-bold text-slate-950' }
];

export function Profile() {
  const { user } = useAuth();
  // useNotifications();

  // Unified loading / state
  const [loading, setLoading] = useState(true);
  const [centerData, setCenterData] = useState(null);
  const [activeTab, setActiveTab] = useState('settings');

  // Form states
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [email, setEmail] = useState(user?.email || '');
  const [avatarColor, setAvatarColor] = useState(user?.avatar_color || PRESET_GRADIENTS[0].class);
  const [avatarUrl, setAvatarUrl] = useState(user?.avatar_url || '');
  const [selectedGradient, setSelectedGradient] = useState(PRESET_GRADIENTS[0].class);

  // Preference states (Optimistic UI updates)
  const [preferences, setPreferences] = useState({
    email_notifications: true,
    system_alerts: true,
    theme: 'dark',
    language: 'en'
  });

  // Password state
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showOldPass, setShowOldPass] = useState(false);
  const [showNewPass, setShowNewPass] = useState(false);

  // Status/Messages
  const [updateMsg, setUpdateMsg] = useState('');
  const [updateError, setUpdateError] = useState('');
  const [passMsg, setPassMsg] = useState('');
  const [passError, setPassError] = useState('');
  const [sessionMsg, setSessionMsg] = useState('');

  // Fetch account center payload
  useEffect(() => {
    async function loadCenter() {
      try {
        const data = await authService.getAccountCenter();
        setCenterData(data);
        if (user?.preferences) {
          setPreferences(prev => ({
            ...prev,
            ...user.preferences,
          }));
        } else if (data?.user?.preferences) {
          setPreferences(prev => ({
            ...prev,
            ...data.user.preferences,
          }));
        } if (user?.avatar_color) {
          setAvatarColor(user.avatar_color);
          setSelectedGradient(user.avatar_color);
        }
        if (user?.avatar_url) {
          setAvatarUrl(user.avatar_url);
        }
      } catch (err) {
        console.error('Failed to load profile details:', err);
      } finally {
        setLoading(false);
      }
    }
    loadCenter();
  }, [user]);

  // Handle profile update
  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    setUpdateMsg('');
    setUpdateError('');
    try {
      const payload = {
        full_name: fullName,
        email: email,
        avatar_color: avatarColor,
        avatar_url: avatarUrl
      };
      await authService.updateProfileDetails(payload);
      setUpdateMsg('Profile details successfully updated.');
    } catch (err) {
      setUpdateError(err?.response?.data?.detail || 'Failed to update profile.');
    }
  };

  // Toggle Preferences (Optimistic UI Update)
  const handleTogglePreference = async (key) => {
    const originalPrefs = { ...preferences };
    const updatedPrefs = { ...preferences, [key]: !preferences[key] };

    // Optimistic state set
    setPreferences(updatedPrefs);

    try {
      await authService.updateProfileDetails({ preferences: updatedPrefs });
    } catch {
      // Revert state on failure
      setPreferences(originalPrefs);
      alert('Failed to save preferences to server.');
    }
  };

  // Change language selection
  const handleLanguageChange = async (e) => {
    const val = e.target.value;
    const originalPrefs = { ...preferences };
    const updatedPrefs = { ...preferences, language: val };

    setPreferences(updatedPrefs);
    try {
      await authService.updateProfileDetails({ preferences: updatedPrefs });
    } catch {
      setPreferences(originalPrefs);
      alert('Failed to save language preferences.');
    }
  };

  // Change password
  const handleChangePassword = async (e) => {
    e.preventDefault();
    setPassMsg('');
    setPassError('');

    if (newPassword !== confirmPassword) {
      setPassError('New passwords do not match.');
      return;
    }

    try {
      await authService.changePassword(oldPassword, newPassword);
      setPassMsg('Password changed successfully.');
      setOldPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err) {
      setPassError(err?.response?.data?.detail || 'Failed to change password.');
    }
  };

  // Revoke device session (Optimistic UI Update)
  const handleRevokeSession = async (sessionId) => {
    if (!confirm('Are you sure you want to terminate this active device session?')) return;

    const originalSessions = centerData?.user?.sessions || [];
    const updatedSessions = originalSessions.filter(s => s.session_id !== sessionId);

    // Optimistic UI Update
    setCenterData(prev => ({
      ...prev,
      user: {
        ...prev.user,
        sessions: updatedSessions
      }
    }));

    try {
      await authService.revokeSession(sessionId);
      setSessionMsg('Device session successfully terminated.');
    } catch {
      // Rollback
      setCenterData(prev => ({
        ...prev,
        user: {
          ...prev.user,
          sessions: originalSessions
        }
      }));
      alert('Failed to terminate device session.');
    }
  };

  // Revoke all other sessions
  const handleRevokeAllOther = async () => {
    if (!confirm('Are you sure you want to log out all other active devices?')) return;
    try {
      await authService.revokeAllSessions();
      setSessionMsg('All other devices have been successfully logged out.');
      // Refresh center details
      const data = await authService.getAccountCenter();
      setCenterData(data);
    } catch {
      alert('Failed to revoke all sessions.');
    }
  };

  // Parse relative time
  const getRelativeTime = (dateString) => {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHr = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHr / 24);

    if (diffSec < 60) return 'just now';
    if (diffMin < 60) return `${diffMin}m ago`;
    if (diffHr < 24) return `${diffHr}h ago`;
    if (diffDay === 1) return 'yesterday';
    return `${diffDay}d ago`;
  };

  // Activity Icon mapper
  const getActivityIcon = (type) => {
    switch (type) {
      case 'auth_login':
        return <CheckCircle className="w-4 h-4 text-emerald-400" />;
      case 'auth_logout':
        return <LogOut className="w-4 h-4 text-slate-500" />;
      case 'auth_password_change':
        return <Key className="w-4 h-4 text-amber-400" />;
      case 'profile_update':
        return <User className="w-4 h-4 text-cyan-400" />;
      default:
        return <Activity className="w-4 h-4 text-cyan-500" />;
    }
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex flex-col items-center justify-center py-20">
          <Spinner size="lg" />
          <p className="text-slate-400 text-xs mt-4">Loading FinGuard Account Center...</p>
        </div>
      </DashboardLayout>
    );
  }

  // Calculate scores
  const securityScore = centerData?.security_score || 60;
  const profileCompletion = centerData?.profile_completion || 50;
  const stats = centerData?.statistics || {
    total_transactions_investigated: 0,
    total_reports_generated: 0,
    avg_risk_score: 0.0,
    total_alerts_handled: 0
  };

  // Format creation date
  const memberSince = user?.created_at
    ? formatDate(user.created_at)
    : 'N/A';

  return (
    <DashboardLayout>
      {/* Title Header */}
      <div className="pb-3 border-b border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-6 h-6 text-cyan-400" />
            <h1 className="text-2xl font-bold text-slate-100 tracking-tight">Enterprise Account Center</h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Audit investigator sessions, configure notification alerts, and manage credential attributes.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={user?.role === 'Admin' ? 'danger' : 'info'}>
            {user?.role || 'Fraud Analyst'}
          </Badge>
          <Badge variant="success">Active</Badge>
        </div>
      </div>

      {/* Main Grid: Left summary panel, Right tabs detail panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">

        {/* ── LEFT COLUMN: Summary Audits ───────────────────────────────────── */}
        <div className="space-y-6 lg:col-span-1">

          {/* Main User Card */}
          <Card glass className="flex flex-col items-center text-center p-6">

            {/* Avatar container */}
            <div className="relative group">
              {avatarUrl ? (
                <img
                  src={avatarUrl}
                  alt={user?.full_name}
                  className="w-24 h-24 rounded-2xl mb-4 border border-slate-700 shadow-xl object-cover"
                  onError={() => setAvatarUrl('')} // fallback to initials if image load fails
                />
              ) : (
                <div className={`w-24 h-24 rounded-2xl bg-gradient-to-tr ${avatarColor || selectedGradient} flex items-center justify-center text-slate-950 font-bold text-3xl mb-4 shadow-lg shadow-cyan-500/10`}>
                  {user?.full_name ? user.full_name.charAt(0).toUpperCase() : 'A'}
                </div>
              )}
            </div>

            <h3 className="text-lg font-bold text-slate-100">{user?.full_name || 'FinGuard Analyst'}</h3>
            <span className="text-xs text-slate-400 font-mono mt-0.5">{user?.email || 'analyst@finguard.ai'}</span>

            {/* Verification Stats */}
            <div className="w-full grid grid-cols-2 gap-4 border-t border-b border-slate-800/80 my-5 py-4">
              <div>
                <div className="text-xs text-slate-500 font-semibold uppercase tracking-wider">Sec Score</div>
                <div className={`text-xl font-bold mt-1 ${securityScore >= 80 ? 'text-emerald-400' : 'text-amber-400'}`}>
                  {securityScore}%
                </div>
              </div>
              <div>
                <div className="text-xs text-slate-500 font-semibold uppercase tracking-wider">Completion</div>
                <div className="text-xl font-bold text-cyan-400 mt-1">
                  {profileCompletion}%
                </div>
              </div>
            </div>

            {/* Custom Avatar Gradient selection */}
            <div className="w-full text-left space-y-2">
              <label className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">Preset Avatar Gradient</label>
              <div className="flex gap-2">
                {PRESET_GRADIENTS.map((gradient) => (
                  <button
                    key={gradient.name}
                    title={gradient.name}
                    onClick={() => {
                      setAvatarColor(gradient.class);
                      setSelectedGradient(gradient.class);
                      setAvatarUrl(''); // clear URL to show initials
                    }}
                    className={`w-6 h-6 rounded-full bg-gradient-to-tr ${gradient.class} border-2 ${avatarColor === gradient.class && !avatarUrl ? 'border-cyan-400 scale-110' : 'border-transparent hover:scale-105'
                      } transition-all duration-150`}
                  />
                ))}
              </div>
              <div className="pt-2">
                <input
                  type="text"
                  placeholder="Or paste Custom Image URL"
                  value={avatarUrl}
                  onChange={(e) => setAvatarUrl(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-[11px] text-slate-300 placeholder-slate-600 focus:outline-none focus:border-cyan-500/50"
                />
              </div>
            </div>

            {/* Save details helper button */}
            {(avatarColor !== user?.avatar_color || avatarUrl !== user?.avatar_url) && (
              <Button
                variant="primary"
                size="sm"
                onClick={handleUpdateProfile}
                className="w-full mt-4 text-[10px] py-1.5 font-bold uppercase tracking-wider"
              >
                Save Avatar Setup
              </Button>
            )}
          </Card>

          {/* Account Metrics Timeline Info */}
          <Card className="p-5 space-y-4">
            <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5 border-b border-slate-800/80 pb-2">
              <Calendar className="w-4 h-4 text-cyan-400" />
              Identity Attributes
            </h4>
            <div className="space-y-3 text-[11px]">
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Security Clearance</span>
                <Badge variant={user?.role === 'Admin' ? 'danger' : 'info'}>
                  {user?.role || 'Fraud Analyst'}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Registered Domain</span>
                <span className="text-slate-300 font-semibold">{user?.email.split('@')[1]}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Workspace Member Since</span>
                <span className="text-slate-300 font-semibold">{memberSince}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Last Authentication</span>
                <span className="text-slate-300 font-mono">
                  {user?.last_login
                    ? formatDateTime(user.last_login)
                    : 'Just now'}
                </span>
              </div>
            </div>
          </Card>
        </div>

        {/* ── RIGHT COLUMN: Config Tabs ──────────────────────────────────── */}
        <div className="space-y-6 lg:col-span-2">

          {/* Navigation Controls */}
          <div className="flex border-b border-slate-800 pb-3 gap-2 overflow-x-auto">
            {[
              { id: 'settings', label: 'Preferences & Details', icon: User },
              { id: 'sessions', label: `Active Devices (${centerData?.user?.sessions?.length || 0})`, icon: Monitor },
              { id: 'timeline', label: 'Activity Logs', icon: Activity },
              { id: 'stats', label: 'Work History', icon: FileText }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition-all whitespace-nowrap ${activeTab === tab.id
                  ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 shadow-lg shadow-cyan-500/5'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                  }`}
              >
                <tab.icon className="w-3.5 h-3.5" />
                <span>{tab.label}</span>
              </button>
            ))}
          </div>

          {/* ── TAB 1: Preferences & details ───────────────────────────────── */}
          {activeTab === 'settings' && (
            <div className="space-y-6">

              {/* Personal Details Form */}
              <Card title="Account Profile Attributes" subtitle="Edit credentials and custom display attributes.">
                <form onSubmit={handleUpdateProfile} className="space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <Input
                      label="Full Name"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      icon={User}
                    />
                    <Input
                      label="Email Address"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      icon={Mail}
                    />
                  </div>

                  {updateMsg && <p className="text-xs text-emerald-400 flex items-center gap-1"><Check className="w-3.5 h-3.5" /> {updateMsg}</p>}
                  {updateError && <p className="text-xs text-red-400 flex items-center gap-1"><AlertTriangle className="w-3.5 h-3.5" /> {updateError}</p>}

                  <Button type="submit" variant="primary" size="sm" className="mt-2 font-bold uppercase text-[10px]">
                    Update Profile Details
                  </Button>
                </form>
              </Card>

              {/* Personal Preferences Settings */}
              <Card title="Personal Preferences" subtitle="Configured toggles persist instantly.">
                <div className="space-y-4">

                  {/* Notifications Toggles */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="flex items-center justify-between p-3 rounded-lg bg-slate-900/60 border border-slate-800/80">
                      <div>
                        <span className="text-xs font-semibold text-slate-200">Email Notifications</span>
                        <p className="text-[10px] text-slate-500 mt-0.5">Receive alert summaries on risk escalations.</p>
                      </div>
                      <button
                        onClick={() => handleTogglePreference('email_notifications')}
                        className={`w-10 h-6 flex items-center rounded-full p-1 cursor-pointer transition-colors duration-200 ${preferences.email_notifications ? 'bg-cyan-500' : 'bg-slate-800'
                          }`}
                      >
                        <div className={`bg-slate-950 w-4 h-4 rounded-full shadow-md transform duration-200 ${preferences.email_notifications ? 'translate-x-4' : 'translate-x-0'
                          }`} />
                      </button>
                    </div>

                    <div className="flex items-center justify-between p-3 rounded-lg bg-slate-900/60 border border-slate-800/80">
                      <div>
                        <span className="text-xs font-semibold text-slate-200">System Notification Banners</span>
                        <p className="text-[10px] text-slate-500 mt-0.5">Push popup banners for live incidents.</p>
                      </div>
                      <button
                        onClick={() => handleTogglePreference('system_alerts')}
                        className={`w-10 h-6 flex items-center rounded-full p-1 cursor-pointer transition-colors duration-200 ${preferences.system_alerts ? 'bg-cyan-500' : 'bg-slate-800'
                          }`}
                      >
                        <div className={`bg-slate-950 w-4 h-4 rounded-full shadow-md transform duration-200 ${preferences.system_alerts ? 'translate-x-4' : 'translate-x-0'
                          }`} />
                      </button>
                    </div>
                  </div>

                  {/* Themes / Languages selectors */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800/80 space-y-1.5">
                      <label className="text-xs font-semibold text-slate-200">Workspace Color Theme</label>
                      <div className="flex gap-2">
                        {['dark', 'light', 'glassmorphism'].map(theme => (
                          <button
                            key={theme}
                            onClick={async () => {
                              const updated = { ...preferences, theme };
                              setPreferences(updated);
                              await authService.updateProfileDetails({ preferences: updated });
                            }}
                            className={`px-3 py-1 text-[10px] font-bold uppercase rounded border transition-all ${preferences.theme === theme
                              ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30'
                              : 'text-slate-400 hover:text-slate-200 border-slate-800 bg-slate-950/40'
                              }`}
                          >
                            {theme}
                          </button>
                        ))}
                      </div>
                    </div>

                    <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800/80 space-y-1.5">
                      <label className="text-xs font-semibold text-slate-200">Default Translation / Locale</label>
                      <select
                        value={preferences.language || 'en'}
                        onChange={handleLanguageChange}
                        className="w-full bg-slate-950 border border-slate-800 text-xs text-slate-300 rounded px-2 py-1.5 focus:outline-none focus:border-cyan-500/40 cursor-pointer"
                      >
                        <option value="en">English (US)</option>
                        <option value="es">Español (ES)</option>
                        <option value="fr">Français (FR)</option>
                        <option value="de">Deutsch (DE)</option>
                      </select>
                    </div>
                  </div>

                </div>
              </Card>

              {/* Password Change Form */}
              <Card title="Change Security Password" subtitle="Enter credentials to register a new session password.">
                <form onSubmit={handleChangePassword} className="space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div className="relative w-full">
                      <Input
                        type={showOldPass ? 'text' : 'password'}
                        label="Old Password"
                        value={oldPassword}
                        onChange={(e) => setOldPassword(e.target.value)}
                        icon={Key}
                      />
                      <button
                        type="button"
                        onClick={() => setShowOldPass(!showOldPass)}
                        className="absolute right-3 top-[34px] text-slate-500 hover:text-slate-300"
                      >
                        {showOldPass ? <EyeOff size={14} /> : <Eye size={14} />}
                      </button>
                    </div>

                    <div className="relative w-full">
                      <Input
                        type={showNewPass ? 'text' : 'password'}
                        label="New Password"
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        icon={Key}
                      />
                      <button
                        type="button"
                        onClick={() => setShowNewPass(!showNewPass)}
                        className="absolute right-3 top-[34px] text-slate-500 hover:text-slate-300"
                      >
                        {showNewPass ? <EyeOff size={14} /> : <Eye size={14} />}
                      </button>
                    </div>

                    <Input
                      type="password"
                      label="Confirm Password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      icon={Key}
                    />
                  </div>

                  {passMsg && <p className="text-xs text-emerald-400 flex items-center gap-1"><Check className="w-3.5 h-3.5" /> {passMsg}</p>}
                  {passError && <p className="text-xs text-red-400 flex items-center gap-1"><AlertTriangle className="w-3.5 h-3.5" /> {passError}</p>}

                  <Button type="submit" variant="primary" size="sm" className="font-bold uppercase text-[10px]">
                    Register Password Change
                  </Button>
                </form>
              </Card>

            </div>
          )}

          {/* ── TAB 2: Device Sessions ────────────────────────────────────── */}
          {activeTab === 'sessions' && (
            <Card title="Active Device Audits" subtitle="Manage and revoke active login sessions.">
              <div className="space-y-4">

                {sessionMsg && (
                  <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs flex items-center gap-1">
                    <CheckCircle className="w-4 h-4" />
                    <span>{sessionMsg}</span>
                  </div>
                )}

                <div className="flex justify-between items-center pb-2 border-b border-slate-800">
                  <span className="text-xs font-bold text-slate-300">Outstanding Active Logins</span>
                  {centerData?.user?.sessions?.length > 1 && (
                    <Button
                      variant="danger"
                      size="sm"
                      onClick={handleRevokeAllOther}
                      className="text-[9px] py-1 font-bold uppercase tracking-wider"
                    >
                      Log Out All Other Devices
                    </Button>
                  )}
                </div>

                <div className="space-y-3">
                  {centerData?.user?.sessions?.length === 0 ? (
                    <p className="text-center py-6 text-slate-500 text-xs">No active devices registered.</p>
                  ) : (
                    centerData.user.sessions.map((sess) => {
                      const isCurrent = sess.user_agent === navigator.userAgent; // approximation
                      return (
                        <div
                          key={sess.session_id}
                          className={`p-3.5 rounded-xl border flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 ${isCurrent
                            ? 'bg-slate-900 border-cyan-500/20'
                            : 'bg-slate-900/60 border-slate-800'
                            }`}
                        >
                          <div className="flex gap-3">
                            <div className="p-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-400 flex items-center justify-center">
                              {sess.device_type === 'Mobile' ? <Smartphone size={16} /> : <Monitor size={16} />}
                            </div>
                            <div>
                              <div className="flex items-center gap-2">
                                <span className="text-xs font-bold text-slate-200">
                                  {sess.browser} on {sess.os}
                                </span>
                                {isCurrent && <Badge variant="success" className="text-[8px] py-0 px-1 font-extrabold">Current Device</Badge>}
                              </div>
                              <p className="text-[10px] text-slate-500 font-mono mt-0.5">
                                IP: {sess.ip_address}  •  Location: {sess.location}
                              </p>
                              <p className="text-[9px] text-slate-600 mt-1">
                                Started: {formatDateTime(sess.created_at)}
                              </p>
                            </div>
                          </div>

                          {!isCurrent && (
                            <button
                              onClick={() => handleRevokeSession(sess.session_id)}
                              className="text-[10px] px-2.5 py-1.5 rounded border border-red-500/20 hover:border-red-500/40 text-red-400 hover:bg-red-500/5 transition-all self-start sm:self-center font-bold flex items-center gap-1"
                            >
                              <Trash2 size={12} />
                              Revoke Access
                            </button>
                          )}
                        </div>
                      );
                    })
                  )}
                </div>

              </div>
            </Card>
          )}

          {/* ── TAB 3: Activity Timeline ──────────────────────────────────── */}
          {activeTab === 'timeline' && (
            <Card title="Workspace Security Logs" subtitle="Historical audit logs of authentication and credential events.">
              <div className="space-y-4">

                {centerData?.user?.login_history?.length === 0 ? (
                  <p className="text-center py-6 text-slate-500 text-xs">No activity log entries found.</p>
                ) : (
                  <div className="relative border-l border-slate-800 pl-4 ml-3 space-y-6 py-2">
                    {centerData.user.login_history.map((log) => {
                      const isFailed = log.status === 'Failed';
                      return (
                        <div key={log.id} className="relative">
                          {/* Circle dot marker */}
                          <div className={`absolute -left-[25px] top-0.5 p-1 rounded-full border ${isFailed ? 'bg-red-950 border-red-500/40' : 'bg-slate-950 border-slate-800'
                            }`}>
                            {isFailed ? <AlertTriangle className="w-3 h-3 text-red-400" /> : getActivityIcon(log.type || 'auth_login')}
                          </div>

                          {/* Event info */}
                          <div>
                            <div className="flex items-center gap-2">
                              <span className={`text-xs font-bold ${isFailed ? 'text-red-400' : 'text-slate-200'}`}>
                                {isFailed ? 'Failed Authentication Attempt' : 'Successful User Session Logged'}
                              </span>
                              <span className="text-[9px] text-slate-500">{getRelativeTime(log.timestamp)}</span>
                            </div>
                            <p className="text-[10px] text-slate-400 mt-1">
                              Device profile: <span className="font-semibold text-slate-300">{log.device}</span>
                            </p>
                            <p className="text-[9px] text-slate-500 font-mono mt-0.5">
                              IP: {log.ip_address}  •  Location Hint: {log.location}
                            </p>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}

              </div>
            </Card>
          )}

          {/* ── TAB 4: Work History Statistics ─────────────────────────────── */}
          {activeTab === 'stats' && (
            <div className="space-y-6">

              {/* Stat blocks grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                {[
                  { label: 'Avg Risk Score', val: `${stats.avg_risk_score}%`, color: 'text-orange-400', icon: Shield },
                  { label: 'Txns Scored', val: stats.total_transactions_investigated, color: 'text-cyan-400', icon: Cpu },
                  { label: 'Reports Ready', val: stats.total_reports_generated, color: 'text-blue-400', icon: FileText },
                  { label: 'Alerts Processed', val: stats.total_alerts_handled, color: 'text-emerald-400', icon: Bell }
                ].map((stat, i) => (
                  <Card key={i} glass className="p-3 text-center flex flex-col items-center justify-center">
                    <stat.icon className={`w-5 h-5 mb-1.5 ${stat.color}`} />
                    <span className="text-[9px] font-bold text-slate-500 uppercase tracking-wider">{stat.label}</span>
                    <span className="text-lg font-extrabold text-slate-100 mt-1">{stat.val}</span>
                  </Card>
                ))}
              </div>

              {/* Recent Reports Table */}
              <Card title="Recent Investigative Reports" subtitle="Gemini AI generated report archives.">
                <div className="overflow-x-auto">
                  {centerData?.recent_reports?.length === 0 ? (
                    <p className="text-center py-6 text-slate-500 text-xs">No recent reports found.</p>
                  ) : (
                    <table className="w-full text-left text-[11px]">
                      <thead>
                        <tr className="border-b border-slate-800/80 text-slate-500 font-bold uppercase tracking-wider">
                          <th className="py-2.5">Tx ID</th>
                          <th className="py-2.5">Merchant</th>
                          <th className="py-2.5">Risk Score</th>
                          <th className="py-2.5">Date</th>
                        </tr>
                      </thead>
                      <tbody>
                        {centerData.recent_reports.map((rep) => (
                          <tr key={rep.id} className="border-b border-slate-900/60 hover:bg-slate-900/20">
                            <td className="py-2.5 font-mono text-cyan-400">
                              TXN-{rep.transaction_id.slice(-6).toUpperCase()}
                            </td>
                            <td className="py-2.5 text-slate-300">{rep.merchant_name}</td>
                            <td className="py-2.5">
                              <span className={`font-bold ${rep.risk_score >= 80 ? 'text-red-400' : rep.risk_score >= 50 ? 'text-orange-400' : 'text-emerald-400'
                                }`}>
                                {rep.risk_score}%
                              </span>
                            </td>
                            <td className="py-2.5 text-slate-500">
                              {formatDate(rep.created_at)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              </Card>

              {/* Recent Alerts Feed */}
              <Card title="Latest System Incidents" subtitle="Live feed alert notifications.">
                <div className="space-y-2">
                  {centerData?.recent_notifications?.length === 0 ? (
                    <p className="text-center py-6 text-slate-500 text-xs">No recent alerts found.</p>
                  ) : (
                    centerData.recent_notifications.map((notif) => (
                      <div
                        key={notif.id}
                        className={`p-2.5 rounded-lg border text-[11px] flex justify-between items-start ${notif.is_read
                          ? 'bg-slate-950/20 border-slate-900/80 opacity-60'
                          : 'bg-slate-900/40 border-slate-800'
                          }`}
                      >
                        <div>
                          <span className="font-semibold text-slate-300">{notif.title}</span>
                          <p className="text-slate-500 mt-0.5 line-clamp-1">{notif.message}</p>
                        </div>
                        <span className="text-[9px] text-slate-600 flex-shrink-0 ml-4">
                          {getRelativeTime(notif.created_at)}
                        </span>
                      </div>
                    ))
                  )}
                </div>
              </Card>

            </div>
          )}

        </div>

      </div>

    </DashboardLayout>
  );
}
