import { useState } from 'react';
import { ArrowDownRight, ArrowRight, ArrowUpRight, BadgeCheck, CloudRain, FileCheck2, HeartHandshake, Info, ShieldCheck, Sparkles, Umbrella, WalletCards } from 'lucide-react';
import { Badge, Button, Card, LiveDataNotice, PageHeading } from '../../components/Primitives.jsx';
import { useApp } from '../../app/AppContext.jsx';
import { formatINR } from '../../services/mockData.js';
import CashFlowChart from './CashFlowChart.jsx';
import CounterfactualSimulator, { baselineInputs, calculateProjection } from './CounterfactualSimulator.jsx';
import ConsentHandleModal from './ConsentHandleModal.jsx';
import LenderOverview from './LenderOverview.jsx';

function ScoreCard({ score, delta, limit, segment, onConnect }) {
  const progress = (score - 300) / 600;
  const angle = Math.round(progress * 360);
  return <Card className="overflow-hidden border-indigo-100 dark:border-indigo-900">
    <div className="bg-linear-to-br from-indigo-700 via-indigo-700 to-violet-800 p-5 text-white sm:p-6">
      <div className="flex flex-wrap items-start justify-between gap-3"><div><p className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.16em] text-indigo-200"><Sparkles size={13} /> FairCredit alternate-data score</p><div className="mt-2 flex items-baseline gap-2"><span className="text-5xl font-bold tracking-[-0.07em] tabular-nums">{score}</span><span className="text-xs text-indigo-200">/ 900</span></div><p className="mt-1 text-xs text-indigo-100">Prime band <span className="mx-1 text-indigo-300">·</span> 300–900 range <span className="mx-1 text-indigo-300">·</span> sample {segment.toLowerCase()}</p></div><span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-300/20 bg-emerald-300/15 px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.09em] text-emerald-100"><BadgeCheck size={13} /> APPROVE</span></div>
      <div className="mt-5 flex items-center gap-3"><div className="h-2 flex-1 overflow-hidden rounded-full bg-white/15"><div className="h-full rounded-full bg-linear-to-r from-emerald-300 to-emerald-100" style={{ width: `${progress * 100}%` }} /></div><span className="whitespace-nowrap rounded-full bg-white/10 px-2 py-1 text-[10px] font-semibold text-white">{delta >= 0 ? '+' : ''}{delta} pts</span></div>
      <div className="mt-5 grid grid-cols-2 gap-3 border-t border-white/15 pt-4"><div><p className="text-[10px] text-indigo-200">Illustrative safe loan limit</p><p className="mt-1 text-xl font-bold tabular-nums">{formatINR(limit)}</p></div><div className="flex items-center justify-end"><button onClick={onConnect} className="flex items-center gap-2 rounded-xl border border-white/20 bg-white/10 px-3 py-2 text-[11px] font-semibold text-white transition hover:bg-white/15"><ShieldCheck size={14} /> Connect an AA <ArrowRight size={13} /></button></div></div>
    </div>
    <div className="flex items-center justify-between gap-3 bg-white px-5 py-3 dark:bg-slate-900"><div className="flex items-center gap-2 text-[10px] text-slate-500 dark:text-slate-400"><span className="flex h-6 w-6 items-center justify-center rounded-lg bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300"><ShieldCheck size={13} /></span><span>Fairness review · DIR 0.894</span></div><Badge tone="emerald">Sample pass</Badge></div>
  </Card>;
}

function MonsoonNotice({ enabled, segment }) {
  return <div className="flex items-start gap-3 rounded-2xl border border-amber-200 bg-amber-50/80 p-4 dark:border-amber-900/80 dark:bg-amber-950/35"><div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-amber-100 text-amber-700 dark:bg-amber-900/70 dark:text-amber-200"><CloudRain size={18} /></div><div className="min-w-0 flex-1"><div className="flex flex-wrap items-center gap-2"><p className="text-xs font-bold text-amber-950 dark:text-amber-100">{segment === 'MSME Merchant' ? 'Seasonal income smoothing' : 'IMD monsoon income buffer'}</p>{enabled ? <Badge tone="amber">Buffer on</Badge> : <Badge tone="slate">Buffer off</Badge>}</div><p className="mt-1 text-[11px] leading-5 text-amber-900/80 dark:text-amber-200/80">{enabled ? 'Weather-related income dips are considered in this coaching preview so a rainy week does not define your whole story.' : 'Turn on the income-smoothing buffer in settings to include a seasonal coaching view.'} This is not insurance or a loan guarantee.</p></div><Umbrella size={16} className="mt-1 shrink-0 text-amber-600 dark:text-amber-300" /></div>;
}

