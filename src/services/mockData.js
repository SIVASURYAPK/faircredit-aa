export const STORAGE_KEYS = {
  session: 'faircredit.demo.session.v1',
  preferences: 'faircredit.preferences.v1',
  settings: 'faircredit.settings.v1',
  tickets: 'faircredit.tickets.v1',
};

export const DEFAULT_PREFERENCES = { theme: 'light', language: 'English' };
export const DEFAULT_SETTINGS = {
  require2FA: true,
  consentDays: 90,
  monsoonBuffer: true,
  weeklyNudges: true,
};

export const monthLabels = ['Dec', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov'];
export const cashFlowBySegment = {
  gig: [
    { month: 'Dec', income: 36500, expenses: 28600, net: 7900 }, { month: 'Jan', income: 39200, expenses: 29600, net: 9600 },
    { month: 'Feb', income: 37800, expenses: 28400, net: 9400 }, { month: 'Mar', income: 41600, expenses: 30200, net: 11400 },
    { month: 'Apr', income: 40500, expenses: 29200, net: 11300 }, { month: 'May', income: 43800, expenses: 31500, net: 12300 },
    { month: 'Jun', income: 36900, expenses: 28600, net: 8300 }, { month: 'Jul', income: 34800, expenses: 28100, net: 6700 },
    { month: 'Aug', income: 38200, expenses: 28400, net: 9800 }, { month: 'Sep', income: 42100, expenses: 30100, net: 12000 },
    { month: 'Oct', income: 44600, expenses: 31400, net: 13200 }, { month: 'Nov', income: 45800, expenses: 31700, net: 14100 },
  ],
  msme: [
    { month: 'Dec', income: 284000, expenses: 231000, net: 53000 }, { month: 'Jan', income: 316000, expenses: 253000, net: 63000 },
    { month: 'Feb', income: 302000, expenses: 237000, net: 65000 }, { month: 'Mar', income: 331000, expenses: 259000, net: 72000 },
    { month: 'Apr', income: 324000, expenses: 249000, net: 75000 }, { month: 'May', income: 358000, expenses: 278000, net: 80000 },
    { month: 'Jun', income: 296000, expenses: 235000, net: 61000 }, { month: 'Jul', income: 282000, expenses: 228000, net: 54000 },
    { month: 'Aug', income: 319000, expenses: 245000, net: 74000 }, { month: 'Sep', income: 346000, expenses: 264000, net: 82000 },
    { month: 'Oct', income: 371000, expenses: 280000, net: 91000 }, { month: 'Nov', income: 388000, expenses: 289000, net: 99000 },
  ],
};

export const verifiedAccounts = [
  { id: 'FC-2025-0941', name: 'Ramesh Kumar', handle: 'ramesh.kumar@finvu', segment: 'Gig Worker', fips: ['HDFC UPI', 'EPFO'], score: 742, decision: 'APPROVE', dir: '0.91', verified: '2 min ago', color: 'indigo' },
  { id: 'FC-2025-0938', name: 'Lakshmi Stores', handle: 'lakshmi@onemoney', segment: 'MSME', fips: ['GSTN', 'BBPS'], score: 698, decision: 'REVIEW', dir: '0.89', verified: '18 min ago', color: 'amber' },
  { id: 'FC-2025-0933', name: 'Priya Nair', handle: 'priya.nair@anumati', segment: 'Gig Worker', fips: ['HDFC UPI', 'BBPS'], score: 781, decision: 'APPROVE', dir: '0.93', verified: '42 min ago', color: 'emerald' },
  { id: 'FC-2025-0926', name: 'Arun Electricals', handle: 'arun.elec@finvu', segment: 'MSME', fips: ['GSTN', 'BBPS', 'HDFC UPI'], score: 664, decision: 'REVIEW', dir: '0.88', verified: '1 hr ago', color: 'blue' },
  { id: 'FC-2025-0919', name: 'Meena S.', handle: 'meena.s@onemoney', segment: 'Gig Worker', fips: ['EPFO', 'HDFC UPI'], score: 716, decision: 'APPROVE', dir: '0.90', verified: '2 hrs ago', color: 'violet' },
  { id: 'FC-2025-0912', name: 'Kaveri Textiles', handle: 'kaveri@anumati', segment: 'MSME', fips: ['GSTN', 'BBPS'], score: 623, decision: 'REVIEW', dir: '0.87', verified: '3 hrs ago', color: 'rose' },
];

export const decisionQueue = [
  { id: 'FC-2025-0941', name: 'Ramesh Kumar', segment: 'Gig Worker', score: 742, decision: 'APPROVE', loan: '₹45,000', reasons: ['UPI rhythm +48', 'Income stability +36'] },
  { id: 'FC-2025-0938', name: 'Lakshmi Stores', segment: 'MSME', score: 698, decision: 'REVIEW', loan: '₹2,40,000', reasons: ['GST turnover +32', 'Seasonal volatility −14'] },
  { id: 'FC-2025-0933', name: 'Priya Nair', segment: 'Gig Worker', score: 781, decision: 'APPROVE', loan: '₹62,000', reasons: ['Savings rate +41', 'Repayment history +29'] },
  { id: 'FC-2025-0926', name: 'Arun Electricals', segment: 'MSME', score: 664, decision: 'REVIEW', loan: '₹1,80,000', reasons: ['GST turnover +27', 'Debt ratio −18'] },
];

export const roadmapItems = [
  { title: 'Keep your UPI rhythm steady', detail: '6+ months of regular business receipts can strengthen income consistency.', status: 'In progress', icon: 'activity' },
  { title: 'Build a small monthly buffer', detail: 'Try setting aside 5% of variable income in higher-earning weeks.', status: 'Next step', icon: 'piggy' },
  { title: 'Connect EPFO when ready', detail: 'A longer income history helps tell a more complete cash-flow story.', status: 'Optional', icon: 'shield' },
];

export const fairnessComparison = [
  { metric: 'Approval rate', gig: 67.8, msme: 69.1 },
  { metric: 'DIR parity', gig: 89.4, msme: 91.2 },
  { metric: 'AA completion', gig: 81.2, msme: 84.7 },
];

export const initialTickets = [
  { id: 'FC-SUP-2408', subject: 'Consent expiry clarification', status: 'In review', updated: 'Today, 10:42 AM' },
  { id: 'FC-SUP-2361', subject: 'Connected account refresh', status: 'Resolved', updated: '12 Nov 2025' },
];

export function formatINR(value) {
  return `₹${Math.max(0, Math.round(value)).toLocaleString('en-IN')}`;
}
