import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { AuthLayout } from '../layouts/AuthLayout';
import { Card, Button, Input } from '../components/ui';
import { ShieldAlert, Lock, User} from 'lucide-react';

export function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Authentication failed. Please check credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthLayout>
      <Card glass className="p-8 border-slate-700/60 shadow-2xl">
        <div className="flex flex-col items-center text-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-500/25 mb-4">
            <ShieldAlert className="w-8 h-8 text-slate-950" />
          </div>
          <h1 className="text-2xl font-bold text-slate-100 tracking-tight font-mono">
            FinGuard <span className="text-cyan-400">AI</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">Enterprise Fraud Detection & Intelligence Platform</p>
        </div>

        {error && (
          <div className="p-3 mb-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-medium text-center">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Email"
            type="text"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            icon={User}
            placeholder="Enter your email"
          />
          <Input
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            icon={Lock}
            placeholder="••••••••••••"
          />

          <Button type="submit" variant="primary" isLoading={isLoading} className="w-full py-3 mt-2 text-sm font-bold">
            Sign In to Workspace
          </Button>
        </form>
      </Card>
    </AuthLayout>
  );
}
