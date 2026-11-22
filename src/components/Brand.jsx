export function BrandMark({ size = 36, className = '' }) {
  return <svg width={size} height={size} viewBox="0 0 48 48" fill="none" aria-hidden="true" className={className}>
    <rect width="48" height="48" rx="14" fill="#4F46E5" />
    <path d="M10 31.5h28M13.5 31V22.5L24 15l10.5 7.5V31M18 31v-8h12v8" stroke="white" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" />
    <circle cx="24" cy="11.5" r="2.3" fill="#A7F3D0" />
  </svg>;
}

export function Brand({ compact = false, inverse = false }) {
  return <div className="flex items-center gap-3">
    <BrandMark size={compact ? 32 : 38} />
    <div className="leading-tight">
      <p className={`text-[16px] font-extrabold tracking-[-0.04em] ${inverse ? 'text-white' : 'text-slate-950 dark:text-white'}`}>FairCredit<span className="text-indigo-500">AA</span></p>
      {!compact && <p className={`mt-0.5 text-[9px] font-bold uppercase tracking-[0.19em] ${inverse ? 'text-indigo-200' : 'text-slate-500 dark:text-slate-400'}`}>Fairness, made visible</p>}
    </div>
  </div>;
}
