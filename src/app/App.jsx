import { Navigate, Outlet, Route, Routes, useLocation } from 'react-router-dom';
import { useEffect } from 'react';
import AppShell from '../components/AppShell.jsx';
import { LiveDataNotice, PageHeading } from '../components/Primitives.jsx';
import { useApp } from './AppContext.jsx';
import LoginPage from '../features/auth/LoginPage.jsx';
import DashboardPage from '../features/dashboard/DashboardPage.jsx';
import RecentlyVerifiedPage from '../features/ledger/RecentlyVerifiedPage.jsx';
import SettingsPage from '../features/settings/SettingsPage.jsx';
import ProfilePage from '../features/profile/ProfilePage.jsx';
import SupportContactPage from '../features/support/SupportContactPage.jsx';

const TITLES = {
  '/login': 'Sign in | FairCredit AA', '/dashboard': 'Underwriting dashboard | FairCredit AA',
  '/verified': 'Verified accounts | FairCredit AA', '/settings': 'Settings | FairCredit AA',
  '/profile': 'Verified profile | FairCredit AA', '/support': 'Contact and grievance desk | FairCredit AA',
};

function RouteTitle() {
  const location = useLocation();
  useEffect(() => { document.title = TITLES[location.pathname] || 'FairCredit AA'; }, [location.pathname]);
  return null;
}

function HomeRedirect() {
  const { session } = useApp();
  return <Navigate replace to={session ? '/dashboard' : '/login'} />;
}

function ProtectedLayout() {
  const { session } = useApp();
  const location = useLocation();
  if (!session) return <Navigate to="/login" replace state={{ from: location }} />;
  return <AppShell><Outlet /></AppShell>;
}

function NotFoundPage() {
  return <div className="mx-auto max-w-xl py-16"><PageHeading eyebrow="404 · Not found" title="This page isn’t in your workspace" description="Try one of the navigation links to return to your FairCredit demo." /><LiveDataNotice /></div>;
}

export default function App() {
  return <>
    <RouteTitle />
    <Routes>
      <Route path="/" element={<HomeRedirect />} />
      <Route path="/login" element={<LoginPage />} />
      <Route element={<ProtectedLayout />}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/verified" element={<RecentlyVerifiedPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/support" element={<SupportContactPage />} />
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  </>;
}
