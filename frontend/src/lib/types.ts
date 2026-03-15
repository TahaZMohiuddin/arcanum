export interface TagResponse {
  id: string;
  label: string;
  slug: string;
  vote_count: number;
  is_suggested: boolean;
  confirmed: boolean;
}

export interface AnimeCard {
  id: string;
  title: string;
  title_english: string | null;
  cover_url: string | null;
  genres: string[] | null;
  anilist_score: number | null;
  top_tags: string[];
}

export interface VibeCluster {
  id: string;
  label: string;
  anime: AnimeCard[];
}
