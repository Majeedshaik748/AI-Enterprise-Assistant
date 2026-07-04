"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { auth } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (mode === "register") {
        await auth.register(email, password, fullName);
      }
      const { data } = await auth.login(email, password);

console.log("LOGIN SUCCESS", data);

localStorage.setItem("access_token", data.access_token);
localStorage.setItem("refresh_token", data.refresh_token);

window.location.href = "/dashboard";
    { catch (err: any) {
  console.log("LOGIN ERROR:", err);
  console.log("RESPONSE:", err?.response?.data);

  setError(
    JSON.stringify(err?.response?.data) ||
    err?.message ||
    "Unknown error"
  );
} finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen grid grid-cols-1 md:grid-cols-2">
      {/* Left: brand panel */}
      <div className="hidden md:flex flex-col justify-between bg-[var(--ink)] text-white p-12">
        <div className="mono text-sm tracking-widest text-white/50">KNOWLEDGE ASSISTANT</div>
        <div>
          <h1 className="text-4xl font-semibold leading-tight mb-4">
            Every answer,<br />traced to its source.
          </h1>
          <p className="text-white/60 max-w-sm">
            Upload contracts, reports, and decks. Ask a question in plain
            language. Get an answer with the exact passage it came from.
          </p>
        </div>
        <div className="mono text-xs text-white/30">Backend: FastAPI · RAG · watsonx-ready</div>
      </div>

      {/* Right: form */}
      <div className="flex items-center justify-center p-8">
        <div className="w-full max-w-sm">
          <h2 className="text-2xl font-semibold mb-1">
            {mode === "login" ? "Sign in" : "Create your account"}
          </h2>
          <p className="text-black/50 text-sm mb-6">
            {mode === "login"
              ? "Access your organization's document index."
              : "The first account created becomes the workspace admin."}
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            {mode === "register" && (
              <div>
                <label className="text-xs font-medium text-black/60">Full name</label>
                <input
                  className="mt-1 w-full card px-3 py-2 text-sm outline-none focus:border-[var(--accent)]"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                />
              </div>
            )}
            <div>
              <label className="text-xs font-medium text-black/60">Work email</label>
              <input
                type="email"
                required
                className="mt-1 w-full card px-3 py-2 text-sm outline-none focus:border-[var(--accent)]"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div>
              <label className="text-xs font-medium text-black/60">Password</label>
              <input
                type="password"
                required
                minLength={8}
                className="mt-1 w-full card px-3 py-2 text-sm outline-none focus:border-[var(--accent)]"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>

            {error && <p className="text-sm text-[var(--danger)]">{error}</p>}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-[var(--ink)] text-white rounded-md py-2 text-sm font-medium hover:opacity-90 disabled:opacity-50"
            >
              {loading ? "Please wait…" : mode === "login" ? "Sign in" : "Create account"}
            </button>
          </form>

          <button
            className="mt-4 text-sm text-black/50 hover:text-black"
            onClick={() => setMode(mode === "login" ? "register" : "login")}
          >
            {mode === "login" ? "Need an account? Register" : "Already have an account? Sign in"}
          </button>
        </div>
      </div>
    </div>
  );
}
