/**
 * search.js — Enterprise Global Search & Command Palette API service
 *
 * Features:
 *  - Caching (LRU-style with TTL) to avoid redundant API calls
 *  - Recent search history persisted in localStorage
 *  - Prefix filter parsing  (user:, merchant:, country:, risk:)
 *  - Ranking helpers (exact → startsWith → contains)
 */

import api from './api';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------
const CACHE_TTL_MS = 30_000;        // 30 s per cached query
const CACHE_MAX_SIZE = 50;          // LRU eviction after 50 distinct queries
const RECENT_KEY = 'finguard_recent_searches';
const RECENT_MAX = 8;

// ---------------------------------------------------------------------------
// Query cache
// ---------------------------------------------------------------------------
const cache = new Map();            // key → { data, expiresAt }

function cacheGet(key) {
  const entry = cache.get(key);
  if (!entry) return null;
  if (Date.now() > entry.expiresAt) {
    cache.delete(key);
    return null;
  }
  return entry.data;
}

function cacheSet(key, data) {
  if (cache.size >= CACHE_MAX_SIZE) {
    // evict oldest entry
    cache.delete(cache.keys().next().value);
  }
  cache.set(key, { data, expiresAt: Date.now() + CACHE_TTL_MS });
}

// ---------------------------------------------------------------------------
// Prefix-filter parser
// Parses tokens like  user:alice, merchant:paypal, country:us, risk:high
// Returns { cleanQuery, filters }
// ---------------------------------------------------------------------------
export function parseQuery(raw) {
  const tokens = raw.trim().split(/\s+/);
  const filters = {};
  const words = [];

  for (const token of tokens) {
    const match = token.match(/^(user|merchant|country|risk):(.+)$/i);
    if (match) {
      filters[match[1].toLowerCase()] = match[2].toLowerCase();
    } else {
      words.push(token);
    }
  }

  return { cleanQuery: words.join(' '), filters };
}

// ---------------------------------------------------------------------------
// Main search function (cached)
// ---------------------------------------------------------------------------
export async function globalSearch(rawQuery, signal) {
  const key = rawQuery.trim().toLowerCase();

  // Return cached result immediately
  const cached = cacheGet(key);
  if (cached) return cached;

  const { cleanQuery, filters } = parseQuery(rawQuery);

  const params = new URLSearchParams();
  params.set('q', cleanQuery);
  if (filters.user)     params.set('user', filters.user);
  if (filters.merchant) params.set('merchant', filters.merchant);
  if (filters.country)  params.set('country', filters.country);
  if (filters.risk)     params.set('risk', filters.risk);

  const { data } = await api.get(`/api/v1/search/?${params.toString()}`, { signal });
  cacheSet(key, data);
  return data;
}

// ---------------------------------------------------------------------------
// Built-in commands (navigation actions, no API needed)
// ---------------------------------------------------------------------------
export const BUILTIN_COMMANDS = [
  { id: 'cmd-dashboard',      label: 'Go to Dashboard',          icon: 'LayoutDashboard', path: '/dashboard',         category: 'navigation' },
  { id: 'cmd-transactions',   label: 'View Transactions',        icon: 'ArrowLeftRight',  path: '/transactions',      category: 'navigation' },
  { id: 'cmd-predictions',    label: 'Fraud Predictions',        icon: 'Zap',             path: '/predictions',       category: 'navigation' },
  { id: 'cmd-reports',        label: 'Reports',                  icon: 'FileText',        path: '/reports',           category: 'navigation' },
  { id: 'cmd-notifications',  label: 'Notifications',            icon: 'Bell',            path: '/notifications',     category: 'navigation' },
  { id: 'cmd-profile',        label: 'My Profile',               icon: 'User',            path: '/profile',           category: 'navigation' },
  { id: 'cmd-analytics',      label: 'Analytics',                icon: 'BarChart2',       path: '/analytics',         category: 'navigation' },
  { id: 'cmd-settings',       label: 'Settings',                 icon: 'Settings',        path: '/settings',          category: 'navigation' },
  { id: 'cmd-new-prediction', label: 'New Fraud Prediction',     icon: 'Plus',            path: '/predictions/new',   category: 'action' },
  { id: 'cmd-new-report',     label: 'Generate Report',          icon: 'FilePlus',        path: '/reports/new',       category: 'action' },
];

// ---------------------------------------------------------------------------
// Client-side ranking
// Priority: exact → startsWith → contains (case-insensitive)
// ---------------------------------------------------------------------------
export function rankItems(items, query, getLabelFn = (x) => x.label ?? x) {
  if (!query) return items;
  const q = query.toLowerCase();
  return [...items].sort((a, b) => {
    const la = getLabelFn(a).toLowerCase();
    const lb = getLabelFn(b).toLowerCase();
    const rankA = la === q ? 0 : la.startsWith(q) ? 1 : 2;
    const rankB = lb === q ? 0 : lb.startsWith(q) ? 1 : 2;
    return rankA - rankB;
  });
}

// ---------------------------------------------------------------------------
// Recent search history
// ---------------------------------------------------------------------------
export function getRecentSearches() {
  try {
    return JSON.parse(localStorage.getItem(RECENT_KEY) ?? '[]');
  } catch {
    return [];
  }
}

export function addRecentSearch(query) {
  if (!query?.trim()) return;
  const existing = getRecentSearches().filter(
    (r) => r.toLowerCase() !== query.toLowerCase()
  );
  const updated = [query.trim(), ...existing].slice(0, RECENT_MAX);
  localStorage.setItem(RECENT_KEY, JSON.stringify(updated));
}

export function clearRecentSearches() {
  localStorage.removeItem(RECENT_KEY);
}
