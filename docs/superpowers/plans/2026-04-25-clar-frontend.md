# CLAR Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Next.js 14 (Pages Router) frontend with Clerk auth, IBM Plex Sans, three screens (upload, results with sidebar, chat), and a static export served by FastAPI — all matching the CLAR_Prototype.html design reference.

**Architecture:** Next.js 14 Pages Router with TypeScript and Tailwind CSS. Clerk `@clerk/nextjs@6.x` (pinned) gates the upload and results screens. All API calls go through `lib/api.ts`. The app compiles to a static export (`output: 'export'` in `next.config.ts`) and is served by FastAPI from `./static`. Design tokens live in `styles/tokens.ts` — no hardcoded hex values in components. Each file stays under 150 lines.

**Tech Stack:** Next.js 14 (Pages Router) · TypeScript · Tailwind CSS · Clerk `@clerk/nextjs@6.x` · IBM Plex Sans (Google Fonts) · Inline SVG icons only

**Prerequisite:** Backend API running at `http://localhost:8000`. Complete the backend plan first.

---

## File Map

```
frontend/
  pages/
    _app.tsx              # ClerkProvider + global styles
    index.tsx             # Upload screen (public — Clerk SignedIn/SignedOut gate)
    results.tsx           # Results + sidebar (protected — redirects to sign-in if not authed)
    _document.tsx         # IBM Plex Sans font link
  components/
    upload/
      UploadZone.tsx      # Drag-and-drop + file picker
      SampleButton.tsx    # "Try with sample CBC" button
      TrustBadges.tsx     # PII stripped / no storage / HIPAA aligned badges
    results/
      Sidebar.tsx         # Left panel: report info, verdict, nav, Ask CLAR button
      FindingCard.tsx     # Expandable finding card with urgency badge
      FindingsList.tsx    # Maps findings to FindingCard, filters by view
      VerdictBanner.tsx   # Top-level urgency summary
      QuestionList.tsx    # Numbered list of 5 doctor questions
      ChatDrawer.tsx      # Slide-in chat panel with starter chips
    shared/
      NavBar.tsx          # Top nav with CLAR logo + New Report button
      ErrorState.tsx      # Friendly error display
      LoadingScreen.tsx   # Agent status progress during upload
  lib/
    api.ts                # All fetch calls — one function per endpoint
    types.ts              # TypeScript interfaces matching API response shapes
  styles/
    tokens.ts             # Design tokens — no hardcoded hex in components
    globals.css           # Tailwind directives + IBM Plex Sans import
  public/
    (static assets)
  next.config.ts          # output: 'export', images.unoptimized: true
  tailwind.config.ts
  tsconfig.json
  package.json
```

---

## Task 1: Next.js Project Scaffold

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/next.config.ts`
- Create: `frontend/tailwind.config.ts`
- Create: `frontend/postcss.config.js`
- Create: `frontend/styles/globals.css`
- Create: `frontend/styles/tokens.ts`
- Create: `frontend/.env.local.example`

- [ ] **Step 1: Scaffold Next.js project**

```bash
cd frontend
npx create-next-app@14 . --typescript --tailwind --eslint --no-app --no-src-dir \
  --import-alias "@/*" --yes
```

Expected: Next.js 14 project created with Pages Router, TypeScript, Tailwind, ESLint.

- [ ] **Step 2: Install Clerk (pin to v6)**

```bash
npm install @clerk/nextjs@6
```

Expected: `package.json` shows `"@clerk/nextjs": "^6.x.x"`. Verify: `npm ls @clerk/nextjs`.

- [ ] **Step 3: Update `next.config.ts` for static export**

```typescript
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  images: {
    unoptimized: true,
  },
  trailingSlash: true,
};

export default nextConfig;
```

- [ ] **Step 4: Create `frontend/styles/tokens.ts`**

```typescript
export const colors = {
  navy: "#1B2A4A",
  blue: "#2563EB",
  green: "#1E8B5A",
  amber: "#C87F0A",
  red: "#C0392B",
  surface: "#F5F7FA",
  border: "#E0E0E0",
  textPrimary: "#0F172A",
  textSecondary: "#6B7280",
  white: "#FFFFFF",
} as const;

