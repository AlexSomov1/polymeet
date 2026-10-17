interface SeatsStepperProps {
  value: number;
  onChange: (value: number) => void;
  min?: number;
}

export function SeatsStepper({ value, onChange, min = 0 }: SeatsStepperProps) {
  return (
    <div className="flex items-center rounded-lg border border-white/10 bg-white/5">
      <button
        type="button"
        onClick={() => onChange(Math.max(min, value - 1))}
        className="px-3 py-2.5 text-lg text-slate-400 transition-colors hover:text-white"
        aria-label="Меньше"
      >
        −
      </button>
      <span className="flex-1 text-center text-sm font-medium">{value}</span>
      <button
        type="button"
        onClick={() => onChange(value + 1)}
        className="px-3 py-2.5 text-lg text-slate-400 transition-colors hover:text-white"
        aria-label="Больше"
      >
        +
      </button>
    </div>
  );
}