// widgets/map-view/MapView.tsx
import type { Meeting } from "@/features/meetings/mock";

export function MapView({ meetings }: { meetings: Meeting[] }) {
  // markers derive from meetings — one pin per meeting, position by coords
  return (
    <div className="h-125 overflow-hidden rounded-xl border border-white/10">
      {/* your map implementation here; markers = meetings.map(...) */}
    </div>
  );
}