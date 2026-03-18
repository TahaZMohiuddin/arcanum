"use client";

interface GenreCount {
  genre: string;
  count: number;
}

interface Props {
  scoreDistribution: Record<string, number>;
  genreBreakdown: GenreCount[];
  stats: {
    total: number;
    completed: number;
    watching: number;
    plan_to_watch: number;
    dropped: number;
    mean_score: number | null;
  };
}

const SCORE_COLORS = [
  "#ef4444", "#f97316", "#f97316", "#eab308",
  "#eab308", "#84cc16", "#22c55e", "#10b981",
  "#7c3aed", "#6d28d9"
];

const GENRE_COLORS = [
  "#7c3aed", "#4f46e5", "#0891b2", "#059669",
  "#d97706", "#dc2626", "#db2777", "#7c3aed",
];

export default function StatsCharts({ scoreDistribution, genreBreakdown, stats }: Props) {
  const maxGenreCount = Math.max(...genreBreakdown.map(g => g.count), 1);
  const maxScoreCount = Math.max(...Object.values(scoreDistribution), 1);

  const statusData = [
    { label: "Completed", value: stats.completed, color: "#7c3aed" },
    { label: "Watching", value: stats.watching, color: "#0891b2" },
    { label: "Plan to Watch", value: stats.plan_to_watch, color: "#059669" },
    { label: "Dropped", value: stats.dropped, color: "#dc2626" },
  ].filter(s => s.value > 0);

  return (
    <div className="space-y-12">

      {/* Status breakdown */}
      <div className="space-y-4">
        <h3
          className="text-xs uppercase tracking-widest"
          style={{ color: "var(--text-muted)" }}
        >
          List Breakdown
        </h3>
        <div className="flex h-4 rounded-full overflow-hidden gap-0.5">
          {statusData.map(s => (
            <div
              key={s.label}
              style={{
                width: `${(s.value / stats.total) * 100}%`,
                background: s.color,
              }}
              title={`${s.label}: ${s.value}`}
            />
          ))}
        </div>
        <div className="flex flex-wrap gap-5">
          {statusData.map(s => (
            <div key={s.label} className="flex items-center gap-2">
              <div className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ background: s.color }} />
              <span className="text-sm" style={{ color: "var(--text-secondary)" }}>
                {s.label}
              </span>
              <span className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                {s.value}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Score distribution */}
      <div className="space-y-4">
        <h3
          className="text-xs uppercase tracking-widest"
          style={{ color: "var(--text-muted)" }}
        >
          Score Distribution
        </h3>
        <div className="flex items-end gap-2" style={{ height: "140px" }}>
          {Object.entries(scoreDistribution).map(([score, count], i) => (
            <div key={score} className="flex-1 flex flex-col items-center gap-2">
              {count > 0 && (
                <span className="text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>
                  {count}
                </span>
              )}
              <div
                className="w-full rounded-t transition-all"
                style={{
                  height: `${Math.max((count / maxScoreCount) * 100, 8)}px`,
                  background: count > 0 ? SCORE_COLORS[i] : "var(--bg-card)",
                  opacity: count > 0 ? 1 : 0.15,
                }}
                title={`Score ${score}: ${count} anime`}
              />
              <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                {score}
              </span>
            </div>
          ))}
        </div>
        {stats.mean_score && (
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
            Mean score:{" "}
            <span className="font-semibold" style={{ color: "var(--pill-text)" }}>
              {stats.mean_score}
            </span>
          </p>
        )}
      </div>

      {/* Genre breakdown */}
      <div className="space-y-4">
        <h3
          className="text-xs uppercase tracking-widest"
          style={{ color: "var(--text-muted)" }}
        >
          Top Genres
        </h3>
        <div className="space-y-3">
          {genreBreakdown.slice(0, 8).map((g, i) => (
            <div key={g.genre} className="flex items-center gap-4">
              <span
                className="text-sm w-28 text-right flex-shrink-0"
                style={{ color: "var(--text-secondary)" }}
              >
                {g.genre}
              </span>
              <div
                className="flex-1 h-2 rounded-full"
                style={{ background: "var(--bg-card)" }}
              >
                <div
                  className="h-full rounded-full transition-all"
                  style={{
                    width: `${(g.count / maxGenreCount) * 100}%`,
                    background: GENRE_COLORS[i % GENRE_COLORS.length],
                  }}
                />
              </div>
              <span
                className="text-sm w-8 flex-shrink-0 font-semibold"
                style={{ color: "var(--text-primary)" }}
              >
                {g.count}
              </span>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
}