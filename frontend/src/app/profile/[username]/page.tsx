import { notFound } from "next/navigation";
import StatsCharts from "@/components/StatsCharts";

async function getUserProfile(username: string) {
    const apiUrl = process.env.API_URL || "http://localhost:8000";
    const res = await fetch(`${apiUrl}/users/${username}`, {
        next: { revalidate: 300 }, // 5 min cache — profile stats change occasionally
    });
    if (!res.ok) return null;
    return res.json();
}

// TODO Phase 3+: Add "Your Vibe" identity section above charts — derived from user's
// most-applied mood tags (e.g. "melancholy, character driven, slow burn").
// Add top-rated anime row with cover art (like Fable's "Top Rated Books").
// Add mood tag breakdown donut chart (like StoryGraph's mood pie).
// These require real user tag data to be meaningful — don't build until Phase 3.
export default async function ProfilePage({
    params,
}: {
    params: Promise<{ username: string }>;
}) {
    const { username } = await params;
    const profile = await getUserProfile(username);

    if (!profile) notFound();

    return (
        <main className="page-gradient min-h-screen pt-8">
            <div className="page-container py-12">
                <div className="flex gap-10">

                    {/* Left column — identity + stats summary */}
                    <div className="flex-shrink-0 w-56 space-y-6">
                        {/* Avatar placeholder */}
                        <div
                            className="w-24 h-24 rounded-full flex items-center justify-center text-2xl font-bold"
                            style={{
                                background: "var(--bg-card)",
                                color: "var(--accent-purple)",
                                fontFamily: "var(--font-dm-serif)",
                                border: "2px solid var(--pill-border)",
                            }}
                        >
                            {profile.username.charAt(0).toUpperCase()}
                        </div>

                        {/* Username */}
                        <div>
                            <h1
                                className="text-3xl"
                                style={{
                                    fontFamily: "var(--font-dm-serif), serif",
                                    color: "var(--text-primary)",
                                }}
                            >
                                {profile.username}
                            </h1>
                        </div>

                        {/* Quick stats */}
                        <div className="space-y-3">
                            {[
                                { label: "Total", value: profile.stats.total },
                                { label: "Completed", value: profile.stats.completed },
                                { label: "Watching", value: profile.stats.watching },
                                { label: "Dropped", value: profile.stats.dropped },
                            ].map(stat => (
                                <div key={stat.label} className="flex justify-between">
                                    <span className="text-sm" style={{ color: "var(--text-muted)" }}>
                                        {stat.label}
                                    </span>
                                    <span className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                                        {stat.value}
                                    </span>
                                </div>
                            ))}
                            {profile.stats.mean_score && (
                                <div className="flex justify-between">
                                    <span className="text-sm" style={{ color: "var(--text-muted)" }}>Mean Score</span>
                                    <span className="text-sm font-semibold" style={{ color: "var(--pill-text)" }}>
                                        {profile.stats.mean_score}
                                    </span>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Right column — charts */}
                    <div className="flex-1 space-y-4">
                        <h2
                            className="text-2xl"
                            style={{
                                fontFamily: "var(--font-dm-serif), serif",
                                color: "var(--text-primary)",
                            }}>
                            Taste Fingerprint
                        </h2>
                        <StatsCharts
                            scoreDistribution={profile.score_distribution}
                            genreBreakdown={profile.genre_breakdown}
                            stats={profile.stats}
                        />
                    </div>

                </div>
            </div>
        </main>
    );
}