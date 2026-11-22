import { useRef, useState } from 'react';
import { Check, ChevronRight, LockKeyhole, ShieldCheck, X } from 'lucide-react';
import { Badge, Button, LiveDataNotice } from '../../components/Primitives.jsx';
import { useDialogFocus } from '../../components/useDialogFocus.js';

const handles = ['@finvu', '@onemoney', '@anumati'];
const sources = [
  { name: 'HDFC UPI', category: 'Payments', initials: 'H' },
  { name: 'GSTN', category: 'Business', initials: 'G' },
  { name: 'EPFO', category: 'Income', initials: 'E' },
  { name: 'BBPS', category: 'Bills', initials: 'B' },
];

export default function ConsentHandleModal({ onClose, onSync, currentHandle }) {
  const [handle, setHandle] = useState(currentHandle || handles[0]);
  const [selected, setSelected] = useState(['HDFC UPI', 'EPFO']);
  const dialogRef = useRef(null);
  const handleDialogKeyDown = useDialogFocus(dialogRef, onClose, '[aria-label="Close consent modal"]');
  const toggleSource = (source) => setSelected((items) => items.includes(source) ? items.filter((item) => item !== source) : [...items, source]);

  return <div className="fixed inset-0 z-50 flex items-end justify-center bg-slate-950/50 p-0 backdrop-blur-sm sm:items-center sm:p-5" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
    <section ref={dialogRef} tabIndex={-1} onKeyDown={handleDialogKeyDown} role="dialog" aria-modal="true" aria-labelledby="aa-modal-title" className="animate-in max-h-[92vh] w-full max-w-[520px] overflow-y-auto rounded-t-3xl border border-slate-200 bg-white p-5 shadow-2xl outline-none dark:border-slate-700 dark:bg-slate-900 sm:rounded-3xl sm:p-6">
      <div className="flex items-start justify-between gap-4"><div><Badge tone="indigo"><ShieldCheck size={12} /> Account Aggregator</Badge><h2 id="aa-modal-title" className="mt-3 text-xl font-bold tracking-tight text-slate-950 dark:text-white">Review consent sources</h2><p className="mt-1.5 text-xs leading-5 text-slate-500 dark:text-slate-400">Choose a demo AA handle and sample financial information providers.</p></div><button type="button" aria-label="Close consent modal" onClick={onClose} className="flex h-9 w-9 items-center justify-center rounded-xl text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"><X size={18} /></button></div>
      <div className="mt-6"><p className="mb-2 text-xs font-bold text-slate-800 dark:text-slate-200">Account Aggregator handle</p><div className="grid grid-cols-3 gap-2">{handles.map((item) => <button type="button" key={item} onClick={() => setHandle(item)} aria-pressed={handle === item} className={`rounded-xl border px-2 py-3 text-xs font-bold transition ${handle === item ? 'border-indigo-400 bg-indigo-50 text-indigo-800 ring-2 ring-indigo-500/10 dark:border-indigo-700 dark:bg-indigo-950 dark:text-indigo-200' : 'border-slate-200 text-slate-600 hover:border-slate-300 dark:border-slate-700 dark:text-slate-300 dark:hover:border-slate-600'}`}>{item}</button>)}</div></div>
      <div className="mt-6"><div className="mb-2 flex items-center justify-between"><p className="text-xs font-bold text-slate-800 dark:text-slate-200">Financial Information Providers</p><span className="text-[10px] text-slate-400">{selected.length} selected</span></div><div className="grid grid-cols-2 gap-2">{sources.map((source) => { const active = selected.includes(source.name); return <button type="button" key={source.name} onClick={() => toggleSource(source.name)} aria-pressed={active} className={`flex items-center gap-2.5 rounded-xl border p-3 text-left transition ${active ? 'border-indigo-300 bg-indigo-50/80 dark:border-indigo-800 dark:bg-indigo-950/50' : 'border-slate-200 hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800'}`}><span className={`flex h-8 w-8 items-center justify-center rounded-lg text-xs font-bold ${active ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-300'}`}>{source.initials}</span><span className="min-w-0 flex-1"><span className="block text-xs font-bold text-slate-800 dark:text-slate-100">{source.name}</span><span className="block text-[10px] text-slate-500 dark:text-slate-400">{source.category}</span></span>{active && <Check size={14} className="text-indigo-600 dark:text-indigo-300" />}</button>; })}</div></div>
      <div className="mt-5"><LiveDataNotice /></div>
      <div className="mt-5 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end"><Button variant="secondary" onClick={onClose}>Cancel</Button><Button disabled={!selected.length} onClick={() => onSync({ handle, sources: selected })}><LockKeyhole size={14} /> Sync demo sources <ChevronRight size={14} /></Button></div>
      <p className="mt-3 text-center text-[10px] text-slate-400">A real consent request is not created or transmitted.</p>
    </section>
  </div>;
}
