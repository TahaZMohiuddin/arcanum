"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { getToken, getUsername } from "@/lib/auth";

interface ImportResult {
  imported: number;
  skipped: number;
  unmatched_count: number;
  unmatched_titles: string[];
  total_in_file: number;
}

type ImportMethod = "mal" | "anilist";

export default function ImportPage() {
  const router = useRouter();
  const [method, setMethod] = useState<ImportMethod>("anilist");
  const [file, setFile] = useState<File | null>(null);
  const [anilistUsername, setAnilistUsername] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    const token = getToken();
    if (!token) {
      router.push("/login");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    try {
      let res: Response;

      if (method === "mal") {
        if (!file) return;
        if (file.size > 5 * 1024 * 1024) {
          setError("File too large. MAL exports are typically under 1MB.");
          setLoading(false);
          return;
        }
        const formData = new FormData();
        formData.append("file", file);
        res = await fetch(`${apiUrl}/import/mal`, {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
          body: formData,
        });
      } else {
        if (!anilistUsername.trim()) return;
        res = await fetch(`${apiUrl}/import/anilist`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ username: anilistUsername.trim() }),
        });
      }

      if (res.ok) {
        const data = await res.json();
        setResult(data);
      } else {
        const data = await res.json();
        setError(data.detail || "Import failed. Please try again.");
      }
    } catch {
      setError("Network error. Check your connection and try again.");
    }
    setLoading(false);
  };

  const canSubmit = method === "mal" ? !!file : !!anilistUsername.trim();

  return (
    <main className="page-gradient min-h-screen pt-8">
      <div className="page-container py-12" style={{ maxWidth: "640px" }}>
        <div className="space-y-2 mb-10">
          <h1
            className="text-4xl"
            style={{
              fontFamily: "var(--font-dm-serif), serif",
              color: "var(--text-primary)",
            }}
          >
            Bring your list.
          </h1>
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
            Your watch history arrives instantly.
          </p>
        </div>

        {/* Method toggle */}
        <div
          className="flex rounded-lg p-1 mb-8"
          style={{ background: "var(--bg-card)" }}
        >
          {(["anilist", "mal"] as ImportMethod[]).map(m => (
            <button
              key={m}
              onClick={() => { setMethod(m); setResult(null); setError(null); }}
              className="flex-1 py-2 rounded-md text-sm font-medium transition-all"
              style={{
                background: method === m ? "var(--accent-purple)" : "transparent",
                color: method === m ? "var(--text-primary)" : "var(--text-secondary)",
              }}
            >
              {m === "anilist" ? "AniList" : "MyAnimeList"}
            </button>
          ))}
        </div>

        {/* AniList method */}
        {method === "anilist" && (
          <div className="space-y-4">
            <div
              className="rounded-xl p-5 space-y-2"
              style={{
                background: "var(--bg-card)",
                border: "1px solid rgba(74, 69, 96, 0.3)",
              }}
            >
              <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                Import directly from AniList
              </p>
              <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
                Enter your AniList username and we'll fetch your list automatically.
                No export file needed.
              </p>
            </div>
            <div className="space-y-1">
              <label className="text-xs uppercase tracking-widest" style={{ color: "var(--text-muted)" }}>
                AniList Username
              </label>
              <input
                type="text"
                value={anilistUsername}
                onChange={e => setAnilistUsername(e.target.value)}
                placeholder="your_username"
                className="w-full px-4 py-3 rounded-lg text-sm outline-none"
                style={{
                  background: "var(--bg-card)",
                  border: "1px solid var(--text-muted)",
                  color: "var(--text-primary)",
                }}
                onFocus={e => e.target.style.borderColor = "var(--accent-purple)"}
                onBlur={e => e.target.style.borderColor = "var(--text-muted)"}
              />
            </div>
          </div>
        )}

        {/* MAL method */}
        {method === "mal" && (
          <div className="space-y-4">
            <div
              className="rounded-xl p-5 space-y-2"
              style={{
                background: "var(--bg-card)",
                border: "1px solid rgba(74, 69, 96, 0.3)",
              }}
            >
              <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                How to export from MAL:
              </p>
              <ol className="space-y-1 text-sm" style={{ color: "var(--text-secondary)" }}>
                <li>1. Go to myanimelist.net → Profile → Export</li>
                <li>2. Click "Export My Anime List"</li>
                <li>3. Download the XML file</li>
                <li>4. Upload it below</li>
              </ol>
            </div>
            <div
              className="rounded-xl p-8 text-center cursor-pointer transition-colors"
              style={{
                background: "var(--bg-card)",
                border: `2px dashed ${file ? "var(--accent-purple)" : "rgba(74, 69, 96, 0.4)"}`,
              }}
              onClick={() => document.getElementById("file-input")?.click()}
            >
              <input
                id="file-input"
                type="file"
                accept=".xml"
                className="hidden"
                onChange={e => setFile(e.target.files?.[0] || null)}
              />
              {file ? (
                <div className="space-y-1">
                  <p className="text-sm font-medium" style={{ color: "var(--pill-text)" }}>
                    {file.name}
                  </p>
                  <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                    {(file.size / 1024).toFixed(1)} KB — click to change
                  </p>
                </div>
              ) : (
                <div className="space-y-2">
                  <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
                    Click to select your MAL XML export
                  </p>
                  <p className="text-xs" style={{ color: "var(--text-muted)" }}>.xml files only</p>
                </div>
              )}
            </div>
          </div>
        )}

        <button
          onClick={handleSubmit}
          disabled={!canSubmit || loading}
          className="w-full py-3 rounded-lg text-sm font-semibold transition-opacity hover:opacity-90 disabled:opacity-40 mt-6"
          style={{
            background: "var(--accent-purple)",
            color: "var(--text-primary)",
          }}
        >
          {loading ? "Importing..." : `Import from ${method === "anilist" ? "AniList" : "MAL"}`}
        </button>

        {/* Error */}
        {error && (
          <div
            className="mt-6 rounded-xl p-4"
            style={{
              background: "rgba(239,68,68,0.1)",
              border: "1px solid rgba(239,68,68,0.3)",
            }}
          >
            <p className="text-sm" style={{ color: "#ef4444" }}>{error}</p>
          </div>
        )}

        {/* Result */}
        {result && (
          <div
            className="mt-6 rounded-xl p-6 space-y-4"
            style={{
              background: "var(--bg-card)",
              border: "1px solid rgba(74, 69, 96, 0.3)",
            }}
          >
            <h2
              className="text-xl"
              style={{
                fontFamily: "var(--font-dm-serif), serif",
                color: "var(--text-primary)",
              }}
            >
              Import complete.
            </h2>
            <div className="grid grid-cols-3 gap-4">
              {[
                { label: "Imported", value: result.imported, color: "var(--pill-text)" },
                { label: "Already in list", value: result.skipped, color: "var(--text-secondary)" },
                { label: "Not found", value: result.unmatched_count, color: "var(--text-muted)" },
              ].map(stat => (
                <div key={stat.label} className="text-center space-y-1">
                  <p className="text-2xl font-bold" style={{ color: stat.color }}>
                    {stat.value}
                  </p>
                  <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                    {stat.label}
                  </p>
                </div>
              ))}
            </div>
            {result.unmatched_count > 0 && (
              <div className="space-y-2">
                <p className="text-xs uppercase tracking-widest" style={{ color: "var(--text-muted)" }}>
                  Not in Arcanum yet
                </p>
                <div className="flex flex-wrap gap-2">
                  {result.unmatched_titles.map(title => (
                    <span
                      key={title}
                      className="text-xs px-2 py-1 rounded"
                      style={{
                        background: "var(--bg-secondary)",
                        color: "var(--text-muted)",
                      }}
                    >
                      {title}
                    </span>
                  ))}
                </div>
                {result.unmatched_count > 20 && (
                  <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                    +{result.unmatched_count - 20} more not shown
                  </p>
                )}
              </div>
            )}
            <div className="flex gap-6">
              <button
                onClick={() => router.push("/vibe")}
                className="text-sm transition-colors"
                style={{ color: "var(--pill-text)" }}
              >
                Start browsing →
              </button>
              <button
                onClick={() => router.push(`/profile/${getUsername()}`)}
                className="text-sm transition-colors"
                style={{ color: "var(--text-secondary)" }}
              >
                View your list →
              </button>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}