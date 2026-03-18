"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { setToken, setUsername } from "@/lib/auth";

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({ username: "", email: "", password: "" });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    // Register
    const registerRes = await fetch(`${apiUrl}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    });

    if (!registerRes.ok) {
      const data = await registerRes.json();
      setError(data.detail || "Registration failed.");
      setLoading(false);
      return;
    }

    // Auto-login after register
    const loginRes = await fetch(`${apiUrl}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: new URLSearchParams({ username: form.username, password: form.password }),
    });

    if (loginRes.ok) {
      const data = await loginRes.json();
      setToken(data.access_token);
      setUsername(form.username);
      router.push("/vibe");
    } else {
      router.push("/login");
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
            Begin your archive.
          </h1>
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
            Track, tag, and discover anime through taste.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {["username", "email", "password"].map(field => (
            <div key={field} className="space-y-1">
              <label className="text-xs uppercase tracking-widest" style={{ color: "var(--text-muted)" }}>
                {field}
              </label>
              <input
                type={field === "password" ? "password" : field === "email" ? "email" : "text"}
                value={form[field as keyof typeof form]}
                onChange={e => setForm(f => ({ ...f, [field]: e.target.value }))}
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
          ))}

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
            {loading ? "Creating account..." : "Create account"}
          </button>
        </form>

        <p className="text-sm text-center" style={{ color: "var(--text-muted)" }}>
          Already have an account?{" "}
          <Link href="/login" style={{ color: "var(--pill-text)" }}>
            Sign in
          </Link>
        </p>
      </div>
    </main>
  );
}