export const urgencyColors = {
  normal: { bg: "#E8F5EE", text: "#1E8B5A", border: "#1E8B5A" },
  watch: { bg: "#FEF9E7", text: "#C87F0A", border: "#C87F0A" },
  urgent: { bg: "#FDEDEC", text: "#C0392B", border: "#C0392B" },
} as const;
```

- [ ] **Step 5: Update `frontend/styles/globals.css`**

```css
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  font-family: 'IBM Plex Sans', sans-serif;
  background-color: #F5F7FA;
  color: #0F172A;
}
```

- [ ] **Step 6: Update `frontend/tailwind.config.ts`**

```typescript
import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["IBM Plex Sans", "sans-serif"],
      },
      colors: {
        navy: "#1B2A4A",
        cblue: "#2563EB",
        cgreen: "#1E8B5A",
        amber: "#C87F0A",
        danger: "#C0392B",
      },
    },
  },
  plugins: [],
};

export default config;
```

- [ ] **Step 7: Create `frontend/.env.local.example`**

```
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Copy to `.env.local` and fill in values from Clerk Dashboard.

- [ ] **Step 8: Verify dev server starts**

```bash
cd frontend
cp .env.local.example .env.local
# Fill in Clerk keys from https://dashboard.clerk.com
npm run dev
```

Expected: Next.js dev server at `http://localhost:3000`. Default Next.js page loads.

- [ ] **Step 9: Commit**

```bash
cd ..  # back to clar/
git add frontend/
git commit -m "feat: Next.js 14 scaffold — Pages Router, Tailwind, Clerk v6, static export config"
```

---

## Task 2: TypeScript Types + API Client

**Files:**
- Create: `frontend/lib/types.ts`
- Create: `frontend/lib/api.ts`

- [ ] **Step 1: Create `frontend/lib/types.ts`**

```typescript
export interface Finding {
  name: string;
  value: string;
  reference_range: string;
  urgency: "normal" | "watch" | "urgent";
  urgency_reason: string;
  explanation: string;
}

export interface Verdict {
  level: "normal" | "watch" | "urgent";
  summary: string;
}

export interface ReportResult {
  report_id: string;
  report_type: string;
  verdict: Verdict;
  findings: Finding[];
  questions: string[];
  processing_time_ms: number;
  deid_entities_removed: number;
}

export interface ChatResponse {
  answer: string;
}

export type ViewType = "findings" | "urgency" | "questions";
```

- [ ] **Step 2: Create `frontend/lib/api.ts`**

```typescript
import { ReportResult, ChatResponse } from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function uploadReport(file: File): Promise<ReportResult> {
  const form = new FormData();
  form.append("file", file);

  const res = await fetch(`${BASE}/api/upload`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error ?? `Upload failed: ${res.status}`);
  }

  return res.json();
}

export async function sendChatMessage(
  reportId: string,
  question: string
): Promise<ChatResponse> {
  const res = await fetch(`${BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ report_id: reportId, question }),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error ?? `Chat failed: ${res.status}`);
  }

  return res.json();
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/lib/
git commit -m "feat: TypeScript types + API client (upload + chat)"
```

---

## Task 3: Shared Components — NavBar, ErrorState, LoadingScreen

**Files:**
- Create: `frontend/components/shared/NavBar.tsx`
- Create: `frontend/components/shared/ErrorState.tsx`
- Create: `frontend/components/shared/LoadingScreen.tsx`

- [ ] **Step 1: Create `frontend/components/shared/NavBar.tsx`**

```tsx
import { useRouter } from "next/router";

interface NavBarProps {
  showNewReport?: boolean;
}

export function NavBar({ showNewReport = false }: NavBarProps) {
  const router = useRouter();

  return (
    <header
      style={{ backgroundColor: "#1B2A4A" }}
      className="flex items-center justify-between px-6 py-3"
    >
      <div
        className="text-white text-xl font-bold tracking-tight cursor-pointer"
        onClick={() => router.push("/")}
      >
        CLAR
      </div>
      {showNewReport && (
        <button
          onClick={() => router.push("/")}
          className="bg-white text-navy text-sm font-semibold px-4 py-1.5 rounded-md hover:bg-gray-100 transition-colors"
          style={{ color: "#1B2A4A" }}
        >
          + New Report
        </button>
      )}
    </header>
  );
}
```

- [ ] **Step 2: Create `frontend/components/shared/ErrorState.tsx`**

```tsx
interface ErrorStateProps {
  message: string;
  onRetry?: () => void;
}

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center min-h-64 px-6">
      <div
        className="w-12 h-12 rounded-full flex items-center justify-center mb-4"
        style={{ backgroundColor: "#FDEDEC" }}
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#C0392B" strokeWidth="2">
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
      </div>
      <p className="text-center text-gray-700 mb-4 max-w-sm">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="px-4 py-2 bg-cblue text-white rounded-md text-sm font-semibold hover:bg-blue-700 transition-colors"
          style={{ backgroundColor: "#2563EB" }}
        >
          Try again
        </button>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Create `frontend/components/shared/LoadingScreen.tsx`**

