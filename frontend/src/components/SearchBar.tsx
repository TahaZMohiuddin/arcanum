"use client";
import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";

interface SearchResult {
  id: string;
  title: string;
  title_english: string | null;
  cover_url: string | null;
  average_score: number | null;
}

// TODO: Add responsive behavior — search bar overflows on mobile narrow viewports
// TODO Phase 5: Replace /anime/search endpoint with pgvector semantic search
export default function SearchBar() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

useEffect(() => {
  if (query.length < 2) {
    setResults([]);
    setOpen(false);
    return;
  }

  const timeout = setTimeout(async () => {
    setLoading(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/anime/search?q=${encodeURIComponent(query)}`);
      if (res.ok) {
        const data = await res.json();
        setResults(data);
        setOpen(true);
      }
    } catch {
      // Silently fail — search is non-critical
    }
    setLoading(false);
  }, 300);

  return () => clearTimeout(timeout);
}, [query]);

  // Close on outside click
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const handleSelect = (id: string) => {
    setQuery("");
    setOpen(false);
    router.push(`/anime/${id}`);
  };

  return (
    <div ref={containerRef} className="relative">
      <input
        type="text"
        value={query}
        onChange={e => setQuery(e.target.value)}
        placeholder="Search anime..."
        className="text-sm px-3 py-1.5 rounded-lg outline-none w-48 transition-all focus:w-64"
        style={{
          background: "var(--bg-card)",
          border: "1px solid var(--text-muted)",
          color: "var(--text-primary)",
        }}
        onFocus={e => e.currentTarget.style.borderColor = "var(--accent-purple)"}
        onBlur={e => e.currentTarget.style.borderColor = "var(--text-muted)"}
      />

      {/* Dropdown results */}
      {open && results.length > 0 && (
        <div
          className="absolute top-full mt-1 right-0 w-72 rounded-xl overflow-hidden z-50 shadow-xl"
          style={{
            background: "var(--bg-secondary)",
            border: "1px solid rgba(74, 69, 96, 0.3)",
          }}
        >
          {results.map(anime => (
            <button
              key={anime.id}
              onClick={() => handleSelect(anime.id)}
              className="w-full flex items-center gap-3 px-3 py-2 text-left transition-colors hover:bg-white/5"
            >
              {anime.cover_url && (
                <div className="relative w-8 h-12 flex-shrink-0 rounded overflow-hidden">
                  <Image
                    src={anime.cover_url}
                    alt={anime.title}
                    fill
                    className="object-cover"
                    sizes="32px"
                  />
                </div>
              )}
              <div className="flex-1 min-w-0">
                <p className="text-sm truncate" style={{ color: "var(--text-primary)" }}>
                  {anime.title_english || anime.title}
                </p>
                {anime.title_english && (
                  <p className="text-xs truncate" style={{ color: "var(--text-muted)" }}>
                    {anime.title}
                  </p>
                )}
              </div>
              {anime.average_score && (
                <span className="text-xs flex-shrink-0" style={{ color: "var(--pill-text)" }}>
                  {anime.average_score}
                </span>
              )}
            </button>
          ))}
        </div>
      )}

      {loading && (
        <div
          className="absolute top-full mt-1 right-0 w-72 rounded-xl px-4 py-3 text-sm"
          style={{
            background: "var(--bg-secondary)",
            border: "1px solid rgba(74, 69, 96, 0.3)",
            color: "var(--text-muted)",
          }}
        >
          Searching...
        </div>
      )}
    </div>
  );
}