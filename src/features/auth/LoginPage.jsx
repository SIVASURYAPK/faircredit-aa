import { useRef, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { ArrowDownRight, ArrowLeft, ArrowRight, BadgeCheck, Building2, Check, ChevronDown, CircleHelp, Fingerprint, Globe2, Landmark, LockKeyhole, Mail, ShieldCheck, Sparkles, TrendingUp, UserRound, WalletCards, X } from 'lucide-react';
import { useApp } from '../../app/AppContext.jsx';
import { Brand } from '../../components/Brand.jsx';
import { Badge, Button, Field, LiveDataNotice, SelectField } from '../../components/Primitives.jsx';
import { makeTicket } from '../../services/storage.js';

const loginText = {
  English: { eyebrow: 'A fairer way forward', title: 'From Everyday Cash Flows to Fair, Auditable Credit', subtitle: 'A fuller view of your financial story — with your consent at every step.', signin: 'Sign in to your account', create: 'Create your account' },
  हिंदी: { eyebrow: 'न्यायपूर्ण वित्त की ओर', title: 'रोज़मर्रा के नक़दी प्रवाह से निष्पक्ष, पारदर्शी ऋण तक।', subtitle: 'आपकी वित्तीय कहानी का बेहतर चित्र — हर कदम पर आपकी सहमति के साथ।', signin: 'अपने खाते में साइन इन करें', create: 'अपना खाता बनाएँ' },
  தமிழ்: { eyebrow: 'நியாயமான கடன் நோக்கி', title: 'அன்றாட பணப்புழக்கத்திலிருந்து நியாயமான, தெளிவான கடன் வரை.', subtitle: 'உங்கள் ஒப்புதலுடன், உங்கள் நிதி நிலையின் முழுமையான பார்வை.', signin: 'உங்கள் கணக்கில் உள்நுழையவும்', create: 'கணக்கை உருவாக்கவும்' },
};

export default function LoginPage() {
  const { preferences, updatePreference, settings, setSession, notify, tickets, setTickets } = useApp();
  const navigate = useNavigate();
  const location = useLocation();
  const [panel, setPanel] = useState('auth');
  const [mode, setMode] = useState('signin');
  const [step, setStep] = useState('credentials');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('Gig Worker');
  const [remember, setRemember] = useState(true);
  const [forgotBanner, setForgotBanner] = useState(false);
  const [error, setError] = useState('');
  const [otp, setOtp] = useState(Array(6).fill(''));
  const otpRefs = useRef([]);
  const [supportSubject, setSupportSubject] = useState('');
  const [supportMessage, setSupportMessage] = useState('');
  const [supportSent, setSupportSent] = useState(false);
  const copy = loginText[preferences.language] || loginText.English;

  function completeLogin(user) {
    setSession({ ...user, createdAt: new Date().toISOString() });
    notify('Demo session started. Your workspace is ready.');
    navigate(location.state?.from?.pathname || '/dashboard', { replace: true });
  }

  function getDemoUser() {
    const accountName = (email.split('@')[0] || 'Ramesh Kumar').replace(/[._-]/g, ' ');
    return {
      email: email.trim(),
      name: (name.trim() || accountName).replace(/\b\w/g, (letter) => letter.toUpperCase()),
      role,
      rememberMe: mode === 'create' || remember,
    };
  }

  function submitCredentials(event) {
    event.preventDefault();
    setError('');
    if (!email.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
      setError('Enter a valid email address to continue.');
      return;
    }
    if (password.length < 6) {
      setError('Use at least 6 characters for this demo password.');
      return;
    }
    const user = getDemoUser();
    if (settings.require2FA) {
      setStep('otp');
      setOtp(Array(6).fill(''));
      window.setTimeout(() => otpRefs.current[0]?.focus(), 50);
    } else completeLogin(user);
  }

  function confirmOtp(code = otp.join('')) {
    if (code !== '123456') {
      setError('That code did not match. For this demo, enter 123456.');
      setOtp(Array(6).fill(''));
      otpRefs.current[0]?.focus();
      return;
    }
    completeLogin(getDemoUser());
  }

  function updateOtp(index, value) {
    const digits = value.replace(/\D/g, '').slice(0, 6 - index);
    const next = [...otp];
    if (digits.length > 1) {
      [...digits].forEach((digit, offset) => { next[index + offset] = digit; });
      setOtp(next);
      setError('');
      if (next.every(Boolean)) confirmOtp(next.join(''));
      else otpRefs.current[Math.min(index + digits.length, 5)]?.focus();
      return;
    }
    const digit = digits.slice(-1);
    next[index] = digit;
    setOtp(next);
    setError('');
    if (digit && index < 5) otpRefs.current[index + 1]?.focus();
    if (digit && index === 5) confirmOtp(next.join(''));
  }

  function handleOtpKey(event, index) {
    if (event.key === 'Backspace' && !otp[index] && index > 0) otpRefs.current[index - 1]?.focus();
    if (event.key === 'ArrowLeft' && index > 0) otpRefs.current[index - 1]?.focus();
    if (event.key === 'ArrowRight' && index < 5) otpRefs.current[index + 1]?.focus();
  }

  function submitSupport(event) {
    event.preventDefault();
    if (supportMessage.trim().length < 8) {
      notify('Add a little more detail so the support team can help.', 'error');
      return;
    }
    const ticket = makeTicket(supportSubject, supportMessage);
    setTickets([ticket, ...tickets]);
    setSupportSent(true);
    setSupportSubject('');
    setSupportMessage('');
    notify(`Support request ${ticket.id} added to this demo session.`);
  }

  return <div className="min-h-screen bg-white text-slate-900 dark:bg-slate-950 dark:text-white lg:grid lg:grid-cols-[1.02fr_0.98fr]">
    <section className="relative hidden min-h-screen overflow-hidden bg-linear-to-br from-indigo-800 via-slate-950 to-slate-950 px-10 py-9 text-white lg:flex lg:flex-col xl:px-16">
      <div className="pointer-events-none absolute inset-0 opacity-25" style={{ backgroundImage: 'radial-gradient(#a5b4fc 0.8px, transparent 0.8px)', backgroundSize: '20px 20px', maskImage: 'linear-gradient(130deg, black, transparent 74%)' }} />
      <div className="pointer-events-none absolute -right-40 top-24 h-[520px] w-[520px] rounded-full border border-indigo-300/15" />
      <div className="pointer-events-none absolute -right-20 top-44 h-[350px] w-[350px] rounded-full border border-indigo-300/15" />
      <div className="relative z-10"><Brand inverse /></div>
      <div className="relative z-10 my-auto max-w-[600px] py-16">
        <div className="mb-5 flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.2em] text-indigo-200"><span className="h-px w-8 bg-emerald-300" /> Fair credit starts with your story</div>
        <h1 className="max-w-[580px] text-[38px] font-semibold leading-[1.08] tracking-[-0.04em] xl:text-[52px]">{copy.title}</h1>
        <p className="mt-5 max-w-[440px] text-[15px] leading-7 text-slate-300">{copy.subtitle}</p>

        <div className="relative mt-9 max-w-[440px] rounded-[24px] border border-white/15 bg-white/10 p-5 shadow-2xl shadow-indigo-950/40 backdrop-blur-xl">
          <div className="absolute -right-3 -top-3 flex h-9 w-9 items-center justify-center rounded-xl border border-white/20 bg-emerald-400 text-emerald-950 shadow-lg"><BadgeCheck size={18} /></div>
          <div className="flex items-start justify-between gap-4">
            <div><p className="text-[10px] font-bold uppercase tracking-[0.16em] text-indigo-200">Alternate-data score</p><div className="mt-2 flex items-end gap-2"><span className="text-[42px] font-semibold leading-none tracking-[-0.06em] tabular-nums">742</span><span className="pb-1 text-sm text-slate-400">/ 900</span></div><p className="mt-2 text-xs font-medium text-emerald-300">Prime band · Demo only</p></div>
            <div className="rounded-2xl border border-white/10 bg-slate-950/25 px-3 py-2 text-right"><Badge tone="emerald" className="bg-emerald-300/15 text-emerald-200"><ShieldCheck size={12} /> AA Verified</Badge><p className="mt-2 text-[10px] text-slate-400">Consent-led data</p></div>
          </div>
          <div className="mt-5 space-y-3 border-t border-white/10 pt-4">
            <div className="flex items-center justify-between gap-3"><span className="flex items-center gap-2 text-xs text-slate-300"><WalletCards size={14} /> UPI Consistency</span><span className="text-xs font-semibold text-emerald-300">+48 SHAP pts</span></div>
            <div className="flex items-center justify-between gap-3"><span className="flex items-center gap-2 text-xs text-slate-300"><Fingerprint size={14} /> Fairlearn DIR</span><span className="text-xs font-semibold text-white">0.89 <span className="text-emerald-300">Pass</span></span></div>
          </div>
        </div>

        <div className="mt-9 grid max-w-[540px] grid-cols-3 gap-3">
          {[{ icon: LockKeyhole, title: 'Consent-First AA', detail: 'You stay in control' }, { icon: Landmark, title: 'Fairlearn Audited', detail: 'Parity made visible' }, { icon: Sparkles, title: 'SHAP Coaching', detail: 'Know what can help' }].map(({ icon: Icon, title, detail }) => <div key={title} className="border-l border-white/15 pl-3"><Icon size={15} className="mb-2 text-indigo-200" /><p className="text-[11px] font-semibold text-white">{title}</p><p className="mt-1 text-[10px] leading-4 text-slate-400">{detail}</p></div>)}
        </div>
      </div>
      <div className="relative z-10 flex items-center justify-between gap-4 border-t border-white/10 pt-4 text-[10px] text-slate-400"><span>Built around consent. Designed for fairness.</span><span className="flex items-center gap-1.5"><span className="h-1.5 w-1.5 rounded-full bg-emerald-400" /> India-first · DEPA aligned</span></div>
    </section>

    <section className="relative flex min-h-screen flex-col bg-white dark:bg-slate-950">
      <header className="flex items-center justify-between gap-3 px-5 py-5 sm:px-8 lg:px-10">
        <div className="lg:hidden"><Brand compact /></div>
        <div className="hidden lg:block"><Badge tone="indigo"><Globe2 size={12} /> Demo workspace</Badge></div>
        <div className="ml-auto flex items-center gap-2">
          <label className="sr-only" htmlFor="login-language">Language</label>
          <div className="relative flex items-center">
            <Globe2 size={14} className="pointer-events-none absolute left-2.5 text-slate-400" aria-hidden="true" />
            <select id="login-language" value={preferences.language} onChange={(event) => updatePreference('language', event.target.value)} className="h-9 appearance-none rounded-xl border border-slate-200 bg-white pl-8 pr-7 text-[11px] font-semibold text-slate-600 outline-none focus:border-indigo-400 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200">
              <option>English</option><option>हिंदी</option><option>தமிழ்</option>
            </select><ChevronDown size={13} className="pointer-events-none absolute right-2 text-slate-400" aria-hidden="true" />
          </div>
          <button onClick={() => { setPanel(panel === 'support' ? 'auth' : 'support'); setSupportSent(false); }} className={`flex h-9 items-center gap-1.5 rounded-xl px-3 text-xs font-semibold transition-colors ${panel === 'support' ? 'bg-indigo-50 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-200' : 'text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800'}`}><CircleHelp size={15} aria-hidden="true" /> {panel === 'support' ? 'Sign in' : 'Support'}</button>
        </div>
      </header>

      <div className="flex flex-1 items-start justify-center px-5 pb-10 pt-6 sm:px-8 sm:pt-8 lg:items-center lg:px-10 lg:py-10">
        <div className="w-full max-w-[430px] animate-in">
          {panel === 'support' ? <>
            <button onClick={() => setPanel('auth')} className="mb-6 flex items-center gap-2 text-xs font-semibold text-slate-500 hover:text-indigo-700 dark:text-slate-400 dark:hover:text-indigo-300"><ArrowLeft size={14} /> Back to secure sign in</button>
            <div className="mb-7"><Badge tone="amber"><CircleHelp size={12} /> Pre-login support</Badge><h2 className="mt-3 text-2xl font-bold tracking-tight text-slate-950 dark:text-white">How can we help?</h2><p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-400">Questions about Account Aggregators, consent handles, or getting started? We’ll point you in the right direction.</p></div>
            <div className="mb-6 space-y-3">
              {[['What is an AA handle?', 'It identifies your Account Aggregator. In a live flow, you choose an AA to request consent from your financial institution.'], ['Can FairCredit see my PIN or password?', 'No. A real AA flow shares only consented financial information; this prototype uses sample data and does not connect to accounts.'], ['Can I revoke consent?', 'In a live AA experience, consent can be reviewed and revoked with your chosen Account Aggregator. This mock flow does not create real consent.']].map(([question, answer]) => <details key={question} className="group rounded-xl border border-slate-200 bg-white px-4 py-3 dark:border-slate-800 dark:bg-slate-900"><summary className="flex cursor-pointer list-none items-center justify-between gap-3 text-xs font-semibold text-slate-800 dark:text-slate-100">{question}<ChevronDown size={14} className="shrink-0 transition-transform group-open:rotate-180" /></summary><p className="mt-2 text-xs leading-5 text-slate-600 dark:text-slate-400">{answer}</p></details>)}
            </div>
            <form onSubmit={submitSupport} className="space-y-4 rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900/60">
              {supportSent && <div role="status" className="flex items-center gap-2 rounded-xl bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200"><Check size={14} /> Your request was added to this demo session.</div>}
              <Field label="Subject (optional)" name="preSupportSubject" placeholder="e.g. AA handle setup" value={supportSubject} onChange={(event) => setSupportSubject(event.target.value)} />
              <label htmlFor="preSupportMessage" className="block space-y-1.5"><span className="text-xs font-semibold text-slate-700 dark:text-slate-300">Message</span><textarea id="preSupportMessage" rows={3} value={supportMessage} onChange={(event) => setSupportMessage(event.target.value)} required placeholder="Tell us what you need help with" className="w-full resize-y rounded-xl border border-slate-200 bg-white px-3.5 py-3 text-sm text-slate-900 outline-none placeholder:text-slate-400 focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:placeholder:text-slate-500" /></label>
              <Button type="submit" className="w-full">Submit quick ticket <ArrowRight size={15} /></Button>
            </form>
          </> : step === 'otp' ? <>
            <button onClick={() => { setStep('credentials'); setError(''); }} className="mb-7 flex items-center gap-2 text-xs font-semibold text-slate-500 hover:text-indigo-700 dark:text-slate-400 dark:hover:text-indigo-300"><ArrowLeft size={14} /> Back to sign in</button>
            <div className="mb-7 flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600 dark:bg-indigo-950 dark:text-indigo-200"><ShieldCheck size={24} /></div>
            <p className="text-[11px] font-bold uppercase tracking-[0.17em] text-indigo-600 dark:text-indigo-300">Two-step verification</p>
            <h2 className="mt-2 text-2xl font-bold tracking-tight text-slate-950 dark:text-white">Check your inbox</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-400">Enter the 6-digit demo verification code sent to <span className="font-semibold text-slate-800 dark:text-slate-200">{email || 'your email'}</span>.</p>
            <div className="mt-7 flex justify-between gap-2" role="group" aria-label="Six-digit verification code">
              {otp.map((digit, index) => <input key={index} ref={(element) => { otpRefs.current[index] = element; }} type="text" inputMode="numeric" autoComplete={index === 0 ? 'one-time-code' : 'off'} aria-label={`Verification digit ${index + 1}`} value={digit} maxLength={6} onChange={(event) => updateOtp(index, event.target.value)} onKeyDown={(event) => handleOtpKey(event, index)} className="h-12 w-12 rounded-xl border border-slate-200 bg-white text-center text-lg font-bold text-slate-900 outline-none transition focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10 dark:border-slate-700 dark:bg-slate-900 dark:text-white sm:h-14 sm:w-14" />)}
            </div>
            {error && <p role="alert" className="mt-3 text-xs font-medium text-rose-600 dark:text-rose-300">{error}</p>}
            <p className="mt-4 rounded-xl bg-indigo-50 px-3 py-2 text-xs leading-5 text-indigo-800 dark:bg-indigo-950/60 dark:text-indigo-200"><strong>Demo code:</strong> 123456 <span className="font-normal">· No real message is sent.</span></p>
            <Button type="button" className="mt-6 w-full" onClick={() => confirmOtp()}>Verify and continue <ArrowRight size={15} /></Button>
            <button className="mt-4 w-full text-center text-xs font-semibold text-indigo-700 hover:text-indigo-900 dark:text-indigo-300" onClick={() => { setOtp(Array(6).fill('')); otpRefs.current[0]?.focus(); notify('A fresh demo code is ready: 123456.', 'info'); }}>Resend demo code</button>
          </> : <>
            <div className="mb-7"><Badge tone="emerald"><span className="h-1.5 w-1.5 rounded-full bg-emerald-500" /> Secure demo sign in</Badge><h2 className="mt-3 text-2xl font-bold tracking-tight text-slate-950 dark:text-white">{mode === 'signin' ? copy.signin : copy.create}</h2><p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-400">{mode === 'signin' ? 'See your full financial picture and what could help next.' : 'Create a sample profile to explore your consent-first credit workspace.'}</p></div>
            <div className="mb-5 grid grid-cols-2 rounded-xl bg-slate-100 p-1 dark:bg-slate-900"><button onClick={() => { setMode('signin'); setError(''); }} className={`rounded-lg py-2.5 text-xs font-bold transition ${mode === 'signin' ? 'bg-white text-indigo-700 shadow-sm dark:bg-slate-800 dark:text-indigo-200' : 'text-slate-500 dark:text-slate-400'}`}>Sign in</button><button onClick={() => { setMode('create'); setError(''); }} className={`rounded-lg py-2.5 text-xs font-bold transition ${mode === 'create' ? 'bg-white text-indigo-700 shadow-sm dark:bg-slate-800 dark:text-indigo-200' : 'text-slate-500 dark:text-slate-400'}`}>Create account</button></div>
            {forgotBanner && <div role="status" className="mb-4 flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs leading-5 text-amber-900 dark:border-amber-900 dark:bg-amber-950/50 dark:text-amber-100"><Mail size={15} className="mt-0.5 shrink-0" /> Password reset links are not sent in this frontend demo. Contact care@faircreditaa.in for assistance.<button type="button" onClick={() => setForgotBanner(false)} aria-label="Dismiss password reset banner" className="ml-auto"><X size={14} /></button></div>}
            <form onSubmit={submitCredentials} className="space-y-4">
              {mode === 'create' && <><Field label="Full / business name" name="fullName" autoComplete="name" placeholder="e.g. Ramesh Kumar" value={name} onChange={(event) => setName(event.target.value)} required /><SelectField label="Your role" name="role" value={role} onChange={(event) => setRole(event.target.value)}><option>Gig Worker</option><option>MSME</option><option>NBFC Lender</option></SelectField></>}
              <Field label="Email address" name="email" type="email" autoComplete="email" placeholder="you@example.com" value={email} onChange={(event) => setEmail(event.target.value)} required />
              <Field label="Password" name="password" type="password" autoComplete={mode === 'signin' ? 'current-password' : 'new-password'} placeholder="At least 6 characters" value={password} onChange={(event) => setPassword(event.target.value)} required minLength={6} />
              {mode === 'signin' && <div className="flex items-center justify-between gap-3"><label className="flex cursor-pointer items-center gap-2 text-xs font-medium text-slate-600 dark:text-slate-400"><input type="checkbox" checked={remember} onChange={(event) => setRemember(event.target.checked)} className="h-4 w-4 rounded border-slate-300 accent-indigo-600" /> Remember me</label><button type="button" onClick={() => setForgotBanner(true)} className="text-xs font-semibold text-indigo-700 hover:underline dark:text-indigo-300">Forgot password?</button></div>}
              {error && <p role="alert" className="text-xs font-semibold text-rose-600 dark:text-rose-300">{error}</p>}
              <Button type="submit" className="w-full">{mode === 'signin' ? 'Continue securely' : 'Create demo account'} <ArrowRight size={15} /></Button>
            </form>
            <div className="my-5 flex items-center gap-3"><span className="h-px flex-1 bg-slate-200 dark:bg-slate-800" /><span className="text-[10px] font-semibold uppercase tracking-[0.1em] text-slate-400">or continue with</span><span className="h-px flex-1 bg-slate-200 dark:bg-slate-800" /></div>
            <div className="grid grid-cols-2 gap-3"><Button variant="secondary" className="w-full" onClick={() => notify('Google sign-in is a demo-only action. Use the email form to enter the workspace.', 'info')}><span className="text-sm font-bold text-blue-600">G</span> Google</Button><Button variant="secondary" className="w-full" onClick={() => notify('Microsoft sign-in is a demo-only action. Use the email form to enter the workspace.', 'info')}><Building2 size={15} className="text-slate-600 dark:text-slate-300" /> Microsoft</Button></div>
            <div className="mt-6"><LiveDataNotice /></div>
            <p className="mt-5 text-center text-[10px] leading-5 text-slate-400">By continuing, you agree to explore a non-production prototype. No financial account is accessed.</p>
          </>}
        </div>
      </div>
      <div className="px-5 pb-4 text-center text-[10px] text-slate-400 sm:px-8">© 2026 FairCredit AA · <button className="font-semibold hover:text-indigo-600" onClick={() => setPanel('support')}>Help & grievance support</button></div>
    </section>
  </div>;
}
