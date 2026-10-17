import { Calendar } from "lucide-react";

interface DateFieldProps {
  value: string;
  onChange: (value: string) => void;
}

export function DateField({ value, onChange }: DateFieldProps) {
  return (
    <div className="relative">
      <Calendar
        size={15}
        className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
      />
      <input
        type="date"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-lg border border-white/10 bg-white/5 py-2.5 pl-9 pr-3 text-sm text-slate-200 outline-none transition-colors [color-scheme:dark] focus:border-blue-500/60"
      />
    </div>
  );
}