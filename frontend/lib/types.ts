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
