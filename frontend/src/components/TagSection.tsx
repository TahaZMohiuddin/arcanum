"use client";
import { useState } from "react";
import { TagResponse } from "@/lib/types";

interface Props {
  confirmed: TagResponse[];
  suggested: TagResponse[];
  animeId: string;
  token?: string;
}

export default function TagSection({ confirmed, suggested, animeId, token }: Props) {
  const [localConfirmed, setLocalConfirmed] = useState(confirmed);
  const [localSuggested, setLocalSuggested] = useState(suggested);
  const [applying, setApplying] = useState<string | null>(null);
  const applyTag = async (tagId: string) => {
    if (!token) return; // User must be logged in to vote
    setApplying(tagId); // Show loading state on the clicked tag
  
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const res = await fetch(`${apiUrl}/anime/${animeId}/tags`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ tag_id: tagId }),
  });

  if (res.ok) {
    // Optimistic UI — update local state immediately without refetching from server.
    // This makes the interaction feel instant rather than waiting for a round trip.
    const existingConfirmed = localConfirmed.find(t => t.id === tagId);
    if (existingConfirmed) {
      // Tag already confirmed — user is adding another vote, increment the count
      setLocalConfirmed(prev =>
        prev.map(t => t.id === tagId ? { ...t, vote_count: t.vote_count + 1 } : t)
      );
    } else {
      // Tag was in suggested — move it to confirmed with vote_count: 1
      // Note: this is optimistic. Real confirmation threshold is 3 votes on the backend.
      // The tag will correctly re-sort on next page load.
      const tag = localSuggested.find(t => t.id === tagId);
      if (tag) {
        setLocalSuggested(prev => prev.filter(t => t.id !== tagId));
        setLocalConfirmed(prev => [...prev, { ...tag, vote_count: 1, confirmed: true }]);
      }
    }
  }

  setApplying(null); // Clear loading state regardless of success or failure
};

  return (
    <div className="space-y-4">
      {/* Confirmed tags */}
      {localConfirmed.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs uppercase tracking-widest" style={{ color: "var(--text-muted)" }}>
            Community Tags
          </p>
          <div className="flex flex-wrap gap-2">
            {localConfirmed.map((tag) => (
              <button
                key={tag.id}
                onClick={() => applyTag(tag.id)}
                disabled={applying === tag.id}
                className="tag-pill cursor-pointer hover:opacity-80 transition-opacity"
              >
                {tag.label}
                <span className="ml-1 opacity-50">{tag.vote_count}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Suggested tags */}
      {localSuggested.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs uppercase tracking-widest" style={{ color: "var(--text-muted)" }}>
            Suggested
          </p>
          <div className="flex flex-wrap gap-2">
            {localSuggested.map((tag) => (
              <button
                key={tag.id}
                onClick={() => applyTag(tag.id)}
                disabled={applying === tag.id}
                className="cursor-pointer hover:opacity-100 transition-opacity"
                style={{
                  fontSize: "0.7rem",
                  padding: "3px 10px",
                  borderRadius: "9999px",
                  background: "rgba(124, 58, 237, 0.06)",
                  border: "1px solid rgba(124, 58, 237, 0.15)",
                  color: "var(--text-secondary)",
                  opacity: 0.7,
                }}
              >
                {tag.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}