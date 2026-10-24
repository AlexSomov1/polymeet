import { useMemo, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { Banner } from "@/widgets/banner/Banner";
import { MeetingCard } from "@/widgets/meeting-card/MeetingCard";
import { MOCK_MEETINGS } from "@/features/meetings/mock";
import { filterMeetings } from "@/lib/filterMeetings";
import type { FiltersState } from "@/features/meetings/filters/categories";

interface FeedContext {
  appliedFilters: FiltersState | null;
}

export function FeedPage() {
  const { appliedFilters } = useOutletContext<FeedContext>();
  const [query, setQuery] = useState("");

  const visibleMeetings = useMemo(
    () => filterMeetings(MOCK_MEETINGS, appliedFilters, query),
    [appliedFilters, query]
  );

  return (
    <div className="space-y-6">
      <Banner query={query} onQueryChange={setQuery} />

      <section>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white">Доступные встречи</h2>
          <span className="text-sm text-slate-400">
            {visibleMeetings.length} встреч
          </span>
        </div>

        {visibleMeetings.length === 0 ? (
          <p className="rounded-xl border border-dashed border-white/15 p-10 text-center text-sm text-slate-500">
            Ничего не найдено. Попробуйте ослабить фильтры.
          </p>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {visibleMeetings.map((m) => (
              <MeetingCard key={m.id} meeting={m} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}