import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import { useAuth } from "@clerk/nextjs";
import { NavBar } from "@/components/shared/NavBar";
import { Sidebar } from "@/components/results/Sidebar";
import { FindingsList } from "@/components/results/FindingsList";
import { VerdictBanner } from "@/components/results/VerdictBanner";
import { QuestionList } from "@/components/results/QuestionList";
import { ChatDrawer } from "@/components/results/ChatDrawer";
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
            Processed in {result.processing_time_ms}ms &nbsp;&middot;&nbsp;{" "}
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
