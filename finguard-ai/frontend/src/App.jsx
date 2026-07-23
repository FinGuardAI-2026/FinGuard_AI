import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { NotificationProvider } from './context/NotificationContext';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { Prediction } from './pages/Prediction';
import { Transactions } from './pages/Transactions';
import { Analytics } from './pages/Analytics';
import { Reports } from './pages/Reports';
import { Settings } from './pages/Settings';
import { Profile } from './pages/Profile';
import { Notifications } from './pages/Notifications';
import { AdminPanel } from './pages/admin/AdminPanel';

function ProtectedRoute({ children, adminOnly = false }) {
  const { isAuthenticated, user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-400 text-xs">
        Authenticating FinGuard Workspace...
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (adminOnly && user?.role !== 'Admin') {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
}

function App() {
  return (
    <AuthProvider>
      <NotificationProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            
            <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            <Route path="/prediction" element={<ProtectedRoute><Prediction /></ProtectedRoute>} />
            <Route path="/transactions" element={<ProtectedRoute><Transactions /></ProtectedRoute>} />
            <Route path="/analytics" element={<ProtectedRoute><Analytics /></ProtectedRoute>} />
            <Route path="/reports" element={<ProtectedRoute><Reports /></ProtectedRoute>} />
            <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
            <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
            <Route path="/notifications" element={<ProtectedRoute><Notifications /></ProtectedRoute>} />
            
            <Route path="/admin" element={<ProtectedRoute adminOnly><AdminPanel /></ProtectedRoute>} />

            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </BrowserRouter>
      </NotificationProvider>
    </AuthProvider>
  );
}

export default App;
