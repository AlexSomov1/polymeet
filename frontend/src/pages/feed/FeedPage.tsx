// src/pages/feed/FeedPage.tsx
import { useState } from "react";
import { useOutletContext } from "react-router-dom";
import { Banner } from "@/widgets/banner/Banner";
import type { FiltersState } from "@/features/meetings/filters/categories";

// Type the context once — AppLayout must pass exactly this shape
interface FeedContext {
  appliedFilters: FiltersState | null;
}


export function FeedPage() {
  const { appliedFilters } = useOutletContext<FeedContext>();
  const [query, setQuery] = useState("");

  // Temporary: prove the data flows. Delete after checking the console.
  console.log("filters:", appliedFilters, "query:", query);

  return (
    <div className="space-y-6">
      <Banner query={query} onQueryChange={setQuery} />
      {/* Meetings grid lands here next session */}
    </div>
  );
}