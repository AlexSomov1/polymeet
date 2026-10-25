import { useMemo, useState } from "react";
import { Banner } from "@/widgets/banner/Banner";
import { MeetingCard } from "@/widgets/meeting-card/MeetingCard";
import { MOCK_MEETINGS } from "@/features/meetings/mock";
import { filterMeetings } from "@/lib/filterMeetings";
import { FilterSidebar } from "@/widgets/filters/FilterSidebar";
import type { FiltersState } from "@/features/meetings/filters/categories";
import { ViewToggle, type ViewMode } from "@/widgets/view-toggle/ViewToggle";
import { MapView } from "@/widgets/mapview/MapView";

export function FeedPage() {
  const [appliedFilters, setAppliedFilters] = useState<FiltersState | null>(null);
  const [query, setQuery] = useState("");
  const [view, setView] = useState<ViewMode>("list");

  // The single source of truth for what the user sees — both views derive from it
  const visibleMeetings = useMemo(
    () => filterMeetings(MOCK_MEETINGS, appliedFilters, query),
    [appliedFilters, query]
  );

  return (
    <div className="flex flex-col gap-6 lg:flex-row">
      {/* Feed-specific filters — deliberately NOT in AppLayout */}
      <aside className="w-full shrink-0 lg:w-75">
        <FilterSidebar onApply={setAppliedFilters} />
      </aside>

      <div className="min-w-0 flex-1 space-y-6">
        <Banner query={query} onQueryChange={setQuery} />

        <section>
          <div className="mb-4 flex items-center justify-between gap-3">
            <h2 className="text-lg font-semibold text-white">Доступные встречи</h2>
            <div className="flex items-center gap-3">
              <span className="text-sm text-slate-400">
                {visibleMeetings.length} встреч
              </span>
              <ViewToggle view={view} onChange={setView} />
            </div>
          </div>

          {visibleMeetings.length === 0 ? (
            <p className="rounded-xl border border-dashed border-white/15 p-10 text-center text-sm text-slate-500">
              Ничего не найдено. Попробуйте ослабить фильтры.
            </p>
          ) : view === "list" ? (
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {visibleMeetings.map((m) => (
                <MeetingCard key={m.id} meeting={m} />
              ))}
            </div>
          ) : (
            <MapView meetings={visibleMeetings} />
          )}
        </section>
      </div>
    </div>
  );
}