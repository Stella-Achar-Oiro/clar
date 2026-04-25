import { useState, useRef, useEffect } from "react";
import { sendChatMessage } from "@/lib/api";

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

export function ChatDrawer({ reportId, open, onClose, starterQuestions }: ChatDrawerProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend(text: string) {
    if (!text.trim() || loading) return;
    setMessages((prev) => [...prev, { role: "user", text }]);
    setInput("");
    setLoading(true);
    try {
      const res = await sendChatMessage(reportId, text);
      setMessages((prev) => [...prev, { role: "assistant", text: res.answer }]);
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", text: "Sorry, I couldn't answer that. Please try again." }]);
    } finally {
      setLoading(false);
    }
  }

  if (!open) return null;

  const chips = starterQuestions.slice(0, 3);

  return (
    <div
      className="fixed inset-y-0 right-0 flex flex-col shadow-2xl z-50"
      style={{ width: 380, backgroundColor: "#FFFFFF", borderLeft: "1px solid #E0E0E0" }}
    >
      <div
        className="flex items-center justify-between px-4 py-3"
        style={{ borderBottom: "1px solid #E0E0E0", backgroundColor: "#1B2A4A" }}
      >
        <span className="text-white font-semibold text-sm">Ask CLAR</span>
        <button onClick={onClose} className="text-white opacity-70 hover:opacity-100 transition-opacity">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.length === 0 && (
          <div>
            <p className="text-sm mb-3" style={{ color: "#6B7280" }}>
              Ask a question about your report, or try one of these:
            </p>
            <div className="space-y-2">
              {chips.map((q) => (
                <button
                  key={q}
                  onClick={() => handleSend(q)}
                  className="w-full text-left text-xs px-3 py-2 rounded-lg border transition-colors hover:bg-blue-50"
                  style={{ borderColor: "#E0E0E0", color: "#0F172A" }}
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`text-sm px-3 py-2.5 rounded-lg max-w-xs ${
              msg.role === "user" ? "ml-auto" : "mr-auto"
            }`}
            style={
              msg.role === "user"
                ? { backgroundColor: "#2563EB", color: "#FFFFFF" }
                : { backgroundColor: "#F5F7FA", color: "#0F172A" }
            }
          >
            {msg.text}
          </div>
        ))}
        {loading && (
          <div
            className="mr-auto text-sm px-3 py-2.5 rounded-lg"
            style={{ backgroundColor: "#F5F7FA", color: "#6B7280" }}
          >
            Thinking...
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div
        className="flex gap-2 p-3"
        style={{ borderTop: "1px solid #E0E0E0" }}
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend(input)}
          placeholder="Ask about your results..."
          className="flex-1 text-sm px-3 py-2 rounded-lg border outline-none"
          style={{ borderColor: "#CBD5E1", color: "#0F172A" }}
          disabled={loading}
        />
        <button
          onClick={() => handleSend(input)}
          disabled={loading || !input.trim()}
          className="px-3 py-2 rounded-lg text-white font-semibold text-sm disabled:opacity-50 transition-opacity"
          style={{ backgroundColor: "#2563EB" }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="22" y1="2" x2="11" y2="13" />
            <polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>
        </button>
      </div>
    </div>
  );
}
