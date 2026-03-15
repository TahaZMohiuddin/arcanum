"use client";
import { useRef } from "react";
import { VibeCluster as VibeClusterType } from "@/lib/types";
import AnimeCard from "./AnimeCard";
import Link from "next/link";

interface Props {
  cluster: VibeClusterType;
  subtitle?: string;
}

export default function VibeCluster({ cluster, subtitle }: Props) {
  const scrollRef = useRef<HTMLDivElement>(null);

  const scroll = (dir: "left" | "right") => {
    if (!scrollRef.current) return;
    scrollRef.current.scrollBy({
      left: dir === "right" ? 440 : -440,
      behavior: "smooth",
    });
  };

  return (
    <section className="space-y-4">
      {/* Cluster heading */}
      <div className="flex items-end justify-between">
        <div className="space-y-0.5">
          <h2
            className="text-3xl"
            style={{
              fontFamily: "var(--font-dm-serif), serif",
              color: "var(--text-primary)",
            }}
          >
            {cluster.label}
          </h2>
          {subtitle && (
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
              {subtitle}
            </p>
          )}
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => scroll("left")}
            className="text-lg px-2 transition-opacity hover:opacity-100 opacity-40"
            style={{ color: "var(--text-primary)" }}
            aria-label="Scroll left"
          >
            ←
          </button>
          <button
            onClick={() => scroll("right")}
            className="text-lg px-2 transition-opacity hover:opacity-100 opacity-40"
            style={{ color: "var(--text-primary)" }}
            aria-label="Scroll right"
          >
            →
          </button>
          <Link
            href={`/vibe/${cluster.id}`}
            className="text-xs transition-colors hover:opacity-100 opacity-60"
            style={{ color: "var(--text-secondary)" }}
          >
            see all →
          </Link>
        </div>
      </div>

      {/* Horizontal scroll row */}
      <div
        ref={scrollRef}
        className="scroll-row flex items-stretch gap-4 pb-2"
      >
        {cluster.anime.map((anime) => (
          <AnimeCard key={anime.id} anime={anime} />
        ))}
      </div>
    </section>
  );
}