"use client";

import { useState } from "react";
import Sidebar from "@/components/Sidebar";
import { rag, SourceCitation } from "@/lib/api";

interface Turn {
  question: string;
  answer: string;
  sources: SourceCitation[];
}

export default function ChatPage() {
  const [question, setQuestion] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function ask(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const { data } = await rag.query(question);
      setTurns((t) => [...t, { question, answer: data.answer, sources: data.sources }]);
      setQuestion("");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Could not get an answer. Try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 p-8 max-w-3xl flex flex-col h-screen">
        <h1 className="text-2xl font-semibold mb-1">Ask your documents</h1>
        <p className="text-black/50 text-sm mb-6">
          Answers are grounded in your uploaded files, with the source passage cited.
        </p>

        <div className="flex-1 overflow-y-auto space-y-6 mb-4">
          {turns.length === 0 && (
            <p className="text-sm text-black/40">
              Try: “What are the payment terms in the vendor contract?”
            </p>
          )}
          {turns.map((turn, i) => (
            <div key={i} className="space-y-2">
              <p className="text-sm font-medium">{turn.question}</p>
              <div className="card p-4 text-sm leading-relaxed">{turn.answer}</div>
              {turn.sources.length > 0 && (
                <div className="space-y-1">
                  {turn.sources.map((s, j) => (
                    <div key={j} className="mono text-xs text-black/50 flex gap-2">
                      <span className="text-[var(--accent)]">[{j + 1}]</span>
                      <span>
                        {s.filename} · chunk {s.chunk_index} · score {s.score}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>

        {error && <p className="text-sm text-[var(--danger)] mb-2">{error}</p>}

        <form onSubmit={ask} className="flex gap-2">
          <input
            className="flex-1 card px-4 py-3 text-sm outline-none focus:border-[var(--accent)]"
            placeholder="Ask a question about your documents…"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
          />
          <button
            type="submit"
            disabled={loading}
            className="bg-[var(--ink)] text-white px-5 rounded-md text-sm font-medium disabled:opacity-50"
          >
            {loading ? "Thinking…" : "Ask"}
          </button>
        </form>
      </main>
    </div>
  );
}
