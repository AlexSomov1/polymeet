import { Map, LayoutGrid } from "lucide-react";
import { cn } from "@/lib/utils";

export type ViewMode = "list" | "map";

interface ViewToggleProps {
  view: ViewMode;
  onChange: (view: ViewMode) => void;
}

const OPTIONS: { value: ViewMode; label: string; icon: typeof Map }[] = [
  { value: "list", label: "Список", icon: LayoutGrid },
  { value: "map", label: "Карта", icon: Map },
];

export function ViewToggle({ view, onChange }: ViewToggleProps) {
  return (
    <div
      role="group"
      aria-label="Вид отображения"
      className="flex rounded-lg border border-white/10 bg-white/5 p-0.5"
    >
      {OPTIONS.map(({ value, label, icon: Icon }) => (
        <button
          key={value}
          type="button"
          onClick={() => onChange(value)}
          aria-pressed={view === value}
          className={cn(
            "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs transition-colors",
            view === value
              ? "bg-blue-600 text-white"
              : "text-slate-400 hover:text-slate-200"
          )}
        >
          <Icon size={13} />
          <span className="hidden sm:inline">{label}</span>
        </button>
      ))}
    </div>
  );
}