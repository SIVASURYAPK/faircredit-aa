# FairCredit AA — Delivery ToDo

## 1. Login, sign-up, 2FA, and pre-login support

- [x] Provide a left hero panel with brand header, headline “From Everyday Cash Flows to Fair, Auditable Credit”, and a floating preview card showing live alternate-data score `742 / 900 Prime Band`, `AA Verified`, `UPI Consistency +48 SHAP pts`, and `Fairlearn DIR 0.89`.
- [x] Show trust pillars `Consent-First AA`, `Fairlearn Audited`, and `SHAP Coaching`.
- [x] Provide a right auth panel with a top-right Support tab toggle and language switcher (`English`, `हिंदी`, `தமிழ்`).
- [x] Implement Sign In fields for email/password, Remember Me, and a Forgot Password banner.
- [x] Implement Create Account fields for Full/Business Name and a Role selector (`Gig Worker`, `MSME`, `NBFC Lender`).
- [x] Include Google and Microsoft SSO buttons.
- [x] Implement a six-digit Two-Step Verification (2FA OTP) step with auto-focus inputs.
- [x] Implement a pre-login Support Tab with AA handle FAQs and quick ticket submission.

## 2. Applicant underwriting/coaching dashboard and lender audit view

- [x] Provide a top context bar that toggles between Applicant View and Lender Audit View, switches applicant segment between Gig Worker and MSME Merchant, and opens an AA Consent Handle Modal (`@finvu`, `@onemoney`, `@anumati`) to sync Financial Information Providers (FIPs).
- [x] In Applicant View, show a Credit Score Gauge Card for the 300–900 scale, score `742`, simulated delta badge, `APPROVE` status badge, Eligible Safe Loan Limit in INR (`₹45,000`), and an IMD Monsoon/Weather Income-Smoothing protection alert.
- [x] Show a 12-month net cash-flow line chart with segment context.
- [x] Provide interactive What-If Counterfactual Simulator sliders for Monthly Income, Debt/EMI Ratio, and UPI Consistency/Savings Rate; dynamically recalculate projected score, loan limit, and SHAP feature attribution bars in real time.
- [x] Show an actionable step-by-step Recovery Roadmap with credit-building milestones.
- [x] In Lender Audit View (`LenderOverview`), show portfolio KPI cards for `68.4%` Approval Rate, `DIR 0.894 Pass` Demographic Parity Ratio, and `1,420` Active AA Consents.
- [x] Show a Fairlearn bias/parity comparison chart across Gig Workers vs. MSMEs.
- [x] Show an auditable Lender Decision Queue with SHAP reason badges.

## 3. Recently verified accounts and AA ledger

- [x] Provide a DEPA cryptographic consent ledger with 24h verification stats, real-time search input, and segment filter pills (`All Segments`, `Gig Workers`, `MSMEs`).
- [x] Show a structured table with Verification IDs, Applicant Names, AA Consent Handles, Verified FIP tags (`HDFC UPI`, `GSTN`, `EPFO`, `BBPS`), Score + Decision badges, and Fairlearn DIR audit status.
- [x] Provide an Inspect Certificate drawer that displays the signed SHA-256 consent artifact. For this frontend mock, label the artifact and consent records clearly as illustrative rather than a live signature or real RBI-connected verification.

## 4. Platform and security settings

- [x] Provide organized Appearance & Regional Language settings with a Light/Dark theme switcher and `English / हिंदी / தமிழ்` coaching language.
- [x] Provide Authentication & 2FA settings with a toggle controlling whether 2FA triggers on login.
- [x] Provide Account Aggregator & Fairness Controls for Consent auto-expiry (`30/90/180 days`), Monsoon income-smoothing buffer toggle, and weekly coaching nudges.
- [x] Persist appearance, language, and settings in localStorage so they survive reloads.

## 5. Verified identity and profile

- [x] Show a user identity header with `AA KYC Verified` badge and Sign Out button.
- [x] Show a Verified Identity & AA Handle card for `ramesh.kumar@finvu`, masked mobile, 2FA status, proxy-scrubbing confirmation that PIN/Caste/Gender are redacted, and connected FIP badges.
- [x] Provide a functional Update Account Password form with validation feedback.
- [x] Keep KYC and identity verification clearly identified as demo/sample information.

## 6. Post-login Contact Us and RBI DEPA Grievance Desk

- [x] Show contact channel cards for `1800-120-FAIR` Toll-Free Helpline, `care@faircreditaa.in` Nodal Officer, and `IIT-M Research Park, Chennai`.
- [x] Provide a Send Direct Message form pre-populated with the logged-in user's email and active portal role.
- [x] Show a live Your Recent Tickets tracker and append newly submitted tickets immediately.

## 7. Shared application quality and behavior

- [x] Implement seamless navigation among all six screens with responsive desktop and mobile layouts, accessible `aria-label` attributes on icon buttons, and full dark-mode contrast parity on every card, input, and table.
- [x] Use React (Vite) with clean component architecture (`src/features/...`, `src/components/...`, `src/services/...`), Tailwind CSS v4 with class-based dark mode (`@custom-variant dark (&:where(.dark, .dark *));`) and canonical Tailwind v4 classes (`bg-linear-to-r`, `bg-linear-to-br`), `lucide-react` icons, and responsive SVG/Recharts visualizations.
- [x] Use the requested visual system: trustworthy institutional FinTech aesthetic; Slate backgrounds (`bg-slate-50` light / `bg-slate-950` dark), elevated cards (`rounded-xl border border-slate-200 dark:border-slate-800`), Indigo primary accents (`indigo-600`), Emerald verified/approved states, and Amber coaching badges.
- [x] Persist the demo session and theme in localStorage. Keep interactive data mock-driven; clearly disclose that no real authentication, RBI/AA/FIP integration, KYC verification, or live lender decisioning is performed.
- [x] Ensure zero console errors, zero Tailwind canonical class warnings, and readable, contrast-safe light and dark views.
