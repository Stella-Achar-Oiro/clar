import { useState } from "react";
import { Finding } from "@/lib/types";

interface Message { role: "user" | "assistant"; text: string; }

const BASE = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

export function useChatStream(reportId: string, reportType: string, findings: Finding[], starterQuestions: string[]) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [streaming, setStreaming] = useState(false);

  async function send(text: string) {
    if (!text.trim() || streaming) return;
    const question = text.trim();
    setMessages((prev) => [...prev, { role: "user", text: question }, { role: "assistant", text: "" }]);
    setStreaming(true);

    try {
      const res = await fetch(`${BASE}/api/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          report_id: reportId,
          question,
          report_type: reportType,
          findings: findings.map((f) => ({
            name: f.name, value: f.value, reference_range: f.reference_range,
            urgency: f.urgency, explanation: f.explanation,
          })),
          questions: starterQuestions,
        }),
      });
      if (!res.ok || !res.body) throw new Error("Stream failed");

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";
        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const chunk = line.slice(6);
          if (chunk === "[DONE]" || chunk === "[ERROR]") break;
          setMessages((prev) => {
            const next = [...prev];
            next[next.length - 1] = { role: "assistant", text: next[next.length - 1].text + chunk };
            return next;
          });
        }
      }
    } catch {
      setMessages((prev) => {
        const next = [...prev];
        next[next.length - 1] = { role: "assistant", text: "Sorry, I couldn't answer that. Please try again." };
        return next;
      });
    } finally {
      setStreaming(false);
    }
  }

  return { messages, streaming, send };
}
