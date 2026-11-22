import { useMemo } from 'react';
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { cashFlowBySegment } from '../../services/mockData.js';
import { Badge, Card } from '../../components/Primitives.jsx';
import { TrendingUp } from 'lucide-react';

function formatCompact(value, segment) {
  if (segment === 'MSME') return `₹${Math.round(value / 1000)}k`;
  return `₹${Math.round(value / 1000)}k`;
}

function ChartTooltip({ active, payload, label, segment }) {
  if (!active || !payload?.length) return null;
  return <div className="rounded-xl border border-slate-200 bg-white px-3 py-2 shadow-lg dark:border-slate-700 dark:bg-slate-900"><p className="text-[10px] font-semibold text-slate-500">{label} · sample month</p><p className="mt-1 text-sm font-bold text-indigo-700 dark:text-indigo-300">Net cash flow: ₹{Number(payload[0].value).toLocaleString('en-IN')}</p><p className="mt-1 text-[10px] text-slate-500">{segment === 'MSME' ? 'Business account sample' : 'Gig account sample'}</p></div>;
}

export default function CashFlowChart({ segment }) {
  const data = useMemo(() => cashFlowBySegment[segment === 'MSME' ? 'msme' : 'gig'], [segment]);
  const average = Math.round(data.reduce((sum, point) => sum + point.net, 0) / data.length);
  return <Card className="p-5 sm:p-6">
    <div className="mb-5 flex flex-wrap items-start justify-between gap-3">
      <div><div className="flex items-center gap-2"><div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600 dark:bg-indigo-950 dark:text-indigo-300"><TrendingUp size={16} /></div><h2 className="text-sm font-bold text-slate-900 dark:text-white">Cash flow, at a glance</h2></div><p className="mt-2 text-xs text-slate-500 dark:text-slate-400">Monthly net · last 12 months · {segment === 'MSME' ? 'MSME merchant' : 'gig worker'} sample</p></div>
      <Badge tone="emerald">↑ 12.8% <span className="font-medium">vs. prior year</span></Badge>
    </div>
    <div className="mb-2 flex items-end justify-between"><p className="text-2xl font-bold tracking-tight text-slate-950 dark:text-white tabular-nums">₹{average.toLocaleString('en-IN')}<span className="ml-1 text-xs font-medium text-slate-500">avg. net/month</span></p><span className="text-[10px] text-slate-400">Illustrative</span></div>
    <div role="img" aria-label={`${segment} net cash flow across the last 12 sample months`} className="h-[220px] w-full min-w-0 pt-1">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -10 }}>
          <CartesianGrid strokeDasharray="3 5" vertical={false} stroke="var(--chart-grid, #e2e8f0)" />
          <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 10 }} tickMargin={10} />
          <YAxis axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 10 }} tickFormatter={(value) => formatCompact(value, segment)} width={45} />
          <Tooltip content={<ChartTooltip segment={segment} />} cursor={{ stroke: '#c7d2fe', strokeDasharray: '4 4' }} />
          <Line type="monotone" dataKey="net" stroke="#4f46e5" strokeWidth={3} dot={{ r: 3, fill: '#4f46e5', stroke: '#fff', strokeWidth: 2 }} activeDot={{ r: 5, fill: '#4f46e5', stroke: '#c7d2fe', strokeWidth: 4 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
    <table className="sr-only"><caption>Monthly net cash-flow values for the {segment} sample</caption><thead><tr><th scope="col">Month</th><th scope="col">Net cash flow (INR)</th></tr></thead><tbody>{data.map((point) => <tr key={point.month}><th scope="row">{point.month}</th><td>{point.net.toLocaleString('en-IN')}</td></tr>)}</tbody></table>
    <div className="mt-2 flex items-center justify-center gap-2 text-[10px] text-slate-500"><span className="h-2 w-2 rounded-full bg-indigo-600" /> Net cash flow <span className="mx-1 text-slate-300">·</span> <span>Source: consented AA sample</span></div>
  </Card>;
}
