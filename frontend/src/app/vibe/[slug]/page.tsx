import { notFound } from "next/navigation";
import Link from "next/link";
import AnimeCard from "@/components/AnimeCard";
import { AnimeCard as AnimeCardType } from "@/lib/types";

// TODO Phase 3+: Add sort options (by arcanum_score, by anilist_score, by tag vote count)
// TODO Phase 4+: Add pagination or infinite scroll — current limit is 50 from backend
// TODO Phase 5: Add related clusters sidebar ("People who browse Late Night Watch also like...")

// TODO UI: Add sort dropdown (by score, by tag votes) — Phase 3+
// TODO UI: Cards could show genre pills on hover for more discovery context
// TODO UI: "50 anime" count feels clinical — consider "50 titles" or just remove count

const CLUSTER_SUBTITLES: Record<string, string> = {
    "late-night": "For when sleep isn't coming anyway.",
    "watch-together": "Loud, fun, and better with company.",
    "emotional": "You asked for this.",
    "chill": "Low stakes, high reward.",
    "prestige": "The ones that actually deserve the hype.",
    "hidden": "Your next favourite show is in here.",
    "intense": "You will not be okay.",
    "aesthetic": "Watch it for the craft.",
};

async function getVibeCluster(slug: string) {
    const apiUrl = process.env.API_URL || "http://localhost:8000";
    const res = await fetch(`${apiUrl}/vibe/${slug}`, {
        next: { revalidate: 14400 },
    });
    if (!res.ok) return null;
    return res.json();
}

export default async function VibeDrillDownPage({
    params,
}: {
    params: Promise<{ slug: string }>;
}) {
    const { slug } = await params;
    const cluster = await getVibeCluster(slug);

    if (!cluster) notFound();

    return (
        <main className="page-gradient min-h-screen pt-8">
            <div className="page-container py-12">
                {/* Header */}
                <div className="space-y-1 mb-10">
                    <Link
                        href="/vibe"
                        className="text-xs uppercase tracking-widest transition-colors"
                        style={{ color: "var(--text-muted)" }}
                    >
                        ← All vibes
                    </Link>
                    <h1
                        className="text-4xl"
                        style={{
                            fontFamily: "var(--font-dm-serif), serif",
                            color: "var(--text-primary)",
                        }}
                    >
                        {cluster.label}
                    </h1>
                    {CLUSTER_SUBTITLES[slug] && (
                        <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
                            {CLUSTER_SUBTITLES[slug]}
                        </p>
                    )}
                    <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
                        {cluster.anime.length} anime
                    </p>
                </div>

                {/* Grid */}
                {cluster.anime.length === 0 ? (
                    <p style={{ color: "var(--text-muted)" }}>
                        No anime tagged here yet.
                    </p>
                ) : (
                    <div className="flex flex-wrap gap-4">
                        {cluster.anime.map((anime: AnimeCardType) => (
                            <AnimeCard key={anime.id} anime={anime} />
                        ))}
                    </div>
                )}
            </div>
        </main>
    );
}