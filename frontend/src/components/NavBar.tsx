"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { getToken, getUsername, removeToken, removeUsername } from "@/lib/auth";
import SearchBar from "./SearchBar";


// TODO Phase 3+: Add logo icon/motif left of "Arcanum" text (commissioned artist)
// TODO Phase 4+: Add notification indicator dot on username for social features (friend requests, taste matches)
// TODO: Add active state underline or subtle glow on current page link for stronger wayfinding

export default function NavBar() {
  const router = useRouter();
  const pathname = usePathname();
  const [username, setUsername] = useState<string | null>(null);

  useEffect(() => {
    setUsername(getUsername());
  }, [pathname]); // Re-check on route change

  const handleLogout = () => {
  removeToken();
  removeUsername();
  setUsername(null);
  router.push("/login");
};

  return (
    <nav
      className="sticky top-0 z-50 border-b"
      style={{
        background: "rgba(12,11,16,0.85)",
        backdropFilter: "blur(12px)",
        borderColor: "rgba(74, 69, 96, 0.3)",
      }}
    >
      <div className="page-container flex items-center justify-between h-14">
        {/* Logo */}
        <Link
          href="/vibe"
          className="text-2xl tracking-tight"
          style={{
            fontFamily: "var(--font-dm-serif), serif",
            color: "var(--pill-text)",
          }}
        >
          MyArcanum
        </Link>

        {/* Search */}
          <SearchBar />

        {/* Nav links */}
        <div className="flex items-center gap-6">
          <Link
            href="/vibe"
            className="text-sm transition-colors"
            style={{
              color: pathname === "/vibe" ? "var(--text-primary)" : "var(--text-secondary)",
            }}
          >
            Discover
          </Link>

          {username ? (
            <>
              <Link
                href={`/profile/${username}`}
                className="text-sm transition-colors"
                style={{
                  color: "var(--pill-text)",
                }}
              >
                {username}
              </Link>
              <Link
                href="/import"
                className="text-sm transition-colors"
                style={{ color: "var(--text-secondary)" }}
              >
                Import
              </Link>
              <button
                onClick={handleLogout}
                className="text-xs transition-colors cursor-pointer"
                style={{ color: "var(--text-muted)" }}
              >
                Disappear
              </button>
            </>
          ) : (
            <>
              <Link
                href="/login"
                className="text-sm"
                style={{ color: "var(--text-secondary)" }}
              >
                Return
              </Link>
              <Link
                href="/register"
                className="text-sm px-4 py-1.5 rounded-full font-medium"
                style={{
                  background: "var(--accent-purple)",
                  color: "var(--text-primary)",
                }}
              >
                Enter
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}