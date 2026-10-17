const MIN_RADIUS = 1;
const MAX_RADIUS = 50;

interface RadiusSliderProps {
  value: number;
  onChange: (value: number) => void;
}

export function RadiusSlider({ value, onChange }: RadiusSliderProps) {
  const fill = ((value - MIN_RADIUS) / (MAX_RADIUS - MIN_RADIUS)) * 100;

  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <span className="text-sm text-slate-300">Радиус от меня</span>
        <span className="text-sm font-semibold text-white">{value} км</span>
      </div>
      <input
        type="range"
        min={MIN_RADIUS}
        max={MAX_RADIUS}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="h-1.5 w-full cursor-pointer appearance-none rounded-full outline-none [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-white [&::-webkit-slider-thumb]:shadow-[0_0_8px_rgba(96,165,250,.9)]"
        style={{
          background: `linear-gradient(to right, #3b82f6 ${fill}%, rgba(255,255,255,.12) ${fill}%)`,
        }}
      />
    </div>
  );
}