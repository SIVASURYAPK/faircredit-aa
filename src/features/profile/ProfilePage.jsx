import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { BadgeCheck, Check, EyeOff, Fingerprint, KeyRound, LogOut, Mail, MapPin, Phone, ShieldCheck, Smartphone, UserRound, WalletCards } from 'lucide-react';
import { useApp } from '../../app/AppContext.jsx';
import { Badge, Button, Card, Field, LiveDataNotice, PageHeading } from '../../components/Primitives.jsx';

const fips = ['HDFC UPI', 'GSTN', 'EPFO', 'BBPS'];

export default function ProfilePage() {
  const { session, setSession, settings, notify } = useApp();
  const navigate = useNavigate();
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordFeedback, setPasswordFeedback] = useState(null);

  function signOut() {
    setSession(null);
    notify('You have signed out of the demo workspace.', 'info');
    navigate('/login', { replace: true });
  }

  function updatePassword(event) {
    event.preventDefault();
    setPasswordFeedback(null);
    if (currentPassword.length < 6) return setPasswordFeedback({ tone: 'error', text: 'Enter your current demo password (at least 6 characters).' });
    if (newPassword.length < 8) return setPasswordFeedback({ tone: 'error', text: 'Choose a new password with at least 8 characters.' });
    if (newPassword !== confirmPassword) return setPasswordFeedback({ tone: 'error', text: 'The new password and confirmation do not match.' });
    setPasswordFeedback({ tone: 'success', text: 'The demo form passed validation. No real account password was changed.' });
    setCurrentPassword(''); setNewPassword(''); setConfirmPassword('');
    notify('Demo password form validated. No password was changed.', 'info');
  }

  return <div className="animate-in">
    <PageHeading eyebrow="Identity & access" title="Verified identity" description="Review the account details and data protections shown in this illustrative profile." actions={<Button variant="secondary" onClick={signOut}><LogOut size={15} /> Sign out</Button>} />
    <LiveDataNotice className="mb-5" />
    <Card className="mb-5 overflow-hidden"><div className="bg-linear-to-r from-indigo-700 to-violet-700 px-5 py-6 text-white sm:px-7"><div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"><div className="flex items-center gap-4"><span className="flex h-14 w-14 items-center justify-center rounded-2xl border border-white/20 bg-white/10 text-lg font-bold">{session?.name?.split(' ').map((part) => part[0]).slice(0, 2).join('') || 'RK'}</span><div><p className="text-xl font-bold tracking-tight">{session?.name || 'Ramesh Kumar'}</p><p className="mt-1 text-xs text-indigo-100">{session?.role || 'Gig Worker'} · FairCredit demo member</p></div></div><Badge tone="emerald" className="w-fit bg-emerald-300/15 text-emerald-100"><BadgeCheck size={13} /> AA KYC Verified · sample</Badge></div></div><div className="grid gap-3 p-5 sm:grid-cols-3 sm:p-6"><div className="flex items-center gap-3 rounded-xl bg-slate-50 p-3 dark:bg-slate-800/60"><Mail size={15} className="text-slate-400" /><div className="min-w-0"><p className="text-[10px] text-slate-400">Email address</p><p className="truncate text-xs font-semibold text-slate-800 dark:text-slate-100">{session?.email || 'ramesh.kumar@example.in'}</p></div></div><div className="flex items-center gap-3 rounded-xl bg-slate-50 p-3 dark:bg-slate-800/60"><Phone size={15} className="text-slate-400" /><div><p className="text-[10px] text-slate-400">Mobile number</p><p className="text-xs font-semibold text-slate-800 dark:text-slate-100">+91 ••••• •• 4821</p></div></div><div className="flex items-center gap-3 rounded-xl bg-slate-50 p-3 dark:bg-slate-800/60"><MapPin size={15} className="text-slate-400" /><div><p className="text-[10px] text-slate-400">Profile region</p><p className="text-xs font-semibold text-slate-800 dark:text-slate-100">Chennai, Tamil Nadu</p></div></div></div></Card>

    <div className="grid gap-5 xl:grid-cols-[1.05fr_0.95fr]">
      <div className="space-y-5">
        <Card className="p-5 sm:p-6"><div className="flex items-start justify-between gap-3"><div><div className="flex items-center gap-2"><span className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600 dark:bg-indigo-950 dark:text-indigo-300"><Fingerprint size={16} /></span><h2 className="text-sm font-bold text-slate-950 dark:text-white">Verified identity & AA handle</h2></div><p className="mt-2 text-xs text-slate-500 dark:text-slate-400">Account Aggregator details shown for the demo profile.</p></div><Badge tone="emerald"><ShieldCheck size={12} /> Consent-first</Badge></div>
          <dl className="mt-5 divide-y divide-slate-100 rounded-xl border border-slate-200 dark:divide-slate-800 dark:border-slate-700"><div className="flex items-center justify-between gap-3 px-3.5 py-3"><dt className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400"><AtSymbol /> AA handle</dt><dd className="text-xs font-bold text-slate-800 dark:text-slate-100">ramesh.kumar@finvu</dd></div><div className="flex items-center justify-between gap-3 px-3.5 py-3"><dt className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400"><Smartphone size={14} /> Mobile</dt><dd className="text-xs font-semibold text-slate-800 dark:text-slate-100">+91 ••••• •• 4821</dd></div><div className="flex items-center justify-between gap-3 px-3.5 py-3"><dt className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400"><ShieldCheck size={14} /> Two-step verification</dt><dd><Badge tone={settings.require2FA ? 'emerald' : 'amber'}>{settings.require2FA ? 'On · demo' : 'Off'}</Badge></dd></div></dl>
          <div className="mt-4"><p className="mb-2 text-[10px] font-bold uppercase tracking-[0.12em] text-slate-400">Connected sample FIPs</p><div className="flex flex-wrap gap-2">{fips.map((fip) => <Badge key={fip} tone="slate"><span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />{fip}</Badge>)}</div></div>
        </Card>
        <Card className="p-5 sm:p-6"><div className="flex items-center gap-2"><span className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300"><EyeOff size={16} /></span><div><h2 className="text-sm font-bold text-slate-950 dark:text-white">Proxy-scrubbing confirmation</h2><p className="mt-1 text-[11px] text-slate-500 dark:text-slate-400">Sensitive identity proxies are excluded in this sample view.</p></div></div><div className="mt-4 grid grid-cols-3 gap-2">{['PIN', 'Caste', 'Gender'].map((field) => <div key={field} className="flex items-center justify-center gap-1.5 rounded-xl border border-emerald-100 bg-emerald-50/70 px-2 py-2.5 text-xs font-semibold text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-200"><Check size={13} /> {field} redacted</div>)}</div><p className="mt-3 text-[10px] leading-4 text-slate-400">This is a product demonstration, not an audited proof of data processing.</p></Card>
      </div>

      <Card className="h-fit p-5 sm:p-6"><div className="flex items-start gap-3"><span className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600 dark:bg-indigo-950 dark:text-indigo-300"><KeyRound size={17} /></span><div><h2 className="text-sm font-bold text-slate-950 dark:text-white">Update account password</h2><p className="mt-1 text-xs leading-5 text-slate-500 dark:text-slate-400">Try the password validation flow. No account credential is stored or changed.</p></div></div>
        <form onSubmit={updatePassword} className="mt-5 space-y-4"><Field label="Current password" name="currentPassword" type="password" autoComplete="current-password" value={currentPassword} onChange={(event) => setCurrentPassword(event.target.value)} placeholder="At least 6 characters" required /><Field label="New password" name="newPassword" type="password" autoComplete="new-password" value={newPassword} onChange={(event) => setNewPassword(event.target.value)} placeholder="At least 8 characters" required minLength={8} /><Field label="Confirm new password" name="confirmPassword" type="password" autoComplete="new-password" value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} placeholder="Re-enter new password" required minLength={8} />
          {passwordFeedback && <div role={passwordFeedback.tone === 'error' ? 'alert' : 'status'} className={`rounded-xl border px-3 py-2.5 text-xs leading-5 ${passwordFeedback.tone === 'error' ? 'border-rose-200 bg-rose-50 text-rose-800 dark:border-rose-900 dark:bg-rose-950/50 dark:text-rose-200' : 'border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950/50 dark:text-emerald-200'}`}>{passwordFeedback.text}</div>}
          <Button type="submit" className="w-full"><KeyRound size={14} /> Validate password form</Button>
        </form>
      </Card>
    </div>
  </div>;
}

function AtSymbol() { return <span aria-hidden="true" className="inline-flex h-3.5 w-3.5 items-center justify-center rounded-full border border-current text-[9px] font-bold">@</span>; }
