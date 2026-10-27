import { cn } from "@/lib/utils";
import { CATEGORIES } from "@/features/meetings/filters/categories";
import type { CategoryId } from "@/features/meetings/filters/categories";

interface CategoryChipsProps {
  selected: CategoryId;
  onSelect: (id: CategoryId) => void;
  error?: string;
}

export function CategoryChips({ selected, onSelect, error }: CategoryChipsProps) {
  return (
    <div className="space-y-2">
      <label className="text-xs font-medium text-slate-400">
        Тематика <span className="text-red-400">*</span>
      </label>
      <div className="flex flex-wrap gap-2">
        {CATEGORIES.map((cat) => {
          const isActive = selected === cat.id;
          return (
            <button
              key={cat.id}
              type="button"
              onClick={() => onSelect(cat.id)}
              className={cn(
                "flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium transition-colors",
                isActive
                  ? "bg-blue-600 text-white"
                  : "bg-white/5 text-slate-400 hover:bg-white/10 hover:text-slate-200"
              )}
            >
              {isActive ? `#${cat.label}` : cat.label}
            </button>
          );
        })}
      </div>
      {error && <p className="text-xs text-red-400">{error}</p>}
    </div>
  );
}