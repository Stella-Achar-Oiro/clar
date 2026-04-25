import React from "react";
import { ViewType, Verdict } from "@/lib/types";
import { urgencyColors } from "@/styles/tokens";

interface SidebarProps {
  reportType: string;
  verdict: Verdict;
  activeView: ViewType;
  onViewChange: (v: ViewType) => void;
  onAskClar: () => void;
}

const NAV_ITEMS: { view: ViewType; label: string; icon: React.ReactElement }[] = [
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
