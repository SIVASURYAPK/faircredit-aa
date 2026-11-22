# FairCredit AA — Implementation Plan

## Product and implementation approach

Build the requested six-screen FairCredit AA portal as a client-side React/Vite application. Use JSX modules and feature-oriented component boundaries, React Router for direct URL navigation, Tailwind CSS v4 via its Vite plugin, `lucide-react` for icons, and Recharts for the cash-flow and fairness visualizations. The existing project is a blank managed Webdev workspace; its preview runtime is already set to port 3000, with no server or database enabled. Keep the deliverable frontend-only: authentication, records, consent flows, tickets, simulation, and preferences use clearly identified mock data and browser `localStorage`; there are no real AA/FIP connections, credit decisions, lender services, KYC checks, or cryptographic signatures in this frontend prototype.

### Routes and application structure

- `/login` — signed-out sign-in, account creation, demo SSO, OTP verification, language selector, and support/quick ticket flows.
- `/dashboard` — applicant underwriting/coaching dashboard or lender audit view, applicant segment selector, consent-handle modal, cash-flow chart, live counterfactual simulator, roadmap, and audit queue.
- `/verified` — searchable/filterable consent ledger with certificate inspection drawer.
- `/settings` — appearance, coaching language, 2FA, consent expiry, monsoon buffer, and coaching-nudge controls.
- `/profile` — verified identity, AA/FIP details, data-redaction indicators, password update, and sign-out.
- `/support` — contact channels, direct-message form, and recent ticket tracker.
- `/` redirects according to local demo session state; unknown paths render a useful not-found screen.

Use `src/app` for routing and shared state providers; `src/components` for reusable shell, form, badge, modal, and data-display elements; `src/features/{auth,dashboard,ledger,settings,profile,support}` for page-specific UI and behavior; `src/services` for mock records, local-storage adapters, and demo calculations; and `src/styles` for Tailwind v4 entry styles and theme tokens. Keep visualizations and calculations in small focused modules instead of a monolithic page component.

### Demo behavior and persistence

Persist demo session, chosen language/theme, account settings, and newly submitted tickets to versioned local-storage keys. Signing in advances to a six-digit OTP step when the 2FA setting is active; the prototype accepts a clearly documented demo OTP and does not represent real authentication. Account creation and Google/Microsoft buttons provide functional demo feedback. Forgot-password, support FAQ, quick ticket, consent/FIP sync, certificate inspection, profile password validation, applicant/lender modes, segment changes, search/filter controls, and sign-out have working UI responses. Simulator sliders recalculate the projected score, safe-loan estimate, and SHAP-style attribution values immediately. Seed the requested values (742 score, ₹45,000 safe limit, 68.4% approval rate, 0.894 DIR, and 1,420 active AA consents) with coherent sample histories, people, and decision records. The SHA-256 artifact shown in certificate inspection is a demonstrative mock artifact, not a real signed consent record.

### Visual design

- **Design movement:** Contemporary Indian institutional fintech, combining careful public-sector legibility with the clarity of a modern underwriting console.
- **Core principles:** Make consent and explainability visible; keep key decisions legible at a glance; use color semantically rather than decoratively; support dense financial data without sacrificing mobile readability.
- **Color philosophy:** Slate neutrals establish composure and accessible contrast; FairCredit indigo is the signature action/identity color; emerald denotes verified or approved states; amber is reserved for coaching and weather-protection prompts. Light and dark surfaces will receive equivalent contrast treatment.
- **Layout paradigm:** A persistent narrow navigation rail and contextual top bar frame a generous, asymmetric working canvas; summary cards lead into deeper charts, explanations, tables, and drawers. On small screens, the rail becomes a compact mobile navigation/header and tables gain deliberate horizontal scrolling or stacked summaries.
- **Signature elements:** A custom ledger/bridge monogram beside the wordmark; compact consent-verification chips with a subtle dotted connector motif; large tabular score/rupee figures paired with concise explainability labels.
- **Interaction philosophy:** Provide visible state changes for every demo action, maintain context when switching views, use direct controls and inline feedback, and never imply a real-world verification or financial decision.
- **Animation:** Short 140–220 ms transitions for modal/drawer, tab, and control feedback; restrained score/attribution transitions; respect `prefers-reduced-motion`; no looping decorative motion.
- **Typography system:** A highly legible UI sans stack for headings and controls, with tabular numerals for balances, scores, and KPIs and a restrained monospace face for verification IDs and hash text. Use clear size/weight hierarchy rather than relying on color alone.
- **Brand essence:** Explainable, consent-first credit access for India's gig workers and MSMEs; **fair, clear, accountable**.
- **Brand voice:** Direct, practical, and respectful. Example lines: “Your cash flow tells a fuller story.” “See what could strengthen your next offer.” Avoid guarantees and unqualified financial promises.
- **Wordmark and logo:** A purpose-built bridge/ledger monogram suggesting connected accounts and a fair pathway, paired with a carefully spaced FairCredit AA wordmark; the vector mark will serve as the favicon and uploaded project-logo asset.
- **Signature brand color:** Indigo `#4F46E5`, supported by semantic emerald and amber accents.

### Dependencies, diagnostics, and serving

Pin the available pnpm toolchain in the project manifest and commit a pnpm lockfile; configure pnpm 11 lifecycle-script permissions before installing dependencies. Use Vite, React, React DOM, React Router, Tailwind CSS v4 and `@tailwindcss/vite`, `lucide-react`, and `recharts`. Register JavaScript/JSON/HTML/CSS host-managed diagnostics before the first source-code batch. Add the route manifest at `public/manus-routes.json` before starting Vite and keep it synchronized with the routes above. Serve the Vite preview on the already configured port 3000. Produce a static Vite build in `dist` and verify it with the project build command. Set project-root `app.config.ts` to a quoted durable HTTPS URL for the uploaded vector brand mark; retain a separate local SVG favicon. No backend capability is needed for this mock-data product.

## Delivery scope

Deliver the working preview and a saved project checkpoint. Do not publish the application to a public production URL unless separately requested. Clearly label simulated account, AA, fairness, and underwriting data as demo content so the frontend cannot be mistaken for a live RBI-linked service.
