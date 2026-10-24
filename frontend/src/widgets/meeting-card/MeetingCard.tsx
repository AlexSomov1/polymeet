import { MapPin, Bookmark, Users } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Meeting } from "@/features/meetings/mock";
import { CATEGORIES } from "@/features/meetings/filters/categories";
import { formatMeetingDate } from "./format";

interface MeetingCardProps {
  meeting: Meeting;
}

export function MeetingCard({ meeting }: MeetingCardProps) {
  const category = CATEGORIES.find((c) => c.id === meeting.categoryId);

  return (
    <article className="overflow-hidden rounded-xl border border-white/10 bg-[#131a30]">
      {/* Image with overlay chips */}
      <div className="relative h-36 bg-cover bg-center" style={{ backgroundImage: `url(${meeting.imageUrl})` }}>
        <div className="absolute inset-0 bg-linear-to-t from-black/70 to-transparent" />
        <div className="absolute left-3 top-3 flex items-center gap-1.5 rounded-md bg-black/60 px-2 py-1 text-[11px] text-white">
          {category && <category.icon size={12} className="text-blue-400" />}
          {category?.label}
        </div>
        <div className="absolute right-3 top-3 rounded-md bg-black/60 px-2 py-1 text-[11px] text-white">
          {formatMeetingDate(meeting.date)}
        </div>
        <button
          className="absolute bottom-3 right-3 rounded-md bg-black/50 p-1.5 text-white/80 transition-colors hover:text-white"
          aria-label="Сохранить"
        >
          <Bookmark size={14} />
        </button>
      </div>

      {/* Body */}
      <div className="p-4">
        <h3 className="text-sm font-semibold text-white">{meeting.title}</h3>

        <div className="mt-2 flex items-center gap-3 text-xs text-slate-400">
          <span className="flex items-center gap-1">
            <MapPin size={12} />
            {meeting.address}
          </span>
          <span className="ml-auto flex items-center gap-1">
            <Users size={12} />
            {meeting.freeSeats} из 6
          </span>
          <span>{meeting.distanceKm} км</span>
        </div>

        <button
          disabled={meeting.isJoined}
          className={cn(
            "mt-4 w-full rounded-lg py-2 text-xs font-semibold transition-colors",
            meeting.isJoined
              ? "cursor-default bg-emerald-600 text-white"
              : "bg-blue-600 text-white hover:bg-blue-500"
          )}
        >
          {meeting.isJoined ? "Вы участвуете" : "Подать заявку"}
        </button>
      </div>
    </article>
  );
}