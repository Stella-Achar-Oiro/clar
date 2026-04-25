import { useState } from "react";
import { SignedIn, SignedOut, SignInButton } from "@clerk/nextjs";
import { NavBar } from "@/components/shared/NavBar";
import { Disclaimer } from "@/components/shared/Disclaimer";
import { LoadingScreen } from "@/components/shared/LoadingScreen";
import { ErrorState } from "@/components/shared/ErrorState";
import { Sidebar } from "@/components/results/Sidebar";
import { FindingsList } from "@/components/results/FindingsList";
import { VerdictBanner } from "@/components/results/VerdictBanner";
import { QuestionList } from "@/components/results/QuestionList";
import { ChatDrawer } from "@/components/results/ChatDrawer";
import { UploadPanel } from "@/components/upload/UploadPanel";
import { TrustBadges } from "@/components/upload/TrustBadges";
import { useReportState } from "@/lib/useReportState";

export default function IndexPage() {
  const { appState, setAppState, result, errorMessage, step, view, setView, handleFile, handleNewReport } = useReportState();
  const [chatOpen, setChatOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen flex flex-col" style={{ backgroundColor: "#F5F7FA" }}>
      <NavBar
        onNewReport={appState === "results" ? handleNewReport : undefined}
        onMenuToggle={() => setSidebarOpen((o) => !o)}
        menuOpen={sidebarOpen}
      />

      <SignedOut>
        <div className="flex flex-1 items-center justify-center px-4">
          <div
            className="rounded-xl p-8 text-center w-full"
            style={{ backgroundColor: "#FFFFFF", border: "1px solid #E0E0E0", maxWidth: 420 }}
          >
            <h1 className="text-2xl font-bold mb-2" style={{ color: "#E05A00" }}>
              Understand your medical report
            </h1>
            <p className="text-sm mb-6" style={{ color: "#6B7280" }}>
              Upload a lab result, radiology report, or discharge summary. CLAR explains it in plain English.
            </p>
            <SignInButton mode="modal">
              <button
                className="px-6 py-2.5 rounded-lg text-white font-semibold text-sm"
                style={{ backgroundColor: "#E05A00" }}
              >
                Sign in to get started
              </button>
            </SignInButton>
            <TrustBadges />
          </div>
        </div>
      </SignedOut>

      <SignedIn>
        <div className="flex flex-1" style={{ minHeight: 0 }}>
          <Sidebar
            reportType={result?.report_type}
            verdict={result?.verdict}
            activeView={view}
            onViewChange={setView}
            onAskClar={() => setChatOpen(true)}
            hasReport={appState === "results"}
            open={sidebarOpen}
            onClose={() => setSidebarOpen(false)}
          />
          <main className="flex-1 overflow-y-auto">
            {appState === "idle" && <UploadPanel onFile={handleFile} />}
            {appState === "uploading" && (
              <div className="flex items-center justify-center h-full min-h-96">
                <LoadingScreen currentStep={step} />
              </div>
            )}
            {appState === "error" && (
              <div className="max-w-xl mx-auto px-4 py-16">
                <ErrorState message={errorMessage} onRetry={() => setAppState("idle")} />
              </div>
            )}
            {appState === "results" && result && (
              <div className="p-6">
                {view === "findings" && (
                  <>
                    <VerdictBanner verdict={result.verdict} />
                    <h3 className="text-base font-semibold mb-4" style={{ color: "#0F172A" }}>All Findings</h3>
                    <FindingsList findings={result.findings} />
                  </>
                )}
                {view === "urgency" && (
                  <>
                    <VerdictBanner verdict={result.verdict} />
                    <h3 className="text-base font-semibold mb-4" style={{ color: "#0F172A" }}>Flagged Findings</h3>
                    <FindingsList findings={result.findings} filterUrgency />
                  </>
                )}
                {view === "questions" && <QuestionList questions={result.questions} />}
                <div className="mt-6 text-xs" style={{ color: "#9CA3AF" }}>
                  Processed in {result.processing_time_ms}ms &nbsp;&middot;&nbsp;{" "}
                  {result.deid_entities_removed} personal detail(s) removed
                </div>
                <Disclaimer />
              </div>
            )}
          </main>
        </div>
        {result && (
          <ChatDrawer
            reportId={result.report_id}
            open={chatOpen}
            onClose={() => setChatOpen(false)}
            starterQuestions={result.questions}
          />
        )}
      </SignedIn>
    </div>
  );
}
