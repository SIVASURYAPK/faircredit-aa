import { useState } from 'react';
import { useApp } from '../../app/AppContext.jsx';
import { Badge, Button, Card, Field, LiveDataNotice, PageHeading, SelectField } from '../../components/Primitives.jsx';
import { CheckCircle2, Clock3, Headphones, Mail, MapPin, MessageSquareText, Phone, Send, TicketCheck } from 'lucide-react';
import { makeTicket } from '../../services/storage.js';

const statusTone = { 'In review': 'amber', Received: 'indigo', Resolved: 'emerald' };

export default function SupportContactPage() {
  const { session, tickets, setTickets, notify } = useApp();
  const [category, setCategory] = useState('Account Aggregator consent');
  const [subject, setSubject] = useState('');
  const [message, setMessage] = useState('');
  const [sentId, setSentId] = useState('');
  const userRole = session?.role || 'Gig Worker';

  function submitTicket(event) {
    event.preventDefault();
    if (message.trim().length < 10) {
      notify('Please add a few more details so the team can route your message.', 'error');
      return;
    }
    const ticket = makeTicket(subject || category, message);
    const ticketWithMeta = { ...ticket, category, email: session?.email || '', role: userRole };
    setTickets((current) => [ticketWithMeta, ...current]);
    setSentId(ticket.id);
    setSubject(''); setMessage('');
    notify(`Ticket ${ticket.id} has been added to your demo tracker.`);
  }

  return <div className="animate-in">
    <PageHeading eyebrow="RBI DEPA grievance desk" title="Contact & support" description="Reach the FairCredit support channels or send a direct message for this sample portal session." />
    <LiveDataNotice className="mb-5" />
    <div className="mb-5 grid gap-3 md:grid-cols-3">
      <Card className="p-5"><span className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300"><Phone size={18} /></span><p className="mt-4 text-[10px] font-bold uppercase tracking-[0.12em] text-slate-400">Toll-free helpline</p><a href="tel:18001203247" className="mt-1 block text-lg font-bold tracking-tight text-slate-950 hover:text-indigo-700 dark:text-white dark:hover:text-indigo-300">1800-120-FAIR</a><p className="mt-1 flex items-center gap-1.5 text-[10px] text-slate-500 dark:text-slate-400"><Clock3 size={12} /> Mon–Sat · 9:00 AM–6:00 PM IST</p></Card>
      <Card className="p-5"><span className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300"><Mail size={18} /></span><p className="mt-4 text-[10px] font-bold uppercase tracking-[0.12em] text-slate-400">Nodal officer</p><a href="mailto:care@faircreditaa.in" className="mt-1 block break-all text-lg font-bold tracking-tight text-slate-950 hover:text-indigo-700 dark:text-white dark:hover:text-indigo-300">care@faircreditaa.in</a><p className="mt-1 text-[10px] text-slate-500 dark:text-slate-400">Grievance and consent-related enquiries</p></Card>
      <Card className="p-5"><span className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300"><MapPin size={18} /></span><p className="mt-4 text-[10px] font-bold uppercase tracking-[0.12em] text-slate-400">Research & correspondence</p><p className="mt-1 text-lg font-bold tracking-tight text-slate-950 dark:text-white">IIT-M Research Park</p><p className="mt-1 text-[10px] text-slate-500 dark:text-slate-400">Taramani, Chennai, Tamil Nadu</p></Card>
    </div>

    <div className="grid gap-5 xl:grid-cols-[0.95fr_1.05fr]">
      <Card className="p-5 sm:p-6"><div className="flex items-start gap-3"><span className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-50 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300"><MessageSquareText size={17} /></span><div><h2 className="text-sm font-bold text-slate-950 dark:text-white">Send a direct message</h2><p className="mt-1 text-xs leading-5 text-slate-500 dark:text-slate-400">We’ll add it to the local demo ticket tracker. Nothing is sent to a real support team.</p></div></div>
        <form onSubmit={submitTicket} className="mt-5 space-y-4">
          <div className="grid gap-4 sm:grid-cols-2"><Field label="Your email" name="supportEmail" type="email" value={session?.email || ''} readOnly className="opacity-90" /><Field label="Portal role" name="supportRole" value={userRole} readOnly className="opacity-90" /></div>
          <SelectField label="How can we help?" name="category" value={category} onChange={(event) => setCategory(event.target.value)}><option>Account Aggregator consent</option><option>Data correction</option><option>Fairness or decision explanation</option><option>Login and account access</option><option>Other grievance</option></SelectField>
          <Field label="Subject" name="supportSubject" value={subject} onChange={(event) => setSubject(event.target.value)} placeholder="A short summary" />
          <label htmlFor="supportMessage" className="block space-y-1.5"><span className="text-xs font-semibold text-slate-700 dark:text-slate-300">Message</span><textarea id="supportMessage" rows={5} required minLength={10} value={message} onChange={(event) => setMessage(event.target.value)} placeholder="Share the details that will help us understand your request…" className="w-full resize-y rounded-xl border border-slate-200 bg-white px-3.5 py-3 text-sm text-slate-900 outline-none placeholder:text-slate-400 focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:placeholder:text-slate-500" /></label>
          {sentId && <p role="status" className="flex items-center gap-2 rounded-xl bg-emerald-50 px-3 py-2.5 text-xs font-semibold text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200"><CheckCircle2 size={14} /> Ticket {sentId} was added to your recent tickets.</p>}
          <Button type="submit" className="w-full sm:w-auto"><Send size={14} /> Submit message</Button>
        </form>
      </Card>

      <Card className="overflow-hidden"><div className="flex items-start justify-between gap-3 border-b border-slate-100 p-5 dark:border-slate-800 sm:p-6"><div><div className="flex items-center gap-2"><span className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300"><TicketCheck size={16} /></span><h2 className="text-sm font-bold text-slate-950 dark:text-white">Your recent tickets</h2></div><p className="mt-2 text-xs text-slate-500 dark:text-slate-400">Updates are saved to this browser for the demo session.</p></div><Badge tone="indigo">{tickets.length} total</Badge></div>
        <div className="divide-y divide-slate-100 dark:divide-slate-800">{tickets.map((ticket) => <div key={ticket.id} className="flex gap-3 p-4 sm:p-5"><span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-slate-50 text-slate-500 dark:bg-slate-800 dark:text-slate-300"><Headphones size={16} /></span><div className="min-w-0 flex-1"><div className="flex flex-wrap items-center justify-between gap-2"><p className="text-xs font-bold text-slate-800 dark:text-slate-100">{ticket.subject}</p><Badge tone={statusTone[ticket.status] || 'indigo'}>{ticket.status}</Badge></div><div className="mt-1.5 flex flex-wrap items-center gap-x-2 text-[10px] text-slate-400"><span className="font-mono font-semibold">{ticket.id}</span><span>·</span><span>{ticket.updated}</span>{ticket.category && <><span>·</span><span>{ticket.category}</span></>}</div></div></div>)}{!tickets.length && <div className="p-8 text-center text-xs text-slate-500">No tickets yet. Send a message to start a sample ticket.</div>}</div>
        <div className="border-t border-slate-100 bg-slate-50/70 p-4 text-[10px] leading-4 text-slate-500 dark:border-slate-800 dark:bg-slate-950/35 dark:text-slate-400">Demo tickets are stored locally only. For a real grievance, use an established support channel.</div>
      </Card>
    </div>
  </div>;
}
