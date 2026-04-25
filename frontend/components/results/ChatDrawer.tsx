import { useState, useRef, useEffect } from "react";
import { colors } from "@/styles/tokens";
import { ChatMessage } from "./ChatMessage";

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

const BASE = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

export function ChatDrawer({ reportId, open, onClose, starterQuestions }: ChatDrawerProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 50);
  }, [open]);

  async function handleSend(text: string) {
    if (!text.trim() || streaming) return;
    const question = text.trim();
    setMessages((prev) => [...prev, { role: "user", text: question }]);
    setInput("");
    setStreaming(true);
    setMessages((prev) => [...prev, { role: "assistant", text: "" }]);

    try {
      const res = await fetch(`${BASE}/api/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ report_id: reportId, question }),
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

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 flex items-end sm:items-center justify-center z-50"
      style={{ backgroundColor: "rgba(0,0,0,0.4)" }}
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div
        className="flex flex-col w-full rounded-t-xl sm:rounded-xl shadow-2xl overflow-hidden"
        style={{ maxWidth: 680, height: "90vh", maxHeight: "90vh", backgroundColor: colors.white, border: `1px solid ${colors.border}` }}
      >
        <div
          className="flex items-center justify-between px-5 py-3 flex-shrink-0"
          style={{ borderBottom: `1px solid ${colors.border}`, backgroundColor: colors.navy }}
        >
          <span className="font-semibold text-sm" style={{ color: colors.white }}>Ask CLAR</span>
          <button onClick={onClose} style={{ color: colors.white, opacity: 0.7 }} className="hover:opacity-100 transition-opacity" aria-label="Close">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4" style={{ minHeight: 0 }}>
          {messages.length === 0 && (
            <div>
              <p className="text-sm mb-3" style={{ color: colors.textSecondary }}>
                Ask a question about your report, or try one of these:
              </p>
              <div className="space-y-2">
                {starterQuestions.slice(0, 3).map((q) => (
                  <button key={q} onClick={() => handleSend(q)}
                    className="w-full text-left text-xs px-3 py-2 rounded-lg border transition-colors hover:bg-blue-50"
                    style={{ borderColor: colors.border, color: colors.textPrimary }}
                  >{q}</button>
                ))}
              </div>
            </div>
          )}
          {messages.map((msg, i) => <ChatMessage key={i} role={msg.role} text={msg.text} />)}
          {streaming && messages[messages.length - 1]?.text === "" && (
            <div className="flex justify-start">
              <div className="text-sm px-4 py-3 rounded-xl animate-pulse" style={{ backgroundColor: colors.surface, color: colors.textSecondary }}>
                Thinking...
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <div className="flex gap-2 px-5 py-3 flex-shrink-0" style={{ borderTop: `1px solid ${colors.border}` }}>
          <input ref={inputRef} type="text" value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend(input)}
            placeholder="Ask about your results..." disabled={streaming}
            className="flex-1 text-sm px-3 py-2 rounded-lg border outline-none"
            style={{ borderColor: "#CBD5E1", color: colors.textPrimary }}
          />
          <button onClick={() => handleSend(input)} disabled={streaming || !input.trim()} aria-label="Send"
            className="px-3 py-2 rounded-lg text-white disabled:opacity-50 transition-opacity" style={{ backgroundColor: colors.blue }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
          </button>
        </div>
      </div>
    </div>
  );
}
