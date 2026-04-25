import { ViewType, Verdict } from "@/lib/types";
import { urgencyColors } from "@/styles/tokens";
import { SidebarNav } from "./SidebarNav";

interface SidebarProps {
  reportType?: string;
  verdict?: Verdict;
  activeView: ViewType;
  onViewChange: (v: ViewType) => void;
  onAskClar: () => void;
  hasReport: boolean;
  open: boolean;
  onClose: () => void;
}

function SidebarContent({
  reportType, verdict, activeView, onViewChange, onAskClar, hasReport, onClose,
}: Omit<SidebarProps, "open">) {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: "#F5F7FA" }}>
      {!hasReport ? (
        <div className="flex flex-col items-center justify-center flex-1 px-4 text-center">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#CBD5E1" strokeWidth="1.5" className="mb-3">
            <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
            <polyline points="14 2 14 8 20 8" />
          </svg>
          <p className="text-xs leading-snug" style={{ color: "#9CA3AF" }}>
            Upload a report to see your results here
          </p>
        </div>
      ) : (
        <>
          <div style={{ padding: "1rem", borderBottom: "1px solid #E0E0E0" }}>
            <div className="text-xs font-semibold uppercase tracking-widest mb-1" style={{ color: "#6B7280" }}>
              Report
            </div>
            <div className="font-semibold text-sm" style={{ color: "#0F172A" }}>
              {reportType
                ? reportType.charAt(0).toUpperCase() + reportType.slice(1) + " Results"
                : "Results"}
            </div>
          </div>

          {verdict && (
            <div style={{ margin: "0.75rem 1rem" }}>
              <div
                className="rounded px-3 py-2"
                style={{
                  backgroundColor: urgencyColors[verdict.level].bg,
                  borderLeft: `3px solid ${urgencyColors[verdict.level].border}`,
                }}
              >
                <div
                  className="text-xs font-bold uppercase tracking-wide"
                  style={{ color: urgencyColors[verdict.level].text }}
                >
                  {verdict.level}
                </div>
                <div className="text-xs mt-0.5 leading-snug" style={{ color: "#0F172A" }}>
                  {verdict.summary}
                </div>
              </div>
            </div>
          )}

          <SidebarNav activeView={activeView} onViewChange={onViewChange} onClose={onClose} />

          <div style={{ padding: "1rem", borderTop: "1px solid #E0E0E0" }}>
            <button
              onClick={() => { onAskClar(); onClose(); }}
              className="w-full flex items-center justify-center gap-2 text-sm font-semibold py-2.5 rounded-lg text-white transition-opacity hover:opacity-90"
              style={{ backgroundColor: "#E05A00" }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
              </svg>
              Ask CLAR
            </button>
          </div>
        </>
      )}
    </div>
  );
}

export function Sidebar(props: SidebarProps) {
  const { open, onClose, ...rest } = props;
  return (
    <>
      {open && (
        <div
          className="fixed inset-0 z-40 md:hidden"
          style={{ backgroundColor: "rgba(0,0,0,0.4)" }}
          onClick={onClose}
        />
      )}
      <div
        className="fixed top-0 left-0 h-full z-50 md:hidden transition-transform duration-200"
        style={{ width: 260, transform: open ? "translateX(0)" : "translateX(-100%)", borderRight: "1px solid #E0E0E0" }}
      >
        <SidebarContent {...rest} onClose={onClose} />
      </div>
      <aside
        className="hidden md:flex flex-col flex-shrink-0"
        style={{ width: 220, borderRight: "1px solid #E0E0E0" }}
      >
        <SidebarContent {...rest} onClose={() => {}} />
      </aside>
    </>
  );
}
