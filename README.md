# FairCredit AA

A React/Vite frontend prototype for consent-first, explainable credit coaching for India's gig workers and MSMEs. It uses Tailwind CSS v4, Recharts, lucide-react, React Router, and local browser storage.

## Run locally

```sh
pnpm install
pnpm dev
```

The development server listens on port 3000. Run `pnpm build` for the production static bundle in `dist/`.

## Demo sign-in

Use any valid-looking email and a password of at least six characters. When two-step verification is enabled, enter **123456**. This is a local demonstration only; no message is sent and no real identity, AA, FIP, lender, or bank account is contacted. Remember Me controls whether the mock session is retained in localStorage. Theme, language, settings, and tickets are also stored in this browser. Clear the site's localStorage to reset the demo.

## Pages

- `/login` — sign-in, account creation, OTP demo, and pre-login FAQs/ticket submission.
- `/dashboard` — applicant coaching and lender audit modes, mock cash-flow chart, simulator, consent picker, and decision queue.
- `/verified` — searchable and filterable illustrative consent ledger with sample certificate drawer.
- `/settings` — appearance, language, 2FA, consent expiry, weather buffer, and nudges.
- `/profile` — demo identity, redaction indicators, password validation, and sign-out.
- `/support` — contact details, locally tracked tickets, and a direct-message form.

All scores, loan limits, audit metrics, consent details, KYC badges, and certificate hashes are illustrative and must not be interpreted as live underwriting, a loan offer, a regulatory audit, or an RBI-connected service.
