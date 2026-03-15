import type { Metadata } from "next";
import { Syne } from "next/font/google";
import { DM_Serif_Display } from "next/font/google";
import "./globals.css";

const syne = Syne({
  subsets: ["latin"],
  variable: "--font-syne",
  weight: ["400", "500", "600", "700"],
});

const dmSerif = DM_Serif_Display({
  subsets: ["latin"],
  variable: "--font-dm-serif",
  weight: "400",
});

export const metadata: Metadata = {
  title: "Arcanum — Your Anime Taste Fingerprint",
  description: "Track, tag, and discover anime through community vibe tags and taste matching.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${syne.variable} ${dmSerif.variable}`}>
      <body style={{ fontFamily: "var(--font-syne), sans-serif" }}>{children}</body>
    </html>
  );
}