import { Check } from "lucide-react";
import { cn } from "@/lib/utils";
import { CATEGORIES, type CategoryId } from "@/features/meetings/filters/categories";

interface CategoryChecklistProps {
  selected: Record<CategoryId, boolean>;
  onToggle: (id: CategoryId) => void;
}

export function CategoryChecklist({ selected, onToggle }: CategoryChecklistProps) {
  return (
    <div className="grid grid-cols-2 gap-x-4 gap-y-2 lg:grid-cols-1">
      {CATEGORIES.map(({ id, label, icon: Icon }) => {
        const checked = selected[id];
        return (
          <button
            key={id}
            type="button"
            onClick={() => onToggle(id)}
            aria-pressed={checked}
            className="flex w-full items-center gap-3 rounded-lg px-1 py-1.5 text-left transition-colors hover:bg-white/5"
          >
            <span
              className={cn(
                "flex h-5 w-5 shrink-0 items-center justify-center rounded border transition-colors",
                checked ? "border-blue-500 bg-blue-600" : "border-white/20 bg-white/5"
              )}
            >
              {checked && <Check size={12} strokeWidth={3} />}
            </span>
            <Icon size={16} className={checked ? "text-blue-400" : "text-slate-500"} />
            <span className={cn("text-sm", checked ? "text-white" : "text-slate-400")}>
              {label}
            </span>
          </button>
        );
      })}
    </div>
  );
}