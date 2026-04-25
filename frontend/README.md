# CLAR Frontend

Next.js 14 (Pages Router) frontend for CLAR — Clinical Lab Analysis Report.

**Live:** https://clar-608805582585.us-central1.run.app

**GCP Console:** https://console.cloud.google.com/run/detail/us-central1/clar/metrics?project=stella-cyber-analyzer

---

## Stack

- **Next.js 14** (Pages Router) — static export served by the FastAPI backend
- **TypeScript** — strict mode throughout
- **Tailwind CSS** + `@tailwindcss/typography` — utility-first styles, prose rendering for markdown
- **Clerk (`@clerk/nextjs@6.x`)** — authentication (sign-in/sign-up modal, JWT)
- **IBM Plex Sans** — primary typeface
- Design tokens centralised in `styles/tokens.ts` — no hardcoded hex in components

---

## Structure

```
frontend/
├── components/
│   ├── results/
│   │   ├── ChatDrawer.tsx      # Modal chat overlay with SSE streaming
│   │   ├── ChatMessage.tsx     # Markdown-aware message bubble
│   │   ├── FindingCard.tsx     # Individual finding with urgency badge
│   │   ├── FindingsList.tsx    # Findings list with optional urgency filter
│   │   ├── QuestionList.tsx    # Doctor question list
│   │   ├── Sidebar.tsx         # Navigation sidebar (findings / urgency / questions)
│   │   └── VerdictBanner.tsx   # Urgency summary banner
│   ├── shared/
│   │   ├── ErrorState.tsx      # Error display with retry
│   │   ├── LoadingScreen.tsx   # Animated upload progress
│   │   └── NavBar.tsx          # Top bar with CLAR logo and New Report button
│   └── upload/
│       ├── SampleButton.tsx    # Load sample report for demo
│       ├── TrustBadges.tsx     # De-id / privacy trust indicators
│       └── UploadZone.tsx      # Drag-and-drop / click file picker
├── lib/
│   ├── api.ts                  # Typed API client (uploadReport)
│   └── types.ts                # Shared TypeScript types
├── pages/
│   ├── _app.tsx                # ClerkProvider wrapper
│   ├── _document.tsx           # Custom <Head> with favicon and font
│   ├── index.tsx               # Upload page (guarded — signed-in only)
│   └── results.tsx             # Results page (requires sessionStorage report)
├── public/
│   └── favicon.ico             # Orange CLAR logo
└── styles/
    ├── globals.css             # Tailwind base/components/utilities
    └── tokens.ts               # Color and spacing tokens (single source of truth)
```

---

## Key flows

**Upload flow:**
1. User signs in via Clerk modal
2. Drops or selects a PDF/text file
3. `uploadReport()` posts to `/api/upload`, stores result in `sessionStorage`
4. Router pushes to `/results`

**Results flow:**
1. `results.tsx` reads `clar_result` from `sessionStorage` — redirects to `/` if missing
2. Sidebar lets user switch between Findings, Urgent Only, and Doctor Questions views
3. "Ask CLAR" opens `ChatDrawer` — a centered modal with SSE streaming chat
4. "+ New Report" clears `sessionStorage` and returns to `/`

**Chat streaming:**
- `fetch` to `/api/chat/stream` with `ReadableStream` reader
- SSE frames (`data: chunk\n\n`) parsed line-by-line, appended to last assistant message in real time
- `react-markdown` renders bold, bullets, and headings in assistant responses

---

## Running locally

```bash
npm install
npm run dev
# → http://localhost:3000
```

Create `frontend/.env.local`:

```
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Build (static export)

```bash
npm run build
# Outputs static files to frontend/out/ — copied into static/ for FastAPI to serve
```

The build bakes `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` into the JS bundle. Both must be set at build time.

---

## Design rules

- **150-line hard cap** per component file — split before hitting the limit
- **No hardcoded hex** — use tokens from `styles/tokens.ts`
- **No emojis** — SVG icons only
- **Clerk pinned to `@clerk/nextjs@6.x`** — v7 removed `SignedIn`/`SignedOut`
