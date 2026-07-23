/**
 * CommandPalette.jsx — Enterprise Command Palette (Ctrl+K)
 *
 * Features:
 *  - Full-screen overlay with glassmorphism backdrop
 *  - Debounced search (300 ms) against backend
 *  - Prefix-filter hints (user:, merchant:, country:, risk:)
 *  - Keyboard navigation (↑/↓/Enter/Esc)
 *  - Highlighted matching text
 *  - Quick-preview right panel
 *  - Category-grouped results
 *  - Recent searches (empty-state suggestions)
 *  - Optimistic loading skeleton
 *  - Cached previous queries (via search service)
 *  - Read/act on results with animations
 */

import React, {
  useState,
  useEffect,
  useRef,
  useCallback,
  useMemo,
} from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  X,
  Clock,
  ChevronRight,
  User,
  ArrowLeftRight,
  Zap,
  FileText,
  Bell,
  Settings,
  LayoutDashboard,
  BarChart2,
  Plus,
  FilePlus,
  Globe,
  Building2,
  AlertTriangle,
  Shield,
  Loader2,
  Command,
  Hash,
  Trash2,
} from 'lucide-react';

import {
  globalSearch,
  BUILTIN_COMMANDS,
  rankItems,
  getRecentSearches,
  addRecentSearch,
  clearRecentSearches,
  parseQuery,
} from '../../services/search';

// ---------------------------------------------------------------------------
// Icon map — maps icon-name strings (from search service) to Lucide components
// ---------------------------------------------------------------------------
const ICON_MAP = {
  LayoutDashboard, ArrowLeftRight, Zap, FileText, Bell,
  User, Settings, BarChart2, Plus, FilePlus, Globe,
  Building2, AlertTriangle, Shield, Hash,
};

function Icon({ name, className = 'w-4 h-4' }) {
  const Comp = ICON_MAP[name] ?? Hash;
  return <Comp className={className} />;
}

