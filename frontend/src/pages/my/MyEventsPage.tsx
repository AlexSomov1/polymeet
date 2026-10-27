import { useMemo, useState } from "react";
import { cn } from "@/lib/utils";
import { MOCK_MY_EVENTS } from "@/features/meetings/mock";
import type { FiltersState } from "@/features/meetings/filters/categories";
import { ChatSheet } from "@/widgets/chat/ChatSheet";
import {
  selectByRole,
  selectHistory,
  selectThisWeek,
  selectPending,
  selectNextMeeting,
  countPending,
} from "@/lib/selectMyEvents";
import { filterMeetings } from "@/lib/filterMeetings";
import { FilterSidebar } from "@/widgets/filters/FilterSidebar";
import { MyEventCard } from "@/widgets/my-event-card/MyEventCard";
import type { MyEvent } from "@/features/meetings/mock";

type MainTab = "participant" | "organizer" | "history";
type SubFilter = "all" | "thisWeek" | "pending";

const MAIN_TABS: { id: MainTab; label: string }[] = [
  { id: "participant", label: "Я участвую" },
  { id: "organizer", label: "Я организатор" },
  { id: "history", label: "История" },
];
const SUB_FILTERS: { id: SubFilter; label: string }[] = [
  { id: "all", label: "Все" },
  { id: "thisWeek", label: "На этой неделе" },
  { id: "pending", label: "Ожидают ответа" },
];

export function MyEventsPage() {
  const [tab, setTab] = useState<MainTab>("participant");
  const [sub, setSub] = useState<SubFilter>("all");
  const [appliedFilters, setAppliedFilters] = useState<FiltersState | null>(null);

  const pCount = selectByRole(MOCK_MY_EVENTS, "participant").length;
  const oCount = selectByRole(MOCK_MY_EVENTS, "organizer").length;
  const hCount = selectHistory(MOCK_MY_EVENTS).length;
  const oPending = countPending(MOCK_MY_EVENTS, "organizer");

  const tabCounts: Record<MainTab, number> = {
    participant: pCount,
    organizer: oCount,
    history: hCount,
  };

  const baseEvents = useMemo(() => {
    if (tab === "history") return selectHistory(MOCK_MY_EVENTS);
    return selectByRole(MOCK_MY_EVENTS, tab);
  }, [tab]);

  const subFiltered = useMemo(() => {
    if (sub === "thisWeek") return selectThisWeek(baseEvents);
    if (sub === "pending") return selectPending(baseEvents);
    return baseEvents;
  }, [baseEvents, sub]);

  const visibleEvents = useMemo(
    () => filterMeetings(subFiltered, appliedFilters, ""),
    [subFiltered, appliedFilters]
  );

  const nextMeeting = useMemo(
    () => (tab !== "history" ? selectNextMeeting(MOCK_MY_EVENTS, tab) : undefined),
    [tab]
  );

  const handleTabChange = (id: MainTab) => {
    setTab(id);
    setSub("all");
  };
  const [chatMeetingId, setChatMeetingId] = useState<string | null>(null);
  return (
    <div className="flex flex-col gap-6 lg:flex-row">
      {/* Left sidebar */}
      <aside className="w-full shrink-0 space-y-6 lg:w-80">
        <FilterSidebar onApply={setAppliedFilters} />

        {nextMeeting && (
          <div className="rounded-xl border border-white/10 bg-linear-to-b from-[#1b2440] to-[#131a30] p-5">
            <h3 className="text-xs font-medium uppercase tracking-wide text-slate-400">
              Ближайшая встреча
            </h3>
            <div className="mt-3 rounded-lg bg-white/5 px-3 py-2 text-center text-sm font-semibold text-white">
              Через 3 ч. 20 мин
            </div>
            <p className="mt-3 text-sm font-semibold text-white">{nextMeeting.title}</p>
            <p className="mt-1 text-xs text-slate-400">{nextMeeting.address}</p>
            <div className="mt-4 flex gap-2">
              <button className="flex-1 rounded-lg bg-blue-600 py-2 text-xs font-semibold text-white transition-colors hover:bg-blue-500">
                Маршрут
              </button>
              <button className="flex-1 rounded-lg bg-white/10 py-2 text-xs font-semibold text-white transition-colors hover:bg-white/15">
                Чат встречи
              </button>
            </div>
          </div>
        )}

        <div className="rounded-xl border border-white/10 bg-linear-to-b from-[#1b2440] to-[#131a30] p-5">
          <h3 className="text-xs font-medium uppercase tracking-wide text-slate-400">
            Надёжность участника
          </h3>
          <div className="mt-4 grid place-items-center">
            <span className="text-4xl font-bold text-white">96%</span>
          </div>
          <p className="mt-2 text-center text-xs text-slate-500">
            11 посещено / 1 пропуск
          </p>
        </div>
      </aside>

      {/* Right content */}
      <div className="min-w-0 flex-1 space-y-4">
        {/* Main tabs */}
        <div className="flex flex-wrap gap-2">
          {MAIN_TABS.map(({ id, label }) => {
            const active = tab === id;
            return (
              <button
                key={id}
                onClick={() => handleTabChange(id)}
                className={cn(
                  "flex items-center gap-1.5 rounded-lg px-4 py-2 text-sm font-medium transition-colors",
                  active
                    ? "bg-blue-600 text-white"
                    : "bg-white/5 text-slate-400 hover:bg-white/10 hover:text-slate-200"
                )}
              >
                <span>
                  {label} ({tabCounts[id]})
                </span>
                {id === "organizer" && oPending > 0 && (
                  <span className="rounded-full bg-amber-500 px-1.5 text-[10px] font-bold text-black">
                    {oPending} заявки
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* Sub-filters */}
        {tab !== "history" && (
          <div className="flex flex-wrap gap-2">
            {SUB_FILTERS.map(({ id, label }) => (
              <button
                key={id}
                onClick={() => setSub(id)}
                className={cn(
                  "rounded-lg px-3 py-1.5 text-xs transition-colors",
                  sub === id
                    ? "bg-white/10 text-white"
                    : "text-slate-500 hover:text-slate-300"
                )}
              >
                {label}
              </button>
            ))}
          </div>
        )}

        {/* Cards grid */}
        <div className="grid gap-4 sm:grid-cols-2">
          {visibleEvents.map((event) => (
           <MyEventCard
              key={event.id}
              event={event as MyEvent}
              onChat={(id) => setChatMeetingId(id)}
              onEdit={(id) => console.log("edit event", id)}
              onDelete={(id) => console.log("delete event", id)}
              onCancelApplication={(id) => console.log("cancel application", id)}
            />
          ))}
        </div>

        {visibleEvents.length === 0 && (
          <p className="rounded-xl border border-dashed border-white/15 p-10 text-center text-sm text-slate-500">
            Ничего не найдено. Попробуйте изменить фильтры.
          </p>
        )}
      </div>
      <ChatSheet
        meetingId={chatMeetingId}
        isOpen={!!chatMeetingId}
        onClose={() => setChatMeetingId(null)}
      />
    </div>
  );
}