```tsx
const AGENT_STEPS = [
  "Extracting report text...",
  "Removing personal information...",
  "Analysing findings...",
  "Flagging urgency levels...",
  "Generating doctor questions...",
];

interface LoadingScreenProps {
  currentStep?: number;
}

export function LoadingScreen({ currentStep = 0 }: LoadingScreenProps) {
  return (
    <div className="flex flex-col items-center justify-center min-h-64 px-6">
      <div className="mb-6">
        <div
          className="w-12 h-12 rounded-full border-4 border-t-transparent animate-spin"
          style={{ borderColor: "#2563EB", borderTopColor: "transparent" }}
        />
      </div>
      <h3 className="text-lg font-semibold mb-4" style={{ color: "#0F172A" }}>
        Analysing your report
      </h3>
      <div className="w-full max-w-xs space-y-2">
        {AGENT_STEPS.map((step, i) => (
          <div key={step} className="flex items-center gap-3">
            <div
              className="w-5 h-5 rounded-full flex-shrink-0 flex items-center justify-center"
              style={{
                backgroundColor: i < currentStep ? "#1E8B5A" : i === currentStep ? "#2563EB" : "#E0E0E0",
              }}
            >
              {i < currentStep && (
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              )}
            </div>
            <span
              className="text-sm"
              style={{
                color: i <= currentStep ? "#0F172A" : "#6B7280",
                fontWeight: i === currentStep ? 600 : 400,
              }}
            >
              {step}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/components/shared/
git commit -m "feat: shared components — NavBar, ErrorState, LoadingScreen"
```

---

## Task 4: Upload Screen Components

**Files:**
- Create: `frontend/components/upload/UploadZone.tsx`
- Create: `frontend/components/upload/SampleButton.tsx`
- Create: `frontend/components/upload/TrustBadges.tsx`

- [ ] **Step 1: Create `frontend/components/upload/TrustBadges.tsx`**

```tsx
const BADGES = [
  {
    label: "PII stripped before analysis",
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
        <path d="M7 11V7a5 5 0 0 1 10 0v4" />
      </svg>
    ),
  },
  {
    label: "Report not stored",
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <polyline points="3 6 5 6 21 6" />
        <path d="M19 6l-1 14H6L5 6" />
        <path d="M10 11v6M14 11v6" />
      </svg>
    ),
  },
  {
    label: "HIPAA aligned",
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
        <polyline points="9 12 11 14 15 10" />
      </svg>
    ),
  },
];

export function TrustBadges() {
  return (
    <div className="flex flex-wrap justify-center gap-3 mt-6">
      {BADGES.map(({ label, icon }) => (
        <div
          key={label}
          className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium"
          style={{ backgroundColor: "#E8F5EE", color: "#1E8B5A" }}
        >
          {icon}
          {label}
        </div>
      ))}
    </div>
  );
}
```

- [ ] **Step 2: Create `frontend/components/upload/SampleButton.tsx`**

```tsx
interface SampleButtonProps {
  onLoad: (file: File) => void;
}

const SAMPLE_CBC = `CBC Blood Panel Report
Date: [DATE]
Report Type: Laboratory

Haemoglobin: 10.2 g/dL (Reference: 12.0-16.0 g/dL)
MCV: 72 fL (Reference: 80-100 fL)
MCH: 24 pg (Reference: 27-33 pg)
WBC: 6.2 x10^3/uL (Reference: 4.5-11.0 x10^3/uL)
Platelets: 210 x10^3/uL (Reference: 150-400 x10^3/uL)
Neutrophils: 65% (Reference: 40-75%)
`;

export function SampleButton({ onLoad }: SampleButtonProps) {
  function handleClick() {
    const blob = new Blob([SAMPLE_CBC], { type: "text/plain" });
    const file = new File([blob], "sample_cbc.txt", { type: "text/plain" });
    onLoad(file);
  }

  return (
    <button
      onClick={handleClick}
      className="mt-4 text-sm font-medium underline underline-offset-2 hover:opacity-70 transition-opacity"
      style={{ color: "#2563EB" }}
    >
      Try with a sample CBC report
    </button>
  );
}
```

- [ ] **Step 3: Create `frontend/components/upload/UploadZone.tsx`**

