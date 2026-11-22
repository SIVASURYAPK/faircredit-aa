import { useMemo } from 'react';
import { ArrowDownRight, ArrowUpRight, CircleHelp, Lightbulb, SlidersHorizontal, TrendingUp } from 'lucide-react';
import { Badge, Card, ProgressBar } from '../../components/Primitives.jsx';
import { formatINR } from '../../services/mockData.js';

const baseBySegment = {
  'Gig Worker': { score: 742, loan: 45000, income: 45800, debt: 32, consistency: 72 },
  'MSME Merchant': { score: 698, loan: 240000, income: 388000, debt: 28, consistency: 68 },
};

export function baselineInputs(segment) {
  const base = baseBySegment[segment] || baseBySegment['Gig Worker'];
  return { income: base.income, debt: base.debt, consistency: base.consistency };
}

export function calculateProjection(segment, inputs) {
  const base = baseBySegment[segment] || baseBySegment['Gig Worker'];
  const incomeFactor = Math.max(-24, Math.min(36, ((inputs.income / base.income) - 1) * 52));
  const debtFactor = (base.debt - inputs.debt) * 1.05;
  const consistencyFactor = (inputs.consistency - base.consistency) * 0.72;
  const score = Math.round(Math.max(300, Math.min(900, base.score + incomeFactor + debtFactor + consistencyFactor)));
  const delta = score - base.score;
  const incomeLimitFactor = segment === 'MSME Merchant' ? 0.18 : 0.38;
  const loan = Math.max(5000, base.loan + delta * (segment === 'MSME Merchant' ? 1150 : 250) + (inputs.income - base.income) * incomeLimitFactor);
  const attribution = [
    { label: 'Monthly income regularity', value: Math.round(30 + incomeFactor), type: 'positive' },
    { label: 'UPI consistency / savings', value: Math.round(22 + consistencyFactor), type: 'positive' },
    { label: 'Debt-to-EMI ratio', value: Math.round(-12 - Math.max(0, inputs.debt - 20) * 0.72), type: 'negative' },
    { label: 'Repayment history', value: 28, type: 'positive' },
  ];
  return { score, loan, delta, attribution };
}

function SliderControl({ label, value, min, max, step = 1, onChange, display, suffix, note }) {
  return <div className="space-y-2.5">
    <div className="flex items-end justify-between gap-3"><label className="text-xs font-semibold text-slate-700 dark:text-slate-200">{label}</label><span className="text-xs font-bold text-slate-950 dark:text-white tabular-nums">{display ?? `${value}${suffix || ''}`}</span></div>
    <input type="range" min={min} max={max} step={step} value={value} onChange={(event) => onChange(Number(event.target.value))} aria-label={label} className="h-2 w-full cursor-pointer appearance-none rounded-full bg-slate-200 accent-indigo-600 dark:bg-slate-700" />
    <div className="flex justify-between text-[10px] text-slate-400"><span>{note?.[0] || min}</span><span>{note?.[1] || max}</span></div>
  </div>;
}

export default function CounterfactualSimulator({ segment, inputs, onChange }) {
  const projection = useMemo(() => calculateProjection(segment, inputs), [segment, inputs]);
  return <Card className="overflow-hidden">
    <div className="border-b border-slate-100 px-5 py-4 dark:border-slate-800 sm:px-6">
      <div className="flex items-start justify-between gap-4"><div className="flex items-center gap-2.5"><div className="flex h-9 w-9 items-center justify-center rounded-xl bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300"><SlidersHorizontal size={17} /></div><div><h2 className="text-sm font-bold text-slate-950 dark:text-white">What could change?</h2><p className="mt-1 text-[11px] text-slate-500 dark:text-slate-400">Explore a coaching scenario</p></div></div><Badge tone="amber"><Lightbulb size={12} /> Your next step</Badge></div>
    </div>
    <div className="grid gap-0 xl:grid-cols-[1.05fr_0.95fr]">
      <div className="space-y-5 border-b border-slate-100 p-5 dark:border-slate-800 xl:border-b-0 xl:border-r sm:p-6">
        <SliderControl label="Monthly income" value={inputs.income} min={segment === 'MSME Merchant' ? 200000 : 20000} max={segment === 'MSME Merchant' ? 650000 : 80000} step={segment === 'MSME Merchant' ? 5000 : 500} onChange={(income) => onChange({ ...inputs, income })} display={formatINR(inputs.income)} note={segment === 'MSME Merchant' ? ['₹2L', '₹6.5L'] : ['₹20k', '₹80k']} />
        <SliderControl label="Debt / EMI ratio" value={inputs.debt} min={5} max={65} onChange={(debt) => onChange({ ...inputs, debt })} suffix="%" note={['5%', '65%']} />
        <SliderControl label="UPI consistency / savings" value={inputs.consistency} min={10} max={100} onChange={(consistency) => onChange({ ...inputs, consistency })} suffix="%" note={['10%', '100%']} />
        <div className="flex items-start gap-2 rounded-xl bg-slate-50 px-3 py-2.5 text-[10px] leading-4 text-slate-500 dark:bg-slate-800/60 dark:text-slate-400"><CircleHelp size={13} className="mt-0.5 shrink-0" />These controls use illustrative factors, not a lending model or eligibility guarantee.</div>
      </div>
      <div className="p-5 sm:p-6">
        <div className="flex items-start justify-between gap-4"><div><p className="text-[10px] font-bold uppercase tracking-[0.15em] text-slate-400">Projected score</p><div className="mt-1.5 flex items-end gap-2"><span className="text-4xl font-bold tracking-[-0.06em] text-slate-950 dark:text-white tabular-nums">{projection.score}</span><span className="pb-1 text-xs text-slate-400">/ 900</span></div></div><Badge tone={projection.delta >= 0 ? 'emerald' : 'rose'}>{projection.delta >= 0 ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}{projection.delta >= 0 ? '+' : ''}{projection.delta} pts</Badge></div>
        <div className="mt-4 flex items-center justify-between rounded-xl bg-indigo-50 px-3.5 py-3 dark:bg-indigo-950/60"><span className="text-xs font-semibold text-indigo-800 dark:text-indigo-200">Illustrative safe loan limit</span><span className="text-sm font-bold text-indigo-900 dark:text-indigo-100 tabular-nums">{formatINR(projection.loan)}</span></div>
        <div className="mt-5"><div className="mb-3 flex items-center justify-between"><p className="text-[11px] font-bold text-slate-800 dark:text-slate-200">SHAP-style factors</p><span className="text-[10px] text-slate-400">sample points</span></div><div className="space-y-3.5">{projection.attribution.map((factor) => <div key={factor.label}><div className="mb-1.5 flex items-center justify-between gap-3"><span className="truncate text-[10px] font-medium text-slate-600 dark:text-slate-300">{factor.label}</span><span className={`shrink-0 text-[10px] font-bold tabular-nums ${factor.type === 'negative' ? 'text-rose-600 dark:text-rose-300' : 'text-emerald-700 dark:text-emerald-300'}`}>{factor.value > 0 ? '+' : ''}{factor.value}</span></div><ProgressBar value={Math.abs(factor.value) * 1.25} tone={factor.type === 'negative' ? 'amber' : 'emerald'} /></div>)}</div></div>
        <p className="mt-4 flex items-center gap-1.5 text-[10px] text-slate-400"><TrendingUp size={12} /> Changes recalculate as you move a slider.</p>
      </div>
    </div>
  </Card>;
}