function RecoveryRoadmap({ nudgesEnabled = true }) {
  return <Card className="p-5 sm:p-6"><div className="flex items-start justify-between gap-3"><div><div className="flex items-center gap-2"><span className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300"><HeartHandshake size={16} /></span><h2 className="text-sm font-bold text-slate-950 dark:text-white">A practical recovery roadmap</h2></div><p className="mt-2 text-xs text-slate-500 dark:text-slate-400">{nudgesEnabled ? 'Small steps. A stronger financial story.' : 'Weekly coaching reminders are paused in settings.'}</p></div><Badge tone={nudgesEnabled ? 'amber' : 'slate'}>{nudgesEnabled ? 'Weekly coaching' : 'Nudges paused'}</Badge></div>
    <div className="mt-5 space-y-0">{[{ n: '01', title: 'Keep your UPI rhythm steady', text: 'Regular business receipts can make income patterns easier to understand.', status: 'In progress', icon: WalletCards }, { n: '02', title: 'Build a small monthly buffer', text: 'Try setting aside 5% in stronger earning weeks to cushion quieter weeks.', status: 'Next step', icon: ArrowUpRight }, { n: '03', title: 'Connect EPFO when you’re ready', text: 'A longer income view may help complete your cash-flow picture.', status: 'Optional', icon: FileCheck2 }].map(({ n, title, text, status, icon: Icon }, index, list) => <div key={n} className="relative flex gap-3 pb-4 last:pb-0"><div className="relative flex flex-col items-center"><span className={`relative z-10 flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-[10px] font-bold ${index === 0 ? 'bg-indigo-600 text-white' : 'border border-slate-200 bg-white text-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300'}`}>{n}</span>{index < list.length - 1 && <span className="absolute top-8 h-[calc(100%-15px)] w-px bg-slate-200 dark:bg-slate-700" />}</div><div className="min-w-0 flex-1 pt-0.5"><div className="flex flex-wrap items-center justify-between gap-2"><p className="text-xs font-bold text-slate-800 dark:text-slate-100">{title}</p><Badge tone={index === 0 ? 'indigo' : 'slate'}>{status}</Badge></div><p className="mt-1 text-[10px] leading-4 text-slate-500 dark:text-slate-400">{text}</p></div><Icon size={15} className="mt-1 shrink-0 text-slate-300 dark:text-slate-600" /></div>)}</div>
    <p className="mt-5 border-t border-slate-100 pt-4 text-[10px] leading-4 text-slate-400 dark:border-slate-800">These are general coaching suggestions, not credit advice or a promise of approval.</p>
  </Card>;
}

