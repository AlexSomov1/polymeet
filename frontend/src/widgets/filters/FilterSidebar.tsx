import { useMemo, useState } from "react";
import {
  SlidersHorizontal,
  RotateCcw,
  Calendar,
  GraduationCap,
  Gamepad2,
  Music,
  Dumbbell,
  Trees,
  MoreHorizontal,
  Filter,
} from "lucide-react";

export type CategoryId =
  | "lecture"
  | "games"
  | "concert"
  | "sport"
  | "walk"
  | "other";

export interface FiltersState {
  date: string;
  minSeats: number;
  radiusKm: number;
  categories: Record<CategoryId, boolean>;
}

interface FilterSidebarProps {
  onApply?: (filters: FiltersState) => void;
}

const CATEGORIES: { id: CategoryId; label: string; icon: typeof Music }[] = [
  { id: "lecture", label: "Лекция", icon: GraduationCap },
  { id: "games", label: "Игры", icon: Gamepad2 },
  { id: "concert", label: "Концерт", icon: Music },
  { id: "sport", label: "Спорт", icon: Dumbbell },
  { id: "walk", label: "Прогулка", icon: Trees },
  { id: "other", label: "Другое", icon: MoreHorizontal },
];

const MIN_RADIUS = 1;
const MAX_RADIUS = 50;

const defaultFilters: FiltersState = {
  date: "",
  minSeats: 1,
  radiusKm: 10,
  categories: {
    lecture: true,
    games: true,
    concert: true,
    sport: false,
    walk: false,
    other: false,
  },
};

export function FilterSidebar({ onApply }: FilterSidebarProps) {
  const [filters, setFilters] = useState<FiltersState>(defaultFilters);

  const activeCount = useMemo(() => {
    const cats = Object.values(filters.categories).filter(Boolean).length;
    return (
      (filters.date ? 1 : 0) +
      (filters.minSeats > 0 ? 1 : 0) +
      (filters.radiusKm !== defaultFilters.radiusKm ? 1 : 0) +
      cats
    );
  }, [filters]);

  const set = <K extends keyof FiltersState>(key: K, value: FiltersState[K]) =>
    setFilters((f) => ({ ...f, [key]: value }));

  const toggleCategory = (id: CategoryId) =>
    setFilters((f) => ({
      ...f,
      categories: { ...f.categories, [id]: !f.categories[id] },
    }));

  const reset = () => setFilters(defaultFilters);

  const radiusFill =
    ((filters.radiusKm - MIN_RADIUS) / (MAX_RADIUS - MIN_RADIUS)) * 100;

  return (
    <aside className="w-[300px] rounded-2xl border border-white/10 bg-gradient-to-b from-[#101625] to-[#0b0f1a] p-5 text-white shadow-xl">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <SlidersHorizontal size={16} className="text-blue-400" />
          <h2 className="text-white font-semibold">Фильтры</h2>
        </div>
        <button
          onClick={reset}
          className="flex items-center gap-1 text-xs text-blue-400 transition-colors hover:text-blue-300"
        >
          <RotateCcw size={12} />
          Сбросить всё
        </button>
      </div>

      {/* Date */}
      <label className="mb-5 block">
        <span className="mb-2 block text-sm text-slate-300">Дата</span>
        <div className="relative">
          <Calendar
            size={15}
            className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
          />
          <input
            type="date"
            value={filters.date}
            onChange={(e) => set("date", e.target.value)}
            className="w-full rounded-lg border border-white/10 bg-white/5 py-2.5 pl-9 pr-3 text-sm text-slate-200 outline-none transition-colors [color-scheme:dark] focus:border-blue-500/60"
          />
        </div>
      </label>

      {/* Seats */}
      <div className="mb-5">
        <span className="mb-2 block text-sm text-slate-300">
          Свободных мест не менее
        </span>
        <div className="flex items-center rounded-lg border border-white/10 bg-white/5">
          <button
            onClick={() =>
              set("minSeats", Math.max(0, filters.minSeats - 1))
            }
            className="px-3 py-2.5 text-lg text-slate-400 transition-colors hover:text-white"
            aria-label="Меньше"
          >
            −
          </button>
          <span className="flex-1 text-center text-sm font-medium">
            {filters.minSeats}
          </span>
          <button
            onClick={() => set("minSeats", filters.minSeats + 1)}
            className="px-3 py-2.5 text-lg text-slate-400 transition-colors hover:text-white"
            aria-label="Больше"
          >
            +
          </button>
        </div>
      </div>

      {/* Radius */}
      <div className="mb-6">
        <div className="mb-2 flex items-center justify-between">
          <span className="text-sm text-slate-300">Радиус от меня</span>
          <span className="text-sm font-semibold text-white">
            {filters.radiusKm} км
          </span>
        </div>
        <input
          type="range"
          min={MIN_RADIUS}
          max={MAX_RADIUS}
          value={filters.radiusKm}
          onChange={(e) => set("radiusKm", Number(e.target.value))}
          className="h-1.5 w-full cursor-pointer appearance-none rounded-full outline-none [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-white [&::-webkit-slider-thumb]:shadow-[0_0_8px_rgba(96,165,250,.9)]"
          style={{
            background: `linear-gradient(to right, #3b82f6 ${radiusFill}%, rgba(255,255,255,.12) ${radiusFill}%)`,
          }}
        />
      </div>

      {/* Categories */}
      <div className="mb-6">
        <span className="mb-2 block text-sm text-slate-300">Категории</span>
        <div className="space-y-2">
          {CATEGORIES.map(({ id, label, icon: Icon }) => {
            const checked = filters.categories[id];
            return (
              <button
                key={id}
                onClick={() => toggleCategory(id)}
                className="flex w-full items-center gap-3 rounded-lg px-1 py-1.5 text-left transition-colors hover:bg-white/5"
              >
                <span
                  className={`flex h-5 w-5 items-center justify-center rounded border transition-colors ${
                    checked
                      ? "border-blue-500 bg-blue-600"
                      : "border-white/20 bg-white/5"
                  }`}
                >
                  {checked && (
                    <svg width="11" height="9" viewBox="0 0 11 9" fill="none">
                      <path
                        d="M1 4.5L4 7.5L10 1"
                        stroke="white"
                        strokeWidth="2"
                        strokeLinecap="round"
                      />
                    </svg>
                  )}
                </span>
                <Icon
                  size={16}
                  className={checked ? "text-blue-400" : "text-slate-500"}
                />
                <span
                  className={`text-sm ${checked ? "text-white" : "text-slate-400"}`}
                >
                  {label}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Apply */}
      <button
        onClick={() => onApply?.(filters)}
        className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-blue-500 py-3 text-sm font-semibold text-white shadow-lg shadow-blue-900/40 transition-transform hover:scale-[1.02] active:scale-[0.98]"
      >
        <Filter size={15} />
        Применить фильтры
        {activeCount > 0 && (
          <span className="rounded-full bg-white/20 px-1.5 text-xs">
            {activeCount}
          </span>
        )}
      </button>
    </aside>
  );
}