```tsx
import { useRef, useState, DragEvent, ChangeEvent } from "react";

interface UploadZoneProps {
  onFile: (file: File) => void;
  disabled?: boolean;
}

export function UploadZone({ onFile, disabled = false }: UploadZoneProps) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) onFile(file);
  }

  function handleChange(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) onFile(file);
  }

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => !disabled && inputRef.current?.click()}
      className="border-2 border-dashed rounded-xl p-12 flex flex-col items-center justify-center cursor-pointer transition-colors"
      style={{
        borderColor: dragging ? "#2563EB" : "#CBD5E1",
        backgroundColor: dragging ? "#EFF6FF" : "#FFFFFF",
        opacity: disabled ? 0.6 : 1,
        cursor: disabled ? "not-allowed" : "pointer",
      }}
    >
      <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#6B7280" strokeWidth="1.5" className="mb-4">
        <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
        <polyline points="17 8 12 3 7 8" />
        <line x1="12" y1="3" x2="12" y2="15" />
      </svg>
      <p className="text-base font-semibold mb-1" style={{ color: "#0F172A" }}>
        Drop your medical report here
      </p>
      <p className="text-sm" style={{ color: "#6B7280" }}>
        PDF or plain text · max 10 MB
      </p>
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.txt"
        className="hidden"
        onChange={handleChange}
        disabled={disabled}
      />
    </div>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/components/upload/
git commit -m "feat: upload components — UploadZone, SampleButton, TrustBadges"
```

---

## Task 5: Results Components — FindingCard, Sidebar, VerdictBanner, QuestionList

**Files:**
- Create: `frontend/components/results/FindingCard.tsx`
- Create: `frontend/components/results/FindingsList.tsx`
- Create: `frontend/components/results/VerdictBanner.tsx`
- Create: `frontend/components/results/QuestionList.tsx`
- Create: `frontend/components/results/Sidebar.tsx`

- [ ] **Step 1: Create `frontend/components/results/FindingCard.tsx`**

