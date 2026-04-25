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
          <h1 className="text-3xl font-bold mb-3" style={{ color: "#E05A00" }}>
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
                style={{ backgroundColor: "#E05A00" }}
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
