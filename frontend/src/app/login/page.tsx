"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { setToken, setUsername } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [form, setForm] = useState({ username: "", password: "" });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const res = await fetch(`${apiUrl}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ username: form.username, password: form.password, }),
    });

    if (res.ok) {
      const data = await res.json();
      setToken(data.access_token);
      setUsername(form.username);
      router.push("/vibe");
    } else {
      setError("Invalid username or password.");
    }
    setLoading(false);
  };

  return (
    <main className="page-gradient min-h-screen flex items-center justify-center">
      <div className="w-full max-w-sm space-y-8 px-6">
        <div className="space-y-2">
          <h1
            className="text-4xl"
            style={{
              fontFamily: "var(--font-dm-serif), serif",
              color: "var(--text-primary)",
            }}
          >
            Welcome back.
          </h1>
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
            Your taste fingerprint awaits.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1">
            <label className="text-xs uppercase tracking-widest" style={{ color: "var(--text-muted)" }}>
              Username
            </label>
            <input
              type="text"
              value={form.username}
              onChange={e => setForm(f => ({ ...f, username: e.target.value }))}
              required
              className="w-full px-4 py-3 rounded-lg text-sm outline-none transition-colors"
              style={{
                background: "var(--bg-card)",
                border: "1px solid var(--text-muted)",
                color: "var(--text-primary)",
              }}
              onFocus={e => e.target.style.borderColor = "var(--accent-purple)"}
              onBlur={e => e.target.style.borderColor = "var(--text-muted)"}
            />
          </div>

          <div className="space-y-1">
            <label className="text-xs uppercase tracking-widest" style={{ color: "var(--text-muted)" }}>
              Password
            </label>
            <input
              type="password"
              value={form.password}
              onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
              required
              className="w-full px-4 py-3 rounded-lg text-sm outline-none transition-colors"
              style={{
                background: "var(--bg-card)",
                border: "1px solid var(--text-muted)",
                color: "var(--text-primary)",
              }}
              onFocus={e => e.target.style.borderColor = "var(--accent-purple)"}
              onBlur={e => e.target.style.borderColor = "var(--text-muted)"}
            />
          </div>

          {error && (
            <p className="text-sm" style={{ color: "#ef4444" }}>{error}</p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-lg text-sm font-semibold transition-opacity hover:opacity-90 disabled:opacity-50"
            style={{
              background: "var(--accent-purple)",
              color: "var(--text-primary)",
            }}
          >
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>

        <p className="text-sm text-center" style={{ color: "var(--text-muted)" }}>
          No account?{" "}
          <Link href="/register" style={{ color: "var(--pill-text)" }}>
            Register
          </Link>
        </p>
      </div>
    </main>
  );
}