```tsx
import { useState } from "react";
import { Finding } from "@/lib/types";
import { urgencyColors } from "@/styles/tokens";

interface FindingCardProps {
  finding: Finding;
}

export function FindingCard({ finding }: FindingCardProps) {
  const [expanded, setExpanded] = useState(finding.urgency !== "normal");
  const palette = urgencyColors[finding.urgency];

  return (
    <div
      className="rounded-xl mb-3 overflow-hidden"
      style={{ border: `1px solid #E0E0E0`, boxShadow: "0 1px 4px rgba(0,0,0,0.06)" }}
    >
      <button
        className="w-full flex items-center gap-3 px-4 py-3.5 text-left"
        onClick={() => setExpanded((v) => !v)}
      >
        <div className="flex-1">
          <div className="font-semibold text-sm" style={{ color: "#0F172A" }}>
            {finding.name}
          </div>
          <div className="text-xs mt-0.5" style={{ color: "#6B7280" }}>
            {finding.value} &nbsp;·&nbsp; Ref: {finding.reference_range}
          </div>
        </div>
        <span
          className="text-xs font-bold uppercase px-2.5 py-0.5 rounded-full tracking-wide"
          style={{ backgroundColor: palette.bg, color: palette.text }}
        >
          {finding.urgency}
        </span>
        <svg
          width="12"
          height="12"
          viewBox="0 0 24 24"
          fill="none"
          stroke="#6B7280"
          strokeWidth="2"
          style={{ transform: expanded ? "rotate(90deg)" : "none", transition: "transform 0.15s" }}
        >
          <polyline points="9 18 15 12 9 6" />
        </svg>
      </button>

      {expanded && (
        <div
          className="px-4 pb-4 text-sm leading-relaxed"
          style={{ borderTop: "1px solid #F5F7FA", paddingTop: "0.75rem", color: "#0F172A" }}
        >
          {finding.explanation}
          {finding.urgency_reason && (
            <div
              className="mt-2 text-xs px-2.5 py-1.5 rounded"
              style={{ backgroundColor: palette.bg, color: palette.text }}
            >
              {finding.urgency_reason}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Create `frontend/components/results/FindingsList.tsx`**

```tsx
import { Finding } from "@/lib/types";
import { FindingCard } from "./FindingCard";

interface FindingsListProps {
  findings: Finding[];
  filterUrgency?: boolean;
}

export function FindingsList({ findings, filterUrgency = false }: FindingsListProps) {
  const displayed = filterUrgency
    ? findings.filter((f) => f.urgency !== "normal")
    : findings;

  if (displayed.length === 0) {
    return (
      <p className="text-sm text-center py-8" style={{ color: "#6B7280" }}>
        {filterUrgency ? "No flagged findings." : "No findings to display."}
      </p>
    );
  }

  return (
    <div>
      {displayed.map((f) => (
        <FindingCard key={f.name} finding={f} />
      ))}
    </div>
  );
}
```

- [ ] **Step 3: Create `frontend/components/results/VerdictBanner.tsx`**

```tsx
import { Verdict } from "@/lib/types";
import { urgencyColors } from "@/styles/tokens";

interface VerdictBannerProps {
  verdict: Verdict;
}

export function VerdictBanner({ verdict }: VerdictBannerProps) {
  const palette = urgencyColors[verdict.level];

  return (
    <div
      className="rounded-lg px-4 py-3 mb-5 flex items-center gap-3"
      style={{ backgroundColor: palette.bg, borderLeft: `3px solid ${palette.border}` }}
    >
      <div>
        <div
          className="text-xs font-bold uppercase tracking-widest mb-0.5"
          style={{ color: palette.text }}
        >
          {verdict.level}
        </div>
        <div className="text-sm" style={{ color: "#0F172A" }}>
          {verdict.summary}
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Create `frontend/components/results/QuestionList.tsx`**

```tsx
interface QuestionListProps {
  questions: string[];
}

export function QuestionList({ questions }: QuestionListProps) {
  return (
    <div>
      <h3 className="text-base font-semibold mb-4" style={{ color: "#0F172A" }}>
        Questions to ask your doctor
      </h3>
      <ol className="space-y-3">
        {questions.map((q, i) => (
          <li
            key={i}
            className="flex gap-3 text-sm leading-relaxed"
            style={{ color: "#0F172A" }}
          >
            <span
              className="flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white"
              style={{ backgroundColor: "#2563EB" }}
            >
              {i + 1}
            </span>
            {q}
          </li>
        ))}
      </ol>
    </div>
  );
}
```

- [ ] **Step 5: Create `frontend/components/results/Sidebar.tsx`**

```tsx
import { ViewType } from "@/lib/types";
import { Verdict } from "@/lib/types";
import { urgencyColors } from "@/styles/tokens";

interface SidebarProps {
  reportType: string;
  verdict: Verdict;
  activeView: ViewType;
  onViewChange: (v: ViewType) => void;
  onAskClar: () => void;
}

const NAV_ITEMS: { view: ViewType; label: string; icon: JSX.Element }[] = [
  {
    view: "findings",
    label: "Findings",
    icon: (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M9 11l3 3L22 4" />
        <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11" />
      </svg>
    ),
  },
  {
    view: "urgency",
    label: "Urgency Summary",
    icon: (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="12" r="10" />
        <line x1="12" y1="8" x2="12" y2="12" />
        <line x1="12" y1="16" x2="12.01" y2="16" />
      </svg>
    ),
  },
  {
    view: "questions",
    label: "Doctor Questions",
    icon: (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" />
      </svg>
    ),
  },
];

export function Sidebar({ reportType, verdict, activeView, onViewChange, onAskClar }: SidebarProps) {
  const palette = urgencyColors[verdict.level];

  return (
    <aside
      className="flex flex-col"
      style={{ width: 220, flexShrink: 0, backgroundColor: "#F5F7FA", borderRight: "1px solid #E0E0E0" }}
    >
      <div style={{ padding: "1rem", borderBottom: "1px solid #E0E0E0" }}>
        <div className="text-xs font-semibold uppercase tracking-widest mb-1" style={{ color: "#6B7280" }}>
          Report
        </div>
        <div className="font-semibold text-sm" style={{ color: "#0F172A" }}>
          {reportType.charAt(0).toUpperCase() + reportType.slice(1)} Results
        </div>
      </div>

      <div style={{ margin: "0.75rem 1rem" }}>
        <div
          className="rounded px-3 py-2"
          style={{ backgroundColor: palette.bg, borderLeft: `3px solid ${palette.border}` }}
        >
          <div className="text-xs font-bold uppercase tracking-wide" style={{ color: palette.text }}>
            {verdict.level}
          </div>
          <div className="text-xs mt-0.5 leading-snug" style={{ color: "#0F172A" }}>
            {verdict.summary}
          </div>
        </div>
      </div>

      <nav style={{ padding: "0 0.5rem", flex: 1 }}>
        <div className="text-xs font-semibold uppercase tracking-widest px-2 mb-1" style={{ color: "#6B7280" }}>
          View
        </div>
        {NAV_ITEMS.map(({ view, label, icon }) => (
          <button
            key={view}
            onClick={() => onViewChange(view)}
            className="w-full flex items-center gap-2 px-2 py-2 rounded-md text-sm mb-0.5 font-medium transition-colors"
            style={
              activeView === view
                ? { backgroundColor: "#1B2A4A", color: "#FFFFFF" }
                : { color: "#6B7280" }
            }
          >
            {icon}
            {label}
          </button>
        ))}
      </nav>

      <div style={{ padding: "1rem", borderTop: "1px solid #E0E0E0" }}>
        <button
          onClick={onAskClar}
          className="w-full flex items-center justify-center gap-2 text-sm font-semibold py-2.5 rounded-lg text-white transition-opacity hover:opacity-90"
          style={{ backgroundColor: "#2563EB" }}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
          </svg>
          Ask CLAR
        </button>
      </div>
    </aside>
  );
}
```

- [ ] **Step 6: Commit**

```bash
git add frontend/components/results/
git commit -m "feat: results components — FindingCard, FindingsList, VerdictBanner, QuestionList, Sidebar"
```

---

## Task 6: ChatDrawer Component

**Files:**
- Create: `frontend/components/results/ChatDrawer.tsx`

- [ ] **Step 1: Create `frontend/components/results/ChatDrawer.tsx`**

```tsx
import { useState, useRef, useEffect } from "react";
import { sendChatMessage } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  text: string;
}

interface ChatDrawerProps {
  reportId: string;
  open: boolean;
  onClose: () => void;
  starterQuestions: string[];
}

export function ChatDrawer({ reportId, open, onClose, starterQuestions }: ChatDrawerProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend(text: string) {
    if (!text.trim() || loading) return;
    setMessages((prev) => [...prev, { role: "user", text }]);
    setInput("");
    setLoading(true);
    try {
      const res = await sendChatMessage(reportId, text);
      setMessages((prev) => [...prev, { role: "assistant", text: res.answer }]);
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", text: "Sorry, I couldn't answer that. Please try again." }]);
    } finally {
      setLoading(false);
    }
  }

  if (!open) return null;

  const chips = starterQuestions.slice(0, 3);

  return (
    <div
      className="fixed inset-y-0 right-0 flex flex-col shadow-2xl z-50"
      style={{ width: 380, backgroundColor: "#FFFFFF", borderLeft: "1px solid #E0E0E0" }}
    >
      <div
        className="flex items-center justify-between px-4 py-3"
        style={{ borderBottom: "1px solid #E0E0E0", backgroundColor: "#1B2A4A" }}
      >
        <span className="text-white font-semibold text-sm">Ask CLAR</span>
        <button onClick={onClose} className="text-white opacity-70 hover:opacity-100 transition-opacity">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.length === 0 && (
          <div>
            <p className="text-sm mb-3" style={{ color: "#6B7280" }}>
              Ask a question about your report, or try one of these:
            </p>
            <div className="space-y-2">
              {chips.map((q) => (
                <button
                  key={q}
                  onClick={() => handleSend(q)}
                  className="w-full text-left text-xs px-3 py-2 rounded-lg border transition-colors hover:bg-blue-50"
                  style={{ borderColor: "#E0E0E0", color: "#0F172A" }}
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`text-sm px-3 py-2.5 rounded-lg max-w-xs ${
              msg.role === "user" ? "ml-auto" : "mr-auto"
            }`}
            style={
              msg.role === "user"
                ? { backgroundColor: "#2563EB", color: "#FFFFFF" }
                : { backgroundColor: "#F5F7FA", color: "#0F172A" }
            }
          >
            {msg.text}
          </div>
        ))}
        {loading && (
          <div
            className="mr-auto text-sm px-3 py-2.5 rounded-lg"
            style={{ backgroundColor: "#F5F7FA", color: "#6B7280" }}
          >
            Thinking...
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div
        className="flex gap-2 p-3"
        style={{ borderTop: "1px solid #E0E0E0" }}
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend(input)}
          placeholder="Ask about your results..."
          className="flex-1 text-sm px-3 py-2 rounded-lg border outline-none"
          style={{ borderColor: "#CBD5E1", color: "#0F172A" }}
          disabled={loading}
        />
        <button
          onClick={() => handleSend(input)}
          disabled={loading || !input.trim()}
          className="px-3 py-2 rounded-lg text-white font-semibold text-sm disabled:opacity-50 transition-opacity"
          style={{ backgroundColor: "#2563EB" }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="22" y1="2" x2="11" y2="13" />
            <polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>
        </button>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/components/results/ChatDrawer.tsx
git commit -m "feat: ChatDrawer — slide-in chat with starter chips and message thread"
```

---

## Task 7: Pages — `_app.tsx`, `_document.tsx`, `index.tsx`

**Files:**
- Create: `frontend/pages/_app.tsx`
- Create: `frontend/pages/_document.tsx`
- Modify: `frontend/pages/index.tsx`

- [ ] **Step 1: Create `frontend/pages/_app.tsx`**

```tsx
import { ClerkProvider } from "@clerk/nextjs";
import type { AppProps } from "next/app";
import "@/styles/globals.css";

export default function App({ Component, pageProps }: AppProps) {
  return (
    <ClerkProvider {...pageProps}>
      <Component {...pageProps} />
    </ClerkProvider>
  );
}
```

- [ ] **Step 2: Create `frontend/pages/_document.tsx`**

```tsx
import { Html, Head, Main, NextScript } from "next/document";

export default function Document() {
  return (
    <Html lang="en">
      <Head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </Head>
      <body>
        <Main />
        <NextScript />
      </body>
    </Html>
  );
}
```

- [ ] **Step 3: Write `frontend/pages/index.tsx`**

```tsx
import { useState } from "react";
import { useRouter } from "next/router";
import { SignedIn, SignedOut, SignInButton } from "@clerk/nextjs";
import { NavBar } from "@/components/shared/NavBar";
import { UploadZone } from "@/components/upload/UploadZone";
import { SampleButton } from "@/components/upload/SampleButton";
import { TrustBadges } from "@/components/upload/TrustBadges";
import { LoadingScreen } from "@/components/shared/LoadingScreen";
import { ErrorState } from "@/components/shared/ErrorState";
import { uploadReport } from "@/lib/api";
import { ReportResult } from "@/lib/types";

type UploadState = "idle" | "uploading" | "error";

export default function IndexPage() {
  const router = useRouter();
  const [uploadState, setUploadState] = useState<UploadState>("idle");
  const [errorMessage, setErrorMessage] = useState("");
  const [step, setStep] = useState(0);

  async function handleFile(file: File) {
    setUploadState("uploading");
    setStep(0);

    const timer = setInterval(() => setStep((s) => Math.min(s + 1, 4)), 1200);

    try {
      const result: ReportResult = await uploadReport(file);
      clearInterval(timer);
      // Store in sessionStorage — simple, no auth required for this demo
      sessionStorage.setItem("clar_result", JSON.stringify(result));
      router.push("/results");
    } catch (err) {
      clearInterval(timer);
      setErrorMessage(err instanceof Error ? err.message : "Upload failed. Please try again.");
      setUploadState("error");
    }
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: "#F5F7FA" }}>
      <NavBar />

      <main className="max-w-2xl mx-auto px-4 py-16">
        <div className="text-center mb-10">
          <h1 className="text-3xl font-bold mb-3" style={{ color: "#1B2A4A" }}>
            Understand your medical report
          </h1>
          <p className="text-base" style={{ color: "#6B7280" }}>
            Upload a lab result, radiology report, or discharge summary. CLAR explains it in plain English.
          </p>
        </div>

        <SignedOut>
          <div
            className="rounded-xl p-8 text-center"
            style={{ backgroundColor: "#FFFFFF", border: "1px solid #E0E0E0" }}
          >
            <p className="mb-4 text-sm" style={{ color: "#6B7280" }}>
              Sign in to analyse your report.
            </p>
            <SignInButton mode="modal">
              <button
                className="px-6 py-2.5 rounded-lg text-white font-semibold text-sm"
                style={{ backgroundColor: "#2563EB" }}
              >
                Sign in
              </button>
            </SignInButton>
          </div>
        </SignedOut>

        <SignedIn>
          {uploadState === "idle" && (
            <>
              <UploadZone onFile={handleFile} />
              <div className="text-center">
                <SampleButton onLoad={handleFile} />
              </div>
            </>
          )}
          {uploadState === "uploading" && <LoadingScreen currentStep={step} />}
          {uploadState === "error" && (
            <ErrorState
              message={errorMessage}
              onRetry={() => setUploadState("idle")}
            />
          )}
        </SignedIn>

        <TrustBadges />
      </main>
    </div>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/pages/
git commit -m "feat: index page — upload screen with Clerk auth, loading states, error handling"
```

---

## Task 8: Results Page

**Files:**
- Create: `frontend/pages/results.tsx`

- [ ] **Step 1: Write `frontend/pages/results.tsx`**

```tsx
import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import { useAuth } from "@clerk/nextjs";
import { NavBar } from "@/components/shared/NavBar";
import { Sidebar } from "@/components/results/Sidebar";
import { FindingsList } from "@/components/results/FindingsList";
import { VerdictBanner } from "@/components/results/VerdictBanner";
import { QuestionList } from "@/components/results/QuestionList";
import { ChatDrawer } from "@/components/results/ChatDrawer";
import { ErrorState } from "@/components/shared/ErrorState";
import { ReportResult, ViewType } from "@/lib/types";

export default function ResultsPage() {
  const router = useRouter();
  const { isLoaded, isSignedIn } = useAuth();
  const [result, setResult] = useState<ReportResult | null>(null);
  const [view, setView] = useState<ViewType>("findings");
  const [chatOpen, setChatOpen] = useState(false);

  useEffect(() => {
    if (isLoaded && !isSignedIn) {
      router.replace("/");
      return;
    }
    const stored = sessionStorage.getItem("clar_result");
    if (!stored) {
      router.replace("/");
      return;
    }
    setResult(JSON.parse(stored));
  }, [isLoaded, isSignedIn, router]);

  if (!isLoaded || !result) {
    return (
      <div className="min-h-screen" style={{ backgroundColor: "#F5F7FA" }}>
        <NavBar showNewReport />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col" style={{ backgroundColor: "#F5F7FA" }}>
      <NavBar showNewReport />

      <div className="flex flex-1" style={{ minHeight: 0 }}>
        <Sidebar
          reportType={result.report_type}
          verdict={result.verdict}
          activeView={view}
          onViewChange={setView}
          onAskClar={() => setChatOpen(true)}
        />

        <main className="flex-1 overflow-y-auto p-6">
          {view === "findings" && (
            <>
              <VerdictBanner verdict={result.verdict} />
              <h3 className="text-base font-semibold mb-4" style={{ color: "#0F172A" }}>
                All Findings
              </h3>
              <FindingsList findings={result.findings} />
            </>
          )}
          {view === "urgency" && (
            <>
              <VerdictBanner verdict={result.verdict} />
              <h3 className="text-base font-semibold mb-4" style={{ color: "#0F172A" }}>
                Flagged Findings
              </h3>
              <FindingsList findings={result.findings} filterUrgency />
            </>
          )}
          {view === "questions" && (
            <QuestionList questions={result.questions} />
          )}

          <div className="mt-6 text-xs" style={{ color: "#9CA3AF" }}>
            Processed in {result.processing_time_ms}ms &nbsp;·&nbsp;{" "}
            {result.deid_entities_removed} personal detail(s) removed
          </div>
        </main>
      </div>

      <ChatDrawer
        reportId={result.report_id}
        open={chatOpen}
        onClose={() => setChatOpen(false)}
        starterQuestions={result.questions}
      />
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/pages/results.tsx
git commit -m "feat: results page — sidebar layout, three views, chat drawer integration"
```

---

## Task 9: Static Export Build + Verify

- [ ] **Step 1: Build static export**

```bash
cd frontend
npm run build
```

Expected: Build completes, output in `frontend/out/`. No TypeScript errors, no ESLint errors.

- [ ] **Step 2: Run TypeScript check**

```bash
npx tsc --noEmit
```

Expected: Zero errors.

- [ ] **Step 3: Copy static export to backend `static/` directory**

```bash
cp -r out/ ../static/
```

Then start the backend to verify it serves the frontend:

```bash
cd ..
uvicorn app.main:app --port 8000
```

Open `http://localhost:8000` — expected: CLAR upload screen loads.

- [ ] **Step 4: Full smoke test**

Walk through the full user journey manually:
1. `http://localhost:8000` → upload screen loads, IBM Plex Sans font, no emojis
2. Sign in via Clerk modal
3. Click "Try with a sample CBC report" → LoadingScreen appears with agent steps
4. Results screen: sidebar on left, findings on right, "Watch" verdict badge
5. Click "Urgency Summary" → shows only flagged findings
6. Click "Doctor Questions" → shows 5 questions
7. Click "Ask CLAR" → chat drawer slides in with starter chips
8. Type a question → answer appears
9. Click "+ New Report" → returns to upload screen

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: static export verified — frontend served by FastAPI, full smoke test passed"
```

---

## Task 10: Frontend Final Checks

- [ ] **Step 1: ESLint**

```bash
cd frontend
npx next lint
```

Expected: No errors. Fix any if found.

- [ ] **Step 2: TypeScript strict check**

```bash
npx tsc --noEmit --strict
```

Expected: Zero errors.

- [ ] **Step 3: Verify no hardcoded hex values in components**

```bash
grep -r "#[0-9A-Fa-f]\{6\}" components/ --include="*.tsx" | grep -v "tokens.ts"
```

Expected: Only `tokens.ts` should match. If any component has hardcoded hex, move the value to `tokens.ts` and import it.

- [ ] **Step 4: Verify no emojis in any file**

```bash
grep -rP "[\x{1F600}-\x{1F64F}]|[\x{1F300}-\x{1F5FF}]|[\x{1F680}-\x{1F6FF}]" \
  pages/ components/ lib/ styles/ --include="*.tsx" --include="*.ts"
```

Expected: Zero matches.

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "chore: frontend complete — lint, TypeScript, no emojis, no hardcoded hex"
```