// ---------------------------------------------------------------------------
// Text highlighter — wraps matching segments in <mark>
// ---------------------------------------------------------------------------
function Highlight({ text = '', query = '' }) {
  if (!query.trim()) return <span>{text}</span>;
  const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
  const parts = text.split(regex);
  return (
    <span>
      {parts.map((part, i) =>
        regex.test(part) ? (
          <mark key={i} className="bg-cyan-500/30 text-cyan-300 rounded px-0.5 not-italic">
            {part}
          </mark>
        ) : (
          <span key={i}>{part}</span>
        )
      )}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Category config
// ---------------------------------------------------------------------------
const CATEGORY_META = {
  navigation: { label: 'Navigation', color: 'text-indigo-400', icon: 'LayoutDashboard' },
  action: { label: 'Actions', color: 'text-cyan-400', icon: 'Zap' },
  users: { label: 'Users', color: 'text-violet-400', icon: 'User' },
  transactions: { label: 'Transactions', color: 'text-emerald-400', icon: 'ArrowLeftRight' },
  predictions: { label: 'Predictions', color: 'text-amber-400', icon: 'Zap' },
  reports: { label: 'Reports', color: 'text-blue-400', icon: 'FileText' },
  merchants: { label: 'Merchants', color: 'text-pink-400', icon: 'Building2' },
  countries: { label: 'Countries', color: 'text-teal-400', icon: 'Globe' },
};

// ---------------------------------------------------------------------------
// Skeleton row for optimistic loading
// ---------------------------------------------------------------------------
function SkeletonRow() {
  return (
    <div className="flex items-center gap-3 px-4 py-3 animate-pulse">
      <div className="w-6 h-6 rounded-md bg-slate-700/60 flex-shrink-0" />
      <div className="flex-1 space-y-1.5">
        <div className="h-3 bg-slate-700/60 rounded w-2/3" />
        <div className="h-2 bg-slate-800/60 rounded w-1/3" />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Quick-preview panel
// ---------------------------------------------------------------------------
function PreviewPanel({ item }) {
  if (!item) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 text-slate-600">
        <Command className="w-10 h-10 mb-3 opacity-30" />
        <p className="text-xs">Select a result to preview</p>
      </div>
    );
  }

  const meta = CATEGORY_META[item._category] ?? CATEGORY_META.navigation;

  const fields = Object.entries(item._raw ?? {}).filter(
    ([k]) => !['_id', '__v', 'password', 'hashed_password'].includes(k)
  );

  return (
    <div className="flex-1 p-5 overflow-y-auto">
      {/* Header */}
      <div className="flex items-center gap-3 mb-5">
        <div className={`w-9 h-9 rounded-xl flex items-center justify-center bg-slate-800 border border-slate-700 ${meta.color}`}>
          <Icon name={item._icon ?? meta.icon} className="w-5 h-5" />
        </div>
        <div>
          <p className={`text-sm font-semibold ${meta.color}`}>{item.label}</p>
          <span className="text-[10px] text-slate-500 uppercase tracking-wider">{meta.label}</span>
        </div>
      </div>

      {/* Fields */}
      <div className="space-y-2">
        {item._description && (
          <div className="text-xs text-slate-400 bg-slate-800/50 rounded-lg p-3 leading-relaxed border border-slate-700/50">
            {item._description}
          </div>
        )}
        {fields.slice(0, 10).map(([k, v]) => (
          <div key={k} className="flex items-start gap-2 text-[11px]">
            <span className="text-slate-500 capitalize min-w-[80px] pt-0.5 flex-shrink-0">
              {k.replace(/_/g, ' ')}
            </span>
            <span className="text-slate-300 break-all">
              {typeof v === 'boolean' ? (v ? 'Yes' : 'No') : String(v ?? '—')}
            </span>
          </div>
        ))}
      </div>

      {item._path && (
        <div className="mt-5 pt-4 border-t border-slate-800">
          <p className="text-[10px] text-slate-500 mb-1">Press ↵ to navigate</p>
          <code className="text-[10px] text-cyan-400 bg-slate-900 px-2 py-1 rounded">{item._path}</code>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Result item row
// ---------------------------------------------------------------------------
function ResultRow({ item, isActive, onHover, onClick, query }) {
  const meta = CATEGORY_META[item._category] ?? CATEGORY_META.navigation;
  const ref = useRef(null);

  useEffect(() => {
    if (isActive && ref.current) {
      ref.current.scrollIntoView({ block: 'nearest' });
    }
  }, [isActive]);

  return (
    <div
      ref={ref}
      onClick={onClick}
      onMouseEnter={onHover}
      className={`flex items-center gap-3 px-4 py-2.5 cursor-pointer transition-all duration-150 rounded-lg mx-1 group ${isActive
        ? 'bg-cyan-500/10 border border-cyan-500/20'
        : 'hover:bg-slate-800/60 border border-transparent'
        }`}
    >
      <div
        className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 text-sm
          ${isActive ? `bg-slate-800 ${meta.color}` : 'bg-slate-800/60 text-slate-500 group-hover:text-slate-300'}`}
      >
        <Icon name={item._icon ?? meta.icon} className="w-3.5 h-3.5" />
      </div>

      <div className="flex-1 min-w-0">
        <p className={`text-xs font-medium truncate ${isActive ? 'text-slate-100' : 'text-slate-300'}`}>
          <Highlight text={item.label} query={query} />
        </p>
        {item._description && (
          <p className="text-[10px] text-slate-500 truncate mt-0.5">
            <Highlight text={item._description} query={query} />
          </p>
        )}
      </div>

      {item._badge && (
        <span className={`text-[9px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wide border
          ${item._badge === 'fraud' ? 'bg-red-500/10 border-red-500/30 text-red-400'
            : item._badge === 'safe' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
              : 'bg-slate-700/60 border-slate-600/40 text-slate-400'}`}>
          {item._badge}
        </span>
      )}

      <ChevronRight
        className={`w-3.5 h-3.5 flex-shrink-0 transition-opacity ${isActive ? 'opacity-100 text-cyan-400' : 'opacity-0'}`}
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Map API response → normalised result items
// ---------------------------------------------------------------------------
function normaliseResults(apiData, cleanQuery) {
  const groups = [];

  const push = (category, items) => {
    if (items?.length) groups.push({ category, items });
  };

  // Transactions
  const txItems = (apiData.transactions ?? []).map((t) => ({
    id: t._id ?? t.id,
    label: `TXN-${String(t._id ?? t.id ?? '').slice(-8).toUpperCase()}`,
    _description: `${t.merchant_name ?? t.merchant ?? ''}  •  $${t.amount ?? 0}`,
    _category: 'transactions',
    _icon: 'ArrowLeftRight',
    _badge: t.is_fraud ? 'fraud' : 'safe',
    _path: `/transactions`,
    _raw: t,
  }));
  push('transactions', txItems);

  // Predictions
  const predItems = (apiData.predictions ?? []).map((p) => ({
    id: p._id ?? p.id,
    label: `Prediction ${String(p._id ?? '').slice(-8)}`,
    _description: `Risk ${p.risk_score ?? p.score ?? 0}%  •  ${p.merchant_name ?? p.merchant ?? ''}`,
    _category: 'predictions',
    _icon: 'Zap',
    _badge: (p.risk_score ?? p.score ?? 0) > 70 ? 'fraud' : 'safe',
    _path: `/predictions`,
    _raw: p,
  }));
  push('predictions', predItems);

  // Reports
  const reportItems = (apiData.reports ?? []).map((r) => ({
    id: r._id ?? r.id,
    label: r.title ?? r.name ?? `Report ${String(r._id ?? '').slice(-6)}`,
    _description: r.description ?? r.report_type ?? '',
    _category: 'reports',
    _icon: 'FileText',
    _path: `/reports`,
    _raw: r,
  }));
  push('reports', reportItems);

  // Users
  const userItems = (apiData.users ?? []).map((u) => ({
    id: u._id ?? u.id,
    label: u.full_name ?? u.email ?? 'Unknown',
    _description: `${u.email ?? ''}  •  ${u.role ?? ''}`,
    _category: 'users',
    _icon: 'User',
    _path: `/users`,
    _raw: u,
  }));
  push('users', userItems);

  // Merchants
  const merchantItems = (apiData.merchants ?? []).map((m) => ({
    id: m._id ?? m.id ?? m,
    label: typeof m === 'string' ? m : (m.name ?? m.merchant_name ?? String(m)),
    _description: typeof m === 'string' ? '' : (m.category ?? ''),
    _category: 'merchants',
    _icon: 'Building2',
    _path: `/transactions`,
    _raw: typeof m === 'string' ? { name: m } : m,
  }));
  push('merchants', merchantItems);

  // Countries
  const countryItems = (apiData.countries ?? []).map((c) => ({
    id: c._id ?? c.id ?? c,
    label: typeof c === 'string' ? c : (c.name ?? c.country ?? String(c)),
    _description: '',
    _category: 'countries',
    _icon: 'Globe',
    _path: `/analytics`,
    _raw: typeof c === 'string' ? { name: c } : c,
  }));
  push('countries', countryItems);

  // Rank each group's items
  return groups.map(({ category, items }) => ({
    category,
    items: rankItems(items, cleanQuery, (x) => x.label),
  }));
}

// ---------------------------------------------------------------------------
// Filter built-in commands against query
// ---------------------------------------------------------------------------
function filterCommands(query) {
  if (!query.trim()) return BUILTIN_COMMANDS;
  const q = query.toLowerCase();
  return rankItems(
    BUILTIN_COMMANDS.filter(
      (c) =>
        c.label.toLowerCase().includes(q) ||
        c.category.toLowerCase().includes(q)
    ),
    q,
    (x) => x.label
  );
}

// ---------------------------------------------------------------------------
// Main CommandPalette component
// ---------------------------------------------------------------------------
export function CommandPalette({ open, onClose }) {
  const navigate = useNavigate();
  const inputRef = useRef(null);
  const debounceRef = useRef(null);

  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [apiGroups, setApiGroups] = useState([]);   // from backend
  const [activeIndex, setActiveIndex] = useState(0);
  const [preview, setPreview] = useState(null);
  const [recents, setRecents] = useState([]);
  const abortRef = useRef(null);

  // Focus on open
  useEffect(() => {
    if (open) {
      setQuery('');
      setApiGroups([]);
      setActiveIndex(0);
      setPreview(null);
      setRecents(getRecentSearches());
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [open]);

  // Debounced search
  const doSearch = useCallback(async (raw) => {
    const trimmed = raw.trim();
    if (!trimmed) {
      setApiGroups([]);
      setLoading(false);
      return;
    }

    // Abort previous request
    abortRef.current?.abort();
    abortRef.current = new AbortController();

    setLoading(true);
    try {
      const data = await globalSearch(raw, abortRef.current.signal);
      const { cleanQuery } = parseQuery(raw);
      setApiGroups(normaliseResults(data, cleanQuery));
    } catch (err) {
      if (err?.name !== 'CanceledError' && err?.code !== 'ERR_CANCELED') {
        setApiGroups([]);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  const handleQueryChange = useCallback(
    (e) => {
      const val = e.target.value;
      setQuery(val);
      setActiveIndex(0);
      clearTimeout(debounceRef.current);
      debounceRef.current = setTimeout(() => doSearch(val), 300);
    },
    [doSearch]
  );

  // Flatten all selectable items for keyboard navigation
  const allItems = useMemo(() => {
    const { cleanQuery, filters } = parseQuery(query);
    const hasFilters = Object.keys(filters).length > 0;
    const cmds = filterCommands(cleanQuery).map((c) => ({
      ...c,
      _category: c.category,
      _icon: c.icon,
      _description: `Navigate to ${c.label}`,
      _path: c.path,
      _raw: c,
    }));

    // If there's a query or filters, include API results; otherwise show commands + recents placeholder
    const flat = [];
    if (!query.trim() && !hasFilters) {
      flat.push(...cmds);
    } else {
      // Commands first, then API results
      flat.push(...cmds);
      for (const { items } of apiGroups) {
        flat.push(...items);
      }
    }
    return flat;
  }, [query, apiGroups]);

  // Keyboard navigation
  const handleKeyDown = useCallback(
    (e) => {
      if (!open) return;

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setActiveIndex((i) => Math.min(i + 1, allItems.length - 1));
          setPreview(allItems[Math.min(activeIndex + 1, allItems.length - 1)] ?? null);
          break;
        case 'ArrowUp':
          e.preventDefault();
          setActiveIndex((i) => Math.max(i - 1, 0));
          setPreview(allItems[Math.max(activeIndex - 1, 0)] ?? null);
          break;
        case 'Enter': {
          e.preventDefault();
          const selected = allItems[activeIndex];
          if (selected?._path) {
            if (query.trim()) addRecentSearch(query.trim());
            navigate(selected._path);
            onClose();
          }
          break;
        }
        case 'Escape':
          onClose();
          break;
        default:
          break;
      }
    },
    [open, allItems, activeIndex, query, navigate, onClose]
  );

  // Update preview when activeIndex changes
  useEffect(() => {
    setPreview(allItems[activeIndex] ?? null);
  }, [activeIndex, allItems]);

  // Global key listener
  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  // Render groups for the list pane
  const { cleanQuery } = parseQuery(query);
  const cmdItems = filterCommands(cleanQuery).map((c) => ({
    ...c,
    _category: c.category,
    _icon: c.icon,
    _description: `Navigate to ${c.label}`,
    _path: c.path,
    _raw: c,
  }));

  let globalIdx = 0;
  const assignIdx = () => globalIdx++;

  if (!open) return null;

  return (
    /* Backdrop */
    <div
      className="fixed inset-0 z-[200] flex items-start justify-center pt-[10vh] px-4"
      style={{ background: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(6px)' }}
      onClick={onClose}
    >
      {/* Panel */}
      <div
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-3xl rounded-2xl shadow-2xl border border-slate-700/60 overflow-hidden flex flex-col"
        style={{
          background: 'linear-gradient(135deg, rgba(15,23,42,0.98) 0%, rgba(2,6,23,0.99) 100%)',
          maxHeight: '70vh',
          animation: 'cmdSlideIn 0.18s cubic-bezier(0.16,1,0.3,1)',
        }}
      >
        {/* ── Input row ─────────────────────────────────────────────── */}
        <div className="flex items-center gap-3 px-4 py-3.5 border-b border-slate-800">
          {loading
            ? <Loader2 className="w-4 h-4 text-cyan-400 animate-spin flex-shrink-0" />
            : <Search className="w-4 h-4 text-slate-500 flex-shrink-0" />
          }
          <input
            ref={inputRef}
            value={query}
            onChange={handleQueryChange}
            placeholder="Search or type a command…  user:alice  risk:high  country:us"
            className="flex-1 bg-transparent text-sm text-slate-100 placeholder-slate-600 outline-none"
            autoComplete="off"
            spellCheck={false}
          />
          {query && (
            <button
              onClick={() => { setQuery(''); setApiGroups([]); setActiveIndex(0); }}
              className="text-slate-600 hover:text-slate-400 transition-colors p-0.5"
            >
              <X className="w-4 h-4" />
            </button>
          )}
          <kbd className="hidden sm:flex items-center gap-0.5 px-1.5 py-0.5 text-[9px] rounded border border-slate-700 text-slate-500 font-mono">
            ESC
          </kbd>
        </div>

        {/* ── Body: list + preview ───────────────────────────────────── */}
        <div className="flex overflow-hidden" style={{ minHeight: '280px', maxHeight: 'calc(70vh - 60px)' }}>
          {/* ── List pane ─────────────────────────────────────────── */}
          <div className="flex-1 overflow-y-auto py-2 border-r border-slate-800/60">

            {/* Filter hints */}
            {query.trim() && (
              <div className="flex flex-wrap gap-1 px-4 pb-2">
                {['user:', 'merchant:', 'country:', 'risk:'].map((prefix) =>
                  !query.includes(prefix) ? (
                    <button
                      key={prefix}
                      onClick={() => {
                        const newVal = query.trim() + ' ' + prefix;
                        setQuery(newVal);
                        clearTimeout(debounceRef.current);
                        debounceRef.current = setTimeout(() => doSearch(newVal), 300);
                        inputRef.current?.focus();
                      }}
                      className="text-[10px] px-2 py-0.5 rounded border border-slate-700/60 text-slate-500 hover:border-cyan-500/40 hover:text-cyan-400 transition-colors font-mono"
                    >
                      {prefix}
                    </button>
                  ) : null
                )}
              </div>
            )}

            {/* Optimistic loading skeletons */}
            {loading && (
              <div className="space-y-0.5">
                {[1, 2, 3].map((n) => <SkeletonRow key={n} />)}
              </div>
            )}

            {/* Empty-state / recent searches */}
            {!loading && !query.trim() && (
              <>
                {/* Built-in commands */}
                <div className="px-4 pb-1 pt-1">
                  <span className="text-[9px] uppercase tracking-widest text-slate-600 font-semibold">
                    Quick Commands
                  </span>
                </div>
                {cmdItems.map((item) => {
                  const idx = assignIdx();
                  return (
                    <ResultRow
                      key={item.id}
                      item={item}
                      isActive={idx === activeIndex}
                      query=""
                      onHover={() => { setActiveIndex(idx); }}
                      onClick={() => { navigate(item._path); onClose(); }}
                    />
                  );
                })}

                {recents.length > 0 && (
                  <>
                    <div className="px-4 pt-3 pb-1 flex items-center justify-between">
                      <span className="text-[9px] uppercase tracking-widest text-slate-600 font-semibold">
                        Recent Searches
                      </span>
                      <button
                        onClick={() => { clearRecentSearches(); setRecents([]); }}
                        className="flex items-center gap-1 text-[9px] text-slate-600 hover:text-red-400 transition-colors"
                      >
                        <Trash2 className="w-3 h-3" /> Clear
                      </button>
                    </div>
                    {recents.map((r) => {
                      const idx = assignIdx();
                      return (
                        <button
                          key={r}
                          onMouseEnter={() => setActiveIndex(idx)}
                          onClick={() => {
                            setQuery(r);
                            clearTimeout(debounceRef.current);
                            doSearch(r);
                          }}
                          className={`w-full flex items-center gap-3 px-4 py-2 text-left transition-colors rounded-lg mx-1
                            ${idx === activeIndex ? 'bg-slate-800/60' : 'hover:bg-slate-800/40'}`}
                        >
                          <Clock className="w-3.5 h-3.5 text-slate-600 flex-shrink-0" />
                          <span className="text-xs text-slate-400">{r}</span>
                        </button>
                      );
                    })}
                  </>
                )}

                {recents.length === 0 && (
                  <div className="text-center py-8 text-slate-600 text-xs">
                    <Command className="w-8 h-8 mx-auto mb-2 opacity-20" />
                    <p>Start typing to search across everything</p>
                    <p className="text-[10px] mt-1 text-slate-700">
                      Try: <span className="text-slate-500 font-mono">user:alice</span>  or  <span className="text-slate-500 font-mono">risk:high</span>
                    </p>
                  </div>
                )}
              </>
            )}

            {/* Results when query is present */}
            {!loading && query.trim() && (
              <>
                {/* Commands */}
                {cmdItems.length > 0 && (
                  <>
                    <div className="px-4 pb-1 pt-1">
                      <span className="text-[9px] uppercase tracking-widest text-slate-600 font-semibold">Commands</span>
                    </div>
                    {cmdItems.map((item) => {
                      const idx = assignIdx();
                      return (
                        <ResultRow
                          key={item.id}
                          item={item}
                          isActive={idx === activeIndex}
                          query={cleanQuery}
                          onHover={() => setActiveIndex(idx)}
                          onClick={() => {
                            if (query.trim()) addRecentSearch(query.trim());
                            navigate(item._path);
                            onClose();
                          }}
                        />
                      );
                    })}
                  </>
                )}

                {/* API result groups */}
                {apiGroups.map(({ category, items }) => {
                  if (!items.length) return null;
                  const meta = CATEGORY_META[category] ?? {};
                  return (
                    <div key={category}>
                      <div className="px-4 pt-3 pb-1 flex items-center gap-1.5">
                        <Icon name={meta.icon} className={`w-3 h-3 ${meta.color}`} />
                        <span className="text-[9px] uppercase tracking-widest text-slate-600 font-semibold">
                          {meta.label}
                        </span>
                      </div>
                      {items.map((item) => {
                        const idx = assignIdx();
                        return (
                          <ResultRow
                            key={item.id}
                            item={item}
                            isActive={idx === activeIndex}
                            query={cleanQuery}
                            onHover={() => setActiveIndex(idx)}
                            onClick={() => {
                              if (query.trim()) addRecentSearch(query.trim());
                              if (item._path) navigate(item._path);
                              onClose();
                            }}
                          />
                        );
                      })}
                    </div>
                  );
                })}

                {/* True empty state */}
                {!loading && cmdItems.length === 0 && apiGroups.every(g => g.items.length === 0) && (
                  <div className="text-center py-10 text-slate-600 text-xs">
                    <AlertTriangle className="w-7 h-7 mx-auto mb-2 opacity-20" />
                    <p>
                      No results for <span className="text-slate-400">&quot;{query}&quot;</span>
                    </p>
                    <p className="text-[10px] mt-1 text-slate-700">
                      Try <span className="font-mono text-slate-500">user:</span>,&nbsp;
                      <span className="font-mono text-slate-500">merchant:</span>, or&nbsp;
                      <span className="font-mono text-slate-500">country:</span> filters
                    </p>
                  </div>
                )}
              </>
            )}
          </div>

          {/* ── Preview pane ──────────────────────────────────────── */}
          <div className="w-64 flex-shrink-0 hidden lg:flex flex-col border-l border-slate-800/40">
            <PreviewPanel item={preview} />
          </div>
        </div>

        {/* ── Footer ────────────────────────────────────────────────── */}
        <div className="flex items-center justify-between px-4 py-2 border-t border-slate-800 text-[10px] text-slate-600">
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1"><kbd className="bg-slate-800 px-1 py-0.5 rounded text-slate-500">↑↓</kbd> navigate</span>
            <span className="flex items-center gap-1"><kbd className="bg-slate-800 px-1 py-0.5 rounded text-slate-500">↵</kbd> open</span>
            <span className="flex items-center gap-1"><kbd className="bg-slate-800 px-1 py-0.5 rounded text-slate-500">esc</kbd> close</span>
          </div>
          <span className="flex items-center gap-1 text-slate-700">
            <Shield className="w-3 h-3" /> FinGuard AI
          </span>
        </div>
      </div>

      {/* Slide-in animation */}
      <style>{`
        @keyframes cmdSlideIn {
          from { opacity: 0; transform: translateY(-12px) scale(0.97); }
          to   { opacity: 1; transform: translateY(0)    scale(1);    }
        }
      `}</style>
    </div>
  );
}
