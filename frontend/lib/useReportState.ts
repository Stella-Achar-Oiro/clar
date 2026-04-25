import { useState } from "react";
import { uploadReport } from "@/lib/api";
import { ReportResult, ViewType } from "@/lib/types";

type AppState = "idle" | "uploading" | "error" | "results";

export function useReportState() {
  const [appState, setAppState] = useState<AppState>("idle");
  const [result, setResult] = useState<ReportResult | null>(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [step, setStep] = useState(0);
  const [view, setView] = useState<ViewType>("findings");

  async function handleFile(file: File) {
    setAppState("uploading");
    setStep(0);
    const timer = setInterval(() => setStep((s) => Math.min(s + 1, 4)), 1200);
    try {
      const data = await uploadReport(file);
      clearInterval(timer);
      setResult(data);
      setView("findings");
      setAppState("results");
    } catch (err) {
      clearInterval(timer);
      setErrorMessage(err instanceof Error ? err.message : "Upload failed. Please try again.");
      setAppState("error");
    }
  }

  function handleNewReport() {
    setResult(null);
    setAppState("idle");
    setStep(0);
  }

  return { appState, setAppState, result, errorMessage, step, view, setView, handleFile, handleNewReport };
}
