import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { Badge } from './Primitives.jsx';
import { Brand } from './Brand.jsx';
import { useApp } from '../app/AppContext.jsx';
import { Activity, ArrowUpRight, BadgeCheck, CircleHelp, FileCheck2, LayoutDashboard, LogOut, Moon, Settings2, Sun, UserRound } from 'lucide-react';

const navItems = [
  { to: '/dashboard', label: 'Overview', icon: LayoutDashboard },
  { to: '/verified', label: 'AA ledger', icon: FileCheck2 },
  { to: '/settings', label: 'Settings', icon: Settings2 },
  { to: '/profile', label: 'My profile', icon: UserRound },
  { to: '/support', label: 'Support desk', icon: CircleHelp },
];

const routeNames = {
  '/dashboard': 'Underwriting overview', '/verified': 'Recently verified', '/settings': 'Platform settings',
  '/profile': 'Verified profile', '/support': 'Contact & grievance desk',
};

export default function AppShell() {
  const { session, setSession, preferences, updatePreference } = useApp();
  const location = useLocation();
  const navigate = useNavigate();
  const pageName = routeNames[location.pathname] || 'FairCredit AA';
  const roleLabel = session?.role === 'NBFC Lender' ? 'Lender' : session?.role === 'MSME' ? 'MSME owner' : 'Gig worker';

  function signOut() {
    setSession(null);
    navigate('/login', { replace: true });
  }

  return <div className="min-h-screen bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
    <aside className="fixed inset-y-0 left-0 z-30 hidden w-[250px] flex-col border-r border-slate-200 bg-white px-4 py-5 dark:border-slate-800 dark:bg-slate-900 lg:flex">
      <div className="px-2"><Brand /></div>
      <div className="mt-7 rounded-2xl border border-indigo-100 bg-indigo-50/70 p-3.5 dark:border-indigo-900/80 dark:bg-indigo-950/45">
        <div className="flex items-center gap-2"><span className="flex h-7 w-7 items-center justify-center rounded-lg bg-white text-indigo-600 dark:bg-slate-900"><Activity size={15} /></span><span className="text-[10px] font-bold uppercase tracking-[0.14em] text-indigo-800 dark:text-indigo-200">Consent workspace</span></div>
        <p className="mt-2.5 text-xs leading-5 text-indigo-900 dark:text-indigo-100">Your data, your choice. This preview uses illustrative records.</p>
      </div>
      <nav aria-label="Main navigation" className="mt-7 flex flex-1 flex-col gap-1">
        <p className="mb-2 px-3 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-400">Workspace</p>
        {navItems.map(({ to, label, icon: Icon }) => <NavLink key={to} to={to} className={({ isActive }) => `group flex items-center gap-3 rounded-xl px-3 py-2.5 text-[13px] font-semibold transition-colors ${isActive ? 'bg-indigo-50 text-indigo-700 dark:bg-indigo-950/70 dark:text-indigo-200' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-950 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white'}`}>
          {({ isActive }) => <><Icon size={17} className={isActive ? 'text-indigo-600 dark:text-indigo-300' : 'text-slate-400 group-hover:text-slate-600 dark:group-hover:text-slate-200'} aria-hidden="true" /><span>{label}</span>{to === '/verified' && <span className="ml-auto h-1.5 w-1.5 rounded-full bg-emerald-500" />}</>}
        </NavLink>)}
      </nav>
      <a href="/support" className="mb-3 flex items-center justify-between rounded-xl border border-slate-200 px-3 py-3 text-xs font-semibold text-slate-600 hover:border-indigo-200 hover:text-indigo-700 dark:border-slate-700 dark:text-slate-300 dark:hover:border-indigo-700 dark:hover:text-indigo-200"><span className="flex items-center gap-2"><CircleHelp size={15} /> Need a hand?</span><ArrowUpRight size={14} /></a>
      <button onClick={signOut} className="flex items-center gap-3 rounded-xl px-3 py-2.5 text-left text-xs font-semibold text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white"><LogOut size={16} aria-hidden="true" /> Sign out</button>
    </aside>

    <div className="lg:pl-[250px]">
      <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/90 backdrop-blur-xl dark:border-slate-800 dark:bg-slate-900/90">
        <div className="flex h-[68px] items-center justify-between gap-3 px-4 sm:px-6 xl:px-8">
          <div className="flex min-w-0 items-center gap-3">
            <div className="lg:hidden"><Brand compact /></div>
            <div className="hidden min-w-0 lg:block"><p className="truncate text-[11px] font-medium text-slate-500 dark:text-slate-400">Workspace <span className="px-1.5 text-slate-300">/</span><span className="text-slate-800 dark:text-slate-100">{pageName}</span></p><p className="mt-1 text-[10px] font-medium text-slate-400">Tuesday, 17 November 2026 <span className="mx-1">·</span> Demo environment</p></div>
          </div>
          <div className="flex shrink-0 items-center gap-2 sm:gap-3">
            <Badge tone="emerald" className="hidden sm:inline-flex"><span className="h-1.5 w-1.5 rounded-full bg-emerald-500" /> AA session active</Badge>
            <button type="button" aria-label={preferences.theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'} onClick={() => updatePreference('theme', preferences.theme === 'dark' ? 'light' : 'dark')} className="flex h-9 w-9 items-center justify-center rounded-xl border border-slate-200 text-slate-500 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800">{preferences.theme === 'dark' ? <Sun size={17} /> : <Moon size={17} />}</button>
            <button type="button" onClick={() => navigate('/profile')} className="flex items-center gap-2 rounded-full p-1 pr-2.5 hover:bg-slate-50 dark:hover:bg-slate-800" aria-label="Open verified profile">
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-linear-to-br from-indigo-600 to-violet-500 text-[11px] font-bold text-white">{session?.name?.split(' ').map((part) => part[0]).slice(0, 2).join('') || 'RK'}</span>
              <span className="hidden text-left sm:block"><span className="block max-w-[120px] truncate text-[11px] font-bold text-slate-800 dark:text-slate-100">{session?.name || 'Ramesh Kumar'}</span><span className="block text-[10px] text-slate-500 dark:text-slate-400">{roleLabel}</span></span>
            </button>
          </div>
        </div>
        <nav aria-label="Mobile navigation" className="scrollbar-subtle flex gap-1 overflow-x-auto border-t border-slate-100 px-3 py-2 dark:border-slate-800 lg:hidden">
          {navItems.map(({ to, label, icon: Icon }) => <NavLink key={to} to={to} className={({ isActive }) => `flex shrink-0 items-center gap-1.5 rounded-lg px-2.5 py-2 text-[11px] font-semibold ${isActive ? 'bg-indigo-50 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-200' : 'text-slate-500 dark:text-slate-400'}`}><Icon size={14} aria-hidden="true" />{label}</NavLink>)}
          <button onClick={signOut} className="flex shrink-0 items-center gap-1.5 rounded-lg px-2.5 py-2 text-[11px] font-semibold text-slate-500"><LogOut size={14} aria-hidden="true" /> Sign out</button>
        </nav>
      </header>
      <main className="mx-auto w-full max-w-[1600px] px-4 py-6 sm:px-6 lg:px-8 xl:py-8"><Outlet /></main>
      <footer className="px-4 pb-6 text-center text-[10px] leading-5 text-slate-400 sm:px-6 lg:px-8">FairCredit AA demo · Consent-first credit coaching prototype · Not a credit offer or RBI service</footer>
    </div>
  </div>;
}
