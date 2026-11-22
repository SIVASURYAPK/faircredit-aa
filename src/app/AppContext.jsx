import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { DEFAULT_PREFERENCES, DEFAULT_SETTINGS, initialTickets, STORAGE_KEYS } from '../services/mockData.js';
import { readStorage, writeStorage } from '../services/storage.js';

const AppContext = createContext(null);

export function AppProvider({ children }) {
  const [session, setSession] = useState(() => readStorage(STORAGE_KEYS.session, null));
  const [preferences, setPreferences] = useState(() => ({ ...DEFAULT_PREFERENCES, ...readStorage(STORAGE_KEYS.preferences, {}) }));
  const [settings, setSettings] = useState(() => ({ ...DEFAULT_SETTINGS, ...readStorage(STORAGE_KEYS.settings, {}) }));
  const [tickets, setTickets] = useState(() => readStorage(STORAGE_KEYS.tickets, initialTickets));
  const [toasts, setToasts] = useState([]);

  useEffect(() => {
    document.documentElement.classList.toggle('dark', preferences.theme === 'dark');
    document.documentElement.lang = preferences.language === 'हिंदी' ? 'hi' : preferences.language === 'தமிழ்' ? 'ta' : 'en';
    writeStorage(STORAGE_KEYS.preferences, preferences);
  }, [preferences]);
  useEffect(() => {
    writeStorage(STORAGE_KEYS.settings, settings);
  }, [settings]);
  useEffect(() => {
    writeStorage(STORAGE_KEYS.tickets, tickets);
  }, [tickets]);
  useEffect(() => {
    try {
      if (session && session.rememberMe !== false) writeStorage(STORAGE_KEYS.session, session);
      else window.localStorage.removeItem(STORAGE_KEYS.session);
    } catch {
      return;
    }
  }, [session]);

  const notify = useCallback((message, tone = 'success') => {
    const id = `${Date.now()}-${Math.random()}`;
    setToasts((current) => [...current, { id, message, tone }]);
    window.setTimeout(() => setToasts((current) => current.filter((toast) => toast.id !== id)), 3600);
  }, []);
  const updatePreference = useCallback((key, value) => setPreferences((current) => ({ ...current, [key]: value })), []);
  const updateSetting = useCallback((key, value) => setSettings((current) => ({ ...current, [key]: value })), []);
  const dismissToast = useCallback((id) => setToasts((current) => current.filter((toast) => toast.id !== id)), []);
  const value = useMemo(() => ({
    session, setSession, preferences, updatePreference, settings, updateSetting,
    tickets, setTickets, toasts, notify, dismissToast,
  }), [session, preferences, updatePreference, settings, updateSetting, tickets, toasts, notify, dismissToast]);

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp() {
  const context = useContext(AppContext);
  if (!context) throw new Error('useApp must be used inside AppProvider');
  return context;
}
