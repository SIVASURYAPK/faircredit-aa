import { Check, CircleAlert, CircleCheck, Info, LoaderCircle, X } from 'lucide-react';

const buttonStyles = {
  primary: 'bg-indigo-600 text-white shadow-sm hover:bg-indigo-700 focus-visible:ring-indigo-500',
  secondary: 'border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800',
  ghost: 'text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white',
  subtle: 'bg-indigo-50 text-indigo-700 hover:bg-indigo-100 dark:bg-indigo-950/70 dark:text-indigo-200 dark:hover:bg-indigo-900',
  danger: 'bg-rose-600 text-white hover:bg-rose-700 focus-visible:ring-rose-500',
};

export function Button({ variant = 'primary', size = 'md', className = '', children, ...props }) {
  const sizes = { sm: 'min-h-9 px-3 text-xs', md: 'min-h-10 px-4 text-sm', lg: 'min-h-12 px-5 text-sm' };
  return <button className={`inline-flex items-center justify-center gap-2 rounded-xl font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 dark:focus-visible:ring-offset-slate-950 ${buttonStyles[variant]} ${sizes[size]} ${className}`} {...props}>{children}</button>;
}

export function IconButton({ label, className = '', children, ...props }) {
  return <button type="button" aria-label={label} title={label} className={`inline-flex h-10 w-10 items-center justify-center rounded-xl text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white ${className}`} {...props}>{children}</button>;
}

export function Card({ className = '', children, ...props }) {
  return <section className={`rounded-xl border border-slate-200 bg-white shadow-[0_2px_10px_rgba(15,23,42,0.025)] dark:border-slate-800 dark:bg-slate-900 ${className}`} {...props}>{children}</section>;
}

export function Badge({ tone = 'slate', children, className = '' }) {
  const tones = {
    slate: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200',
    indigo: 'bg-indigo-50 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-200',
    emerald: 'bg-emerald-50 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200',
    amber: 'bg-amber-50 text-amber-800 dark:bg-amber-950 dark:text-amber-200',
    rose: 'bg-rose-50 text-rose-700 dark:bg-rose-950 dark:text-rose-200',
    blue: 'bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-200',
  };
  return <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold leading-4 ${tones[tone] || tones.slate} ${className}`}>{children}</span>;
}

export function Field({ label, hint, className = '', id, ...props }) {
  const fieldId = id || props.name;
  return <label htmlFor={fieldId} className={`block space-y-1.5 ${className}`}>
    <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">{label}</span>
    <input id={fieldId} className="min-h-11 w-full rounded-xl border border-slate-200 bg-white px-3.5 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100 dark:placeholder:text-slate-500" {...props} />
    {hint && <span className="block text-xs text-slate-500 dark:text-slate-400">{hint}</span>}
  </label>;
}

export function SelectField({ label, className = '', id, children, ...props }) {
  const fieldId = id || props.name;
  return <label htmlFor={fieldId} className={`block space-y-1.5 ${className}`}>
    <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">{label}</span>
    <select id={fieldId} className="min-h-11 w-full rounded-xl border border-slate-200 bg-white px-3.5 text-sm text-slate-900 outline-none focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100" {...props}>{children}</select>
  </label>;
}

export function Toggle({ checked, onChange, label, description, id }) {
  return <label htmlFor={id} className="flex cursor-pointer items-start justify-between gap-4">
    <span className="min-w-0">
      <span className="block text-sm font-semibold text-slate-800 dark:text-slate-100">{label}</span>
      {description && <span className="mt-1 block text-xs leading-5 text-slate-500 dark:text-slate-400">{description}</span>}
    </span>
    <span className={`relative mt-0.5 inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors ${checked ? 'bg-indigo-600' : 'bg-slate-300 dark:bg-slate-700'}`}>
      <input id={id} type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} className="sr-only" aria-label={label} />
      <span className={`h-5 w-5 rounded-full bg-white shadow transition-transform ${checked ? 'translate-x-[22px]' : 'translate-x-0.5'}`} />
    </span>
  </label>;
}

export function PageHeading({ eyebrow, title, description, actions }) {
  return <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
    <div className="min-w-0">
      {eyebrow && <p className="mb-2 text-[11px] font-bold uppercase tracking-[0.16em] text-indigo-600 dark:text-indigo-300">{eyebrow}</p>}
      <h1 className="text-2xl font-bold tracking-tight text-slate-950 dark:text-white sm:text-[28px]">{title}</h1>
      {description && <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600 dark:text-slate-400">{description}</p>}
    </div>
    {actions && <div className="flex shrink-0 flex-wrap gap-2">{actions}</div>}
  </div>;
}

export function ToastRegion({ toasts, dismissToast }) {
  return <div className="fixed bottom-4 right-4 z-[100] flex w-[min(92vw,380px)] flex-col gap-2" aria-live="polite" aria-label="Notifications">
    {toasts.map((toast) => {
      const Icon = toast.tone === 'error' ? CircleAlert : toast.tone === 'info' ? Info : CircleCheck;
      const tone = toast.tone === 'error' ? 'border-rose-200 dark:border-rose-900' : 'border-slate-200 dark:border-slate-700';
      return <div key={toast.id} role="status" className={`animate-in flex items-center gap-3 rounded-2xl border ${tone} bg-white px-4 py-3 text-sm text-slate-800 shadow-xl dark:bg-slate-900 dark:text-slate-100`}>
        <Icon size={17} className={toast.tone === 'error' ? 'text-rose-600' : toast.tone === 'info' ? 'text-blue-600' : 'text-emerald-600'} aria-hidden="true" />
        <span className="min-w-0 flex-1">{toast.message}</span>
        <button aria-label="Dismiss notification" onClick={() => dismissToast(toast.id)} className="rounded-md p-1 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"><X size={14} /></button>
      </div>;
    })}
  </div>;
}

export function LiveDataNotice({ className = '' }) {
  return <div className={`flex items-start gap-2 rounded-xl border border-indigo-100 bg-indigo-50/80 px-3 py-2.5 text-xs leading-5 text-indigo-800 dark:border-indigo-900 dark:bg-indigo-950/50 dark:text-indigo-200 ${className}`}>
    <Info size={15} className="mt-0.5 shrink-0" aria-hidden="true" />
    <p>Illustrative demo data — no live RBI, AA, FIP, or lender connection.</p>
  </div>;
}

export function ProgressBar({ value, tone = 'indigo' }) {
  const color = tone === 'emerald' ? 'bg-emerald-500' : tone === 'amber' ? 'bg-amber-500' : 'bg-indigo-600';
  return <div className="h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800" role="progressbar" aria-valuenow={value} aria-valuemin="0" aria-valuemax="100"><div className={`h-full rounded-full transition-all duration-300 ${color}`} style={{ width: `${Math.min(100, Math.max(0, value))}%` }} /></div>;
}
