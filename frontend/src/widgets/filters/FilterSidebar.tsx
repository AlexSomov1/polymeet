// src/widgets/filters/FilterSidebar.tsx
import { useState } from "react";
import { SlidersHorizontal, RotateCcw, ChevronDown, Filter } from "lucide-react";
import { useFilters } from "./useFilters";
import { DateField } from "./controls/DateField";
import { SeatsStepper } from "./controls/SeatsStepper";
import { RadiusSlider } from "./controls/RadiusSlider";
import { CategoryChecklist } from "./controls/CategoryChecklist";
import type { FiltersState } from "@/features/meetings/filters/categories";

interface FilterSidebarProps {
  onApply?: (filters: FiltersState) => void;
}

export function FilterSidebar({ onApply }: FilterSidebarProps) {
  const { filters, set, toggleCategory, reset, activeCount } = useFilters();
  const [open, setOpen] = useState(false);

  return (
    <aside className="w-full rounded-2xl border border-white/10 bg-gradient-to-b from-[#101625] to-[#0b0f1a] p-5 text-white shadow-xl lg:w-[300px]">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <SlidersHorizontal size={16} className="text-blue-400" />
          <h2 className="font-semibold text-white">Фильтры</h2>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={reset}
            className="flex items-center gap-1 text-xs text-blue-400 transition-colors hover:text-blue-300"
          >
            <RotateCcw size={12} />
            Сбросить всё
          </button>
          <button
            onClick={() => setOpen((o) => !o)}
            className="text-slate-400 transition-transform lg:hidden"
            aria-label={open ? "Свернуть фильтры" : "Развернуть фильтры"}
            aria-expanded={open}
          >
            <ChevronDown
              size={18}
              className={`transition-transform ${open ? "rotate-180" : ""}`}
            />
          </button>
        </div>
      </div>

      {/* Collapsible content — closed on mobile until toggled, always open on lg+ */}
      <div className={`${open ? "" : "hidden"} lg:block`}>
        {/* Date */}
        <label className="mb-5 block">
          <span className="mb-2 block text-sm text-slate-300">Дата</span>
          <DateField value={filters.date} onChange={(d) => set("date", d)} />
        </label>

        {/* Seats */}
        <div className="mb-5">
          <span className="mb-2 block text-sm text-slate-300">
            Свободных мест не менее
          </span>
          <SeatsStepper
            value={filters.minSeats}
            onChange={(n) => set("minSeats", n)}
          />
        </div>

        {/* Radius */}
        <div className="mb-6">
          <RadiusSlider
            value={filters.radiusKm}
            onChange={(n) => set("radiusKm", n)}
          />
        </div>

        {/* Categories */}
        <div className="mb-6">
          <span className="mb-2 block text-sm text-slate-300">Категории</span>
          <CategoryChecklist
            selected={filters.categories}
            onToggle={toggleCategory}
          />
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
      </div>
    </aside>
  );
}