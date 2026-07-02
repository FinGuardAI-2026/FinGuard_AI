import React from "react";
import { createPortal } from "react-dom";
import clsx from 'clsx';

export function Button({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  className,
  disabled,
  ...props
}) {
  const baseStyles = 'inline-flex items-center justify-center font-medium transition-all duration-200 rounded-lg focus:outline-none focus:ring-2 disabled:opacity-50 disabled:cursor-not-allowed';

  const variants = {
    primary: 'bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold focus:ring-cyan-500/50 shadow-lg shadow-cyan-500/20',
    secondary: 'bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 focus:ring-slate-600',
    danger: 'bg-red-500 hover:bg-red-400 text-white font-semibold focus:ring-red-500/50 shadow-lg shadow-red-500/20',
    ghost: 'bg-transparent hover:bg-slate-800/60 text-slate-400 hover:text-slate-200 focus:ring-slate-700',
    outline: 'border border-cyan-500/40 text-cyan-400 hover:bg-cyan-500/10 focus:ring-cyan-500/30'
  };

  const sizes = {
    sm: 'px-2.5 py-1.5 text-xs',
    md: 'px-4 py-2 text-sm',
    lg: 'px-5 py-2.5 text-base'
  };

  return (
    <button
      className={clsx(baseStyles, variants[variant], sizes[size], className)}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <>
          <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-current" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          Loading...
        </>
      ) : children}
    </button>
  );
}

export function Badge({ children, variant = 'info', className }) {
  const variants = {
    info: 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20',
    success: 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20',
    warning: 'bg-amber-500/10 text-amber-400 border border-amber-500/20',
    danger: 'bg-red-500/10 text-red-400 border border-red-500/20',
    neutral: 'bg-slate-800 text-slate-400 border border-slate-700'
  };

  return (
    <span className={clsx('inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider', variants[variant], className)}>
      {children}
    </span>
  );
}

export function Card({ children, className, glass = true, title, subtitle, action }) {
  return (
    <div className={clsx(
      'rounded-xl p-5 border transition-all duration-200',
      glass ? 'glass shadow-card' : 'bg-slate-900 border-slate-800',
      className
    )}>
      {(title || action) && (
        <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800/80">
          <div>
            {title && <h3 className="text-base font-semibold text-slate-100">{title}</h3>}
            {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      {children}
    </div>
  );
}

export function Input({ label, error, helperText, className, icon: Icon, ...props }) {
  return (
    <div className="w-full">
      {label && <label className="fg-label">{label}</label>}
      <div className="relative">
        {Icon && (
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
            <Icon size={16} />
          </div>
        )}
        <input
          className={clsx(
            'fg-input',
            Icon && 'pl-9',
            error && 'border-red-500 focus:ring-red-500/40 focus:border-red-500',
            className
          )}
          {...props}
        />
      </div>
      {error && <p className="text-xs text-red-400 mt-1">{error}</p>}
      {helperText && !error && <p className="text-xs text-slate-500 mt-1">{helperText}</p>}
    </div>
  );
}

export function Modal({
  isOpen,
  onClose,
  title,
  children,
  maxWidth = "max-w-5xl"
}) {

  if (!isOpen) return null;

  return createPortal(

    <div className="fixed inset-0 z-[9999]">

      <div
        className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm"
        onClick={onClose}
      />

      <div className="absolute inset-0 flex items-center justify-center p-6">

        <div
          className={clsx(
            "w-full rounded-2xl glass border border-slate-700 shadow-2xl",
            "max-h-[90vh] overflow-y-auto",
            maxWidth
          )}
        >

          <div className="sticky top-0 z-10 bg-slate-900/90 backdrop-blur border-b border-slate-800 p-6 flex justify-between items-center">

            <h3 className="text-lg font-semibold text-slate-100">
              {title}
            </h3>

            <button
              onClick={onClose}
              className="text-slate-400 hover:text-white"
            >
              ✕
            </button>

          </div>

          <div className="p-6">

            {children}

          </div>

        </div>

      </div>

    </div>,

    document.body

  );
}

export function Spinner({ size = 'md', className }) {
  const sizes = { sm: 'w-4 h-4', md: 'w-8 h-8', lg: 'w-12 h-12' };
  return (
    <div className={clsx('animate-spin rounded-full border-2 border-slate-700 border-t-cyan-500', sizes[size], className)} />
  );
}
