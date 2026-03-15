import Image from "next/image";
import Link from "next/link";
import { AnimeCard as AnimeCardType } from "@/lib/types";

export default function AnimeCard({ anime }: { anime: AnimeCardType }) {
  const displayTitle = anime.title_english || anime.title;

  return (
    <Link href={`/anime/${anime.id}`} className="group block flex-shrink-0 w-48">
      <div
        className="relative rounded-xl overflow-hidden transition-transform duration-300 group-hover:-translate-y-2"
        style={{ background: "var(--bg-card)" }}
      >
        {/* Cover art — proper anime poster ratio */}
        <div className="relative w-48 h-72">
          {anime.cover_url ? (
            <Image
              src={anime.cover_url}
              alt={displayTitle}
              fill
              className="object-cover"
              sizes="192px"
            />
          ) : (
            <div
              className="w-full h-full flex items-center justify-center text-xs text-center p-3"
              style={{ color: "var(--text-muted)" }}
            >
              {displayTitle}
            </div>
          )}

          {/* Gradient overlay at bottom of cover */}
          <div
            className="absolute bottom-0 left-0 right-0 h-20"
            style={{
              background: "linear-gradient(transparent, rgba(12,11,16,0.95))",
            }}
          />

          {/* Score badge */}
          {anime.anilist_score && (
            <div
              className="absolute top-2 right-2 text-sm font-bold px-2 py-1 rounded-md"
              style={{
                background: "rgba(12,11,16,0.92)",
                color: "var(--text-primary)",
                backdropFilter: "blur(4px)",
              }}
            >
              {anime.anilist_score}
            </div>
          )}
        </div>

        {/* Card footer */}
        <div className="p-3 space-y-2 flex-1" style={{ minHeight: "80px" }}>
          <p
            className="text-xs font-medium leading-tight line-clamp-2"
            style={{ color: "var(--text-primary)", fontFamily: "var(--font-syne)" }}
          >
            {displayTitle}
          </p>

          {/* Tag pills — hero element, always visible */}
          {anime.top_tags.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {anime.top_tags.slice(0, 3).map((tag) => (
                <span key={tag} className="tag-pill">
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </Link>
  );
}