import { VibeCluster as VibeClusterType } from "@/lib/types";
import VibeCluster from "@/components/VibeCluster";

async function getVibeClusters(): Promise<VibeClusterType[]> {
  const apiUrl = process.env.API_URL || "http://localhost:8000";
  const res = await fetch(`${apiUrl}/vibe/`, {
    next: { revalidate: 14400 },
  });
  if (!res.ok) return [];
  return res.json();
}

// One-line descriptions per cluster
const CLUSTER_SUBTITLES: Record<string, string> = {
  "late-night": "For when sleep isn't coming anyway.",
  "watch-together": "Loud, fun, and better with company.",
  "emotional": "Because depression, economic collapse and existential dread aren't enough.",
  "chill": "Low stakes, high reward.",
  "prestige": "The ones that actually deserve the hype.",
  "hidden": "Become an anime hipster.",
  "intense": "You will not be okay.",
  "aesthetic": "Watch it for the craft.",
};

export default async function VibePage() {
  // TODO Phase 4: Sort VIBE_CLUSTERS by time of day before rendering.
  // "Late Night Watch" first at 2am, "Watch With People" first on Friday evening.
  // Frontend-only change — check user's local time, reorder array before map().
  // No schema or backend changes needed.
  const clusters = await getVibeClusters();

  return (
    <main className="page-gradient pt-8">
      <div className="page-container py-16 space-y-20">
        {/* Page header */}
        <div className="space-y-2">
          <h1
            className="text-6xl leading-tight"
            style={{
              fontFamily: "var(--font-dm-serif), serif",
              color: "var(--text-primary)",
            }}
          >
            What do you want to feel?
          </h1>
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
            Browse anime by vibe, not by genre.
          </p>
        </div>

        {/* Clusters */}
        {clusters.length === 0 ? (
          <div style={{ color: "var(--text-muted)" }}>
            No vibes yet. Tag some anime to get started.
          </div>
        ) : (
          clusters.map((cluster) => (
            <VibeCluster
              key={cluster.id}
              cluster={cluster}
              subtitle={CLUSTER_SUBTITLES[cluster.id] || ""}
            />
          ))
        )}
      </div>
    </main>
  );
}