import { VibeCluster as VibeClusterType } from "@/lib/types";
import VibeCluster from "@/components/VibeCluster";

async function getVibeClusters(): Promise<VibeClusterType[]> {
  const res = await fetch("http://localhost:8000/vibe/", {
    next: { revalidate: 14400 }, // 4 hours — matches aggregation job schedule
  });
  if (!res.ok) return [];
  return res.json();
}

export default async function VibePage() {
  const clusters = await getVibeClusters();

  return (
    <main
      className="min-h-screen py-12 space-y-10"
      style={{ background: "var(--bg-primary)" }}
    >
      {/* Page header */}
      <div className="px-6 space-y-1">
        <h1
          className="text-4xl"
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
        <div className="px-6" style={{ color: "var(--text-muted)" }}>
          No vibes yet. Tag some anime to get started.
        </div>
      ) : (
        clusters.map((cluster) => (
          <VibeCluster key={cluster.id} cluster={cluster} />
        ))
      )}
    </main>
  );
}