export default function DashboardPage() {
  const { settings, notify, session } = useApp();
  const [view, setView] = useState('Applicant View');
  const [segment, setSegment] = useState('Gig Worker');
  const [inputs, setInputs] = useState(() => baselineInputs('Gig Worker'));
  const [showConsent, setShowConsent] = useState(false);
  const [activeHandle, setActiveHandle] = useState('@finvu');
  const [lastSync, setLastSync] = useState('AA sync · Sample data');
  const projection = calculateProjection(segment === 'MSME Merchant' ? segment : 'Gig Worker', inputs);
  const firstName = session?.name?.trim().split(/\s+/)[0] || 'Ramesh';
  const pageTitle = view === 'Applicant View' ? `Good morning, ${firstName}` : 'Lender audit overview';

  function changeSegment(nextSegment) {
    setSegment(nextSegment);
    setInputs(baselineInputs(nextSegment));
  }

  function simulateSync(consent) {
    setActiveHandle(consent.handle);
    setLastSync(`Synced ${consent.sources.length} sample sources · just now`);
    setShowConsent(false);
    notify(`${consent.sources.length} illustrative FIP sources synced from ${consent.handle}. No live consent was requested.`, 'info');
  }

  return <div className="animate-in space-y-5">
    <div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
      {view === 'Applicant View' && <PageHeading eyebrow="Your credit, made clearer" title={pageTitle} description="Explore the story your cash flows tell — and the practical steps that could help next." actions={null} />}
      <div className={`flex flex-wrap items-center gap-2 ${view === 'Applicant View' ? 'xl:mb-6' : ''}`}>
        <div className="flex rounded-xl bg-slate-100 p-1 dark:bg-slate-900" role="group" aria-label="Choose dashboard view"><button onClick={() => setView('Applicant View')} className={`rounded-lg px-3 py-2 text-[11px] font-bold transition ${view === 'Applicant View' ? 'bg-white text-indigo-700 shadow-sm dark:bg-slate-800 dark:text-indigo-200' : 'text-slate-500 dark:text-slate-400'}`}>Applicant view</button><button onClick={() => setView('Lender Audit View')} className={`rounded-lg px-3 py-2 text-[11px] font-bold transition ${view === 'Lender Audit View' ? 'bg-white text-indigo-700 shadow-sm dark:bg-slate-800 dark:text-indigo-200' : 'text-slate-500 dark:text-slate-400'}`}>Lender audit</button></div>
        {view === 'Applicant View' && <label className="sr-only" htmlFor="applicantSegment">Applicant segment</label>}
        {view === 'Applicant View' && <select id="applicantSegment" value={segment} onChange={(event) => changeSegment(event.target.value)} className="h-10 rounded-xl border border-slate-200 bg-white px-3 text-[11px] font-semibold text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"><option>Gig Worker</option><option>MSME Merchant</option></select>}
        <Button size="sm" variant="secondary" onClick={() => setShowConsent(true)}><ShieldCheck size={14} /> Consent handle</Button>
      </div>
    </div>
    {view === 'Lender Audit View' ? <LenderOverview /> : <>
      <LiveDataNotice />
      <MonsoonNotice enabled={settings.monsoonBuffer} segment={segment} />
      <div className="grid gap-5 xl:grid-cols-[0.95fr_1.05fr]">
        <ScoreCard score={projection.score} delta={projection.delta} limit={projection.loan} segment={segment} onConnect={() => setShowConsent(true)} />
        <CashFlowChart segment={segment === 'MSME Merchant' ? 'MSME' : 'Gig Worker'} />
      </div>
      <CounterfactualSimulator segment={segment} inputs={inputs} onChange={setInputs} />
      <div className="grid gap-5 xl:grid-cols-[1.05fr_0.95fr]">
        <RecoveryRoadmap nudgesEnabled={settings.weeklyNudges} />
        <Card className="flex flex-col justify-between overflow-hidden p-5 sm:p-6"><div><div className="flex items-start justify-between gap-3"><div><p className="text-[10px] font-bold uppercase tracking-[0.15em] text-indigo-600 dark:text-indigo-300">Your data, your choice</p><h2 className="mt-2 text-lg font-bold tracking-tight text-slate-950 dark:text-white">Consent keeps you in control.</h2><p className="mt-2 max-w-lg text-xs leading-5 text-slate-500 dark:text-slate-400">See which financial sources are connected in this sample workspace. Choose what to share and for how long in a real AA experience.</p></div><span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300"><ShieldCheck size={20} /></span></div><div className="mt-5 flex flex-wrap gap-2">{['HDFC UPI', 'EPFO', 'GSTN'].map((fip) => <Badge key={fip} tone="slate"><span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />{fip}</Badge>)}</div><p className="mt-4 text-[10px] text-slate-400">{lastSync} <span className="mx-1">·</span> {activeHandle}</p></div><Button variant="subtle" className="mt-6 w-full sm:w-fit" onClick={() => setShowConsent(true)}>Review consent sources <ArrowRight size={14} /></Button></Card>
      </div>
    </>}
    {showConsent && <ConsentHandleModal currentHandle={activeHandle} onClose={() => setShowConsent(false)} onSync={simulateSync} />}
  </div>;
}
