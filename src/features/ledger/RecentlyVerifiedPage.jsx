import { useMemo, useRef, useState } from 'react';
import { Activity, ArrowDownToLine, BadgeCheck, Check, Clipboard, FileCheck2, Search, ShieldCheck, X } from 'lucide-react';
import { useApp } from '../../app/AppContext.jsx';
import { Badge, Button, Card, IconButton, LiveDataNotice, PageHeading } from '../../components/Primitives.jsx';
import { verifiedAccounts } from '../../services/mockData.js';
import { useDialogFocus } from '../../components/useDialogFocus.js';

const filters = ['All Segments', 'Gig Workers', 'MSMEs'];
const sampleHash = 'a7f93e14c02d6a8b507c1e4835fd2a109be76c43d80a5f2197e4c3b26d1a8f50';

function LedgerStat({ label, value, detail, icon: Icon, tone }) {
  const tones = {
    emerald: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300',
    amber: 'bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300',
    indigo: 'bg-indigo-50 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300',
  };
  return <Card className="flex items-center gap-3 p-4">
    <span className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${tones[tone]}`}><Icon size={17} /></span>
    <div className="min-w-0"><p className="text-[10px] font-semibold text-slate-500 dark:text-slate-400">{label}</p><p className="mt-0.5 text-xl font-bold text-slate-950 dark:text-white tabular-nums">{value}</p><p className="mt-0.5 truncate text-[10px] text-slate-400">{detail}</p></div>
  </Card>;
}

function CertificateDrawer({ applicant, onClose, notify }) {
  const dialogRef = useRef(null);
  const handleDialogKeyDown = useDialogFocus(dialogRef, onClose, '[aria-label="Close certificate drawer"]');
  async function copyHash() {
    try {
      await navigator.clipboard.writeText(sampleHash);
      notify('Illustrative certificate hash copied.');
    } catch {
      notify('Clipboard access is unavailable in this browser.', 'error');
    }
  }

  const details = [
    ['Verification ID', applicant.id], ['Applicant', applicant.name], ['AA handle', applicant.handle],
    ['Consent purpose', 'Credit underwriting & coaching demo'], ['FIP sources', applicant.fips.join(', ')],
    ['Created', '17 Nov 2026 · 10:42 IST'], ['Expires', '16 Feb 2027 · sample 90-day term'],
    ['Model transparency', `Fairlearn DIR ${applicant.dir} · sample pass`],
  ];

  return <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/40 backdrop-blur-[2px]" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
    <aside ref={dialogRef} tabIndex={-1} onKeyDown={handleDialogKeyDown} role="dialog" aria-modal="true" aria-labelledby="certificate-title" className="animate-in flex h-full w-full max-w-[480px] flex-col overflow-y-auto border-l border-slate-200 bg-white shadow-2xl outline-none dark:border-slate-700 dark:bg-slate-900">
      <div className="flex items-start justify-between gap-4 border-b border-slate-100 p-5 dark:border-slate-800 sm:p-6">
        <div><Badge tone="emerald"><ShieldCheck size={12} /> Sample artifact</Badge><h2 id="certificate-title" className="mt-3 text-lg font-bold text-slate-950 dark:text-white">Consent certificate</h2><p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Illustrative consent trace for {applicant.name}</p></div>
        <IconButton label="Close certificate drawer" onClick={onClose}><X size={18} /></IconButton>
      </div>
      <div className="flex-1 space-y-5 p-5 sm:p-6">
        <div className="rounded-2xl border border-emerald-100 bg-emerald-50/70 p-4 dark:border-emerald-900 dark:bg-emerald-950/40"><div className="flex items-center gap-2 text-emerald-800 dark:text-emerald-200"><BadgeCheck size={16} /><span className="text-xs font-bold">Consent metadata available</span></div><p className="mt-2 text-[11px] leading-5 text-emerald-800/80 dark:text-emerald-200/75">This is generated sample content, not a cryptographically signed or legally valid AA consent artifact.</p></div>
        <div><p className="mb-2 text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">SHA-256 digest · demo only</p><div className="rounded-xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-950"><p className="break-all font-mono text-[11px] leading-5 text-slate-700 dark:text-slate-300">{sampleHash}</p><Button variant="secondary" size="sm" className="mt-3" onClick={copyHash}><Clipboard size={13} /> Copy sample hash</Button></div></div>
        <dl className="divide-y divide-slate-100 rounded-xl border border-slate-200 dark:divide-slate-800 dark:border-slate-700">{details.map(([label, value]) => <div key={label} className="grid grid-cols-[130px_1fr] gap-3 px-3 py-2.5"><dt className="text-[10px] font-medium text-slate-500 dark:text-slate-400">{label}</dt><dd className="break-words text-right text-[10px] font-semibold text-slate-800 dark:text-slate-200">{value}</dd></div>)}</dl>
        <div className="rounded-xl border border-dashed border-slate-300 p-4 text-center dark:border-slate-700"><div className="mx-auto flex h-9 w-9 items-center justify-center rounded-full bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-300"><FileCheck2 size={17} /></div><p className="mt-2 text-xs font-semibold text-slate-700 dark:text-slate-200">Certificate preview</p><p className="mt-1 text-[10px] leading-4 text-slate-500 dark:text-slate-400">No private financial account details are shown in this illustrative record.</p></div>
      </div>
      <div className="border-t border-slate-100 p-5 dark:border-slate-800"><Button variant="secondary" className="w-full" onClick={onClose}>Close preview</Button></div>
    </aside>
  </div>;
}

export default function RecentlyVerifiedPage() {
  const { notify } = useApp();
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('All Segments');
  const [selected, setSelected] = useState(null);
  const rows = useMemo(() => verifiedAccounts.filter((row) => {
    const matchesFilter = filter === 'All Segments' || (filter === 'Gig Workers' ? row.segment === 'Gig Worker' : row.segment === 'MSME');
    const query = search.toLowerCase().trim();
    return matchesFilter && (!query || `${row.id} ${row.name} ${row.handle} ${row.fips.join(' ')}`.toLowerCase().includes(query));
  }), [search, filter]);

  return <div className="animate-in">
    <PageHeading eyebrow="Consent ledger" title="Recently verified accounts" description="A clear, searchable trail of sample verifications and their consent context." actions={<Button variant="secondary" onClick={() => notify('The demo ledger is ready. Export is not enabled for sample records.', 'info')}><ArrowDownToLine size={15} /> Export ledger</Button>} />
    <LiveDataNotice className="mb-5" />
    <div className="mb-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      <LedgerStat icon={Activity} label="Verified in the last 24h" value="247" detail="Sample consent-led verifications" tone="emerald" />
      <LedgerStat icon={FileCheck2} label="Active consent records" value="1,420" detail="Across gig and MSME segments" tone="indigo" />
      <LedgerStat icon={BadgeCheck} label="Fairness review" value="0.894" detail="DIR ratio · illustrative pass" tone="emerald" />
      <LedgerStat icon={ShieldCheck} label="FIP connections" value="4" detail="HDFC UPI · GSTN · EPFO · BBPS" tone="amber" />
    </div>
    <Card className="overflow-hidden">
      <div className="border-b border-slate-100 p-4 dark:border-slate-800 sm:p-5">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div className="flex flex-wrap gap-1.5" role="group" aria-label="Filter by applicant segment">{filters.map((item) => <button key={item} onClick={() => setFilter(item)} aria-pressed={filter === item} className={`rounded-lg px-3 py-2 text-[11px] font-semibold transition ${filter === item ? 'bg-indigo-600 text-white shadow-sm' : 'bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700'}`}>{item}</button>)}</div>
          <label className="relative block w-full xl:max-w-[320px]"><span className="sr-only">Search verified accounts</span><Search size={15} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" aria-hidden="true" /><input type="search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search name, ID, handle, FIP…" className="h-10 w-full rounded-xl border border-slate-200 bg-white pl-9 pr-3 text-xs text-slate-900 outline-none placeholder:text-slate-400 focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:placeholder:text-slate-500" /></label>
        </div>
        <p className="mt-3 text-[10px] text-slate-400">Showing {rows.length} illustrative records · updates as you type</p>
      </div>
      <div className="scrollbar-subtle overflow-x-auto"><table className="w-full min-w-[1050px] border-collapse text-left"><thead><tr className="bg-slate-50 text-[10px] font-bold uppercase tracking-[0.1em] text-slate-500 dark:bg-slate-950/60 dark:text-slate-400"><th className="px-5 py-3.5">Verification & applicant</th><th className="px-5 py-3.5">AA consent handle</th><th className="px-5 py-3.5">Verified FIPs</th><th className="px-5 py-3.5">Score & decision</th><th className="px-5 py-3.5">Fairness audit</th><th className="px-5 py-3.5 text-right">Certificate</th></tr></thead><tbody>
        {rows.map((row) => <tr key={row.id} className="border-t border-slate-100 transition-colors hover:bg-slate-50/70 dark:border-slate-800 dark:hover:bg-slate-800/35"><td className="px-5 py-4"><p className="text-xs font-bold text-slate-900 dark:text-slate-100">{row.name}</p><p className="mt-1 font-mono text-[10px] text-slate-500 dark:text-slate-400">{row.id} <span className="font-sans text-slate-300">·</span> {row.verified}</p></td><td className="px-5 py-4"><p className="text-xs font-semibold text-slate-700 dark:text-slate-200">{row.handle}</p><p className="mt-1 text-[10px] text-slate-400">{row.segment}</p></td><td className="px-5 py-4"><div className="flex max-w-[250px] flex-wrap gap-1">{row.fips.map((fip) => <Badge key={fip} tone="slate" className="px-2 py-0.5">{fip}</Badge>)}</div></td><td className="px-5 py-4"><div className="flex items-center gap-2"><span className="text-xs font-bold tabular-nums text-slate-900 dark:text-slate-100">{row.score}</span><Badge tone={row.decision === 'APPROVE' ? 'emerald' : 'amber'}>{row.decision}</Badge></div></td><td className="px-5 py-4"><Badge tone="emerald"><Check size={11} /> DIR {row.dir} · pass</Badge></td><td className="px-5 py-4 text-right"><Button size="sm" variant="secondary" onClick={() => setSelected(row)}><FileCheck2 size={13} /> Inspect</Button></td></tr>)}
      </tbody></table></div>
      {!rows.length && <div className="px-5 py-12 text-center"><Search size={20} className="mx-auto text-slate-300" /><p className="mt-2 text-sm font-semibold text-slate-700 dark:text-slate-200">No records found</p><p className="mt-1 text-xs text-slate-500">Try another name, ID, AA handle, or segment filter.</p></div>}
      <div className="flex flex-col gap-2 border-t border-slate-100 px-5 py-3 text-[10px] text-slate-400 dark:border-slate-800 sm:flex-row sm:items-center sm:justify-between"><span>Showing {rows.length} of 1,420 sample records</span><span>Consent metadata only · no live financial details</span></div>
    </Card>
    {selected && <CertificateDrawer applicant={selected} onClose={() => setSelected(null)} notify={notify} />}
  </div>;
}
