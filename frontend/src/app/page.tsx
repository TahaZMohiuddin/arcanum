import { redirect } from "next/navigation";

// Next.js requires a page.tsx at the root (/) or it throws a build error

export default function Home() {
  redirect("/vibe");
}