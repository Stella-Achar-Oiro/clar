import React from "react";
import { ViewType } from "@/lib/types";

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

interface SidebarNavProps {
  activeView: ViewType;
  onViewChange: (v: ViewType) => void;
  onClose: () => void;
}

export function SidebarNav({ activeView, onViewChange, onClose }: SidebarNavProps) {
  return (
    <nav style={{ padding: "0 0.5rem", flex: 1 }}>
      <div className="text-xs font-semibold uppercase tracking-widest px-2 mb-1" style={{ color: "#6B7280" }}>
        View
      </div>
      {NAV_ITEMS.map(({ view, label, icon }) => (
        <button
          key={view}
          onClick={() => { onViewChange(view); onClose(); }}
          className="w-full flex items-center gap-2 px-2 py-2 rounded-md text-sm mb-0.5 font-medium transition-colors"
          style={
            activeView === view
              ? { backgroundColor: "#E05A00", color: "#FFFFFF" }
              : { color: "#6B7280" }
          }
        >
          {icon}
          {label}
        </button>
      ))}
    </nav>
  );
}
