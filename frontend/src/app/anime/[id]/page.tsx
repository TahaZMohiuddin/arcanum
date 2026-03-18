import Image from "next/image";
import { notFound } from "next/navigation";
import TagSection from "@/components/TagSection";

async function getAnime(id: string) {
  const apiUrl = process.env.API_URL || "http://localhost:8000";
  const res = await fetch(`${apiUrl}/anime/${id}`, { next: { revalidate: 3600 } });
  if (!res.ok) return null;
  return res.json();
}

async function getAnimeTags(id: string) {
  const apiUrl = process.env.API_URL || "http://localhost:8000";
  const res = await fetch(`${apiUrl}/anime/${id}/tags`, { next: { revalidate: 0 } });
  if (!res.ok) return { confirmed: [], suggested: [] };
  return res.json();
}

export default async function AnimeDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const [anime, tags] = await Promise.all([getAnime(id), getAnimeTags(id)]);

  if (!anime) notFound();

  return (
    <main className="page-gradient min-h-screen pt-8">
      <div className="page-container py-12">
        <div className="flex gap-10">
          {/* Cover art */}
          <div className="flex-shrink-0">
            <div className="relative w-56 h-80 rounded-xl overflow-hidden">
              {anime.cover_url ? (
                <Image
                  src={anime.cover_url}
                  alt={anime.title_english || anime.title}
                  fill
                  className="object-cover"
                  sizes="224px"
                  priority
                />
              ) : (
                <div
                  className="w-full h-full"
                  style={{ background: "var(--bg-card)" }}
                />
              )}
            </div>

            {/* Scores */}
            <div className="mt-4 space-y-2">
              {anime.anilist_score && (
                <div className="flex justify-between text-sm">
                  <span style={{ color: "var(--text-muted)" }}>AniList</span>
                  <span style={{ color: "var(--text-primary)" }} className="font-semibold">
                    {anime.anilist_score}
                  </span>
                </div>
              )}
              {anime.arcanum_score && (
                <div className="flex justify-between text-sm">
                  <span style={{ color: "var(--text-muted)" }}>Arcanum</span>
                  <span style={{ color: "var(--pill-text)" }} className="font-semibold">
                    {anime.arcanum_score}
                  </span>
                </div>
              )}
            </div>

            {/* Meta */}
            <div className="mt-4 space-y-1 text-xs" style={{ color: "var(--text-muted)" }}>
              {anime.episode_count && <p>{anime.episode_count} episodes</p>}
              {anime.season && anime.season_year && (
                <p>{anime.season.charAt(0) + anime.season.slice(1).toLowerCase()} {anime.season_year}</p>
              )}
            </div>
          </div>

          {/* Main content */}
          <div className="flex-1 space-y-6">
            {/* Title */}
            <div>
              <h1
                className="text-4xl leading-tight"
                style={{
                  fontFamily: "var(--font-dm-serif), serif",
                  color: "var(--text-primary)",
                }}
              >
                {anime.title_english || anime.title}
              </h1>
              {anime.title_english && (
                <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>
                  {anime.title}
                </p>
              )}
            </div>

            {/* Genres */}
            {anime.genres?.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {anime.genres.map((genre: string) => (
                  <span
                    key={genre}
                    className="text-xs px-2 py-1 rounded"
                    style={{
                      background: "var(--bg-card)",
                      color: "var(--text-secondary)",
                      border: "1px solid var(--text-muted)",
                    }}
                  >
                    {genre}
                  </span>
                ))}
              </div>
            )}

            {/* Synopsis */}
            {anime.synopsis && (
              <div>
                <p
                  className="text-sm leading-relaxed"
                  style={{ color: "var(--text-secondary)" }}>
                  {anime.synopsis.replace(/<br>/g, " ").replace(/<[^>]+>/g, "")}
                </p>
              </div>
            )}

            {/* Tags */}
            <TagSection
              confirmed={tags.confirmed}
              suggested={tags.suggested}
              animeId={id}
            />
          </div>
        </div>
      </div>
    </main>
  );
}