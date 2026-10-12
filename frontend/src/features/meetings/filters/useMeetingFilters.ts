import { useSearchParams } from "react-router-dom";
import { meetingFiltersSchema, type MeetingFilters } from "./schema";

const DEFAULTS: MeetingFilters = { minFreeSeats: 0, radiusKm: 10, categories: [] };

export function useMeetingFilters() {
  const [searchParams, setSearchParams] = useSearchParams();

  const filters = meetingFiltersSchema.parse({
    date: searchParams.get("date") ?? undefined,
    minFreeSeats: searchParams.get("minSeats") ?? undefined,
    radiusKm: searchParams.get("radius") ?? undefined,
    categories: searchParams.get("cats")?.split(",").filter(Boolean) ?? [],
  });

  const setFilters = (next: Partial<MeetingFilters>) => {
    const merged = { ...filters, ...next };
    const params = new URLSearchParams();
    if (merged.date) params.set("date", merged.date);
    if (merged.minFreeSeats) params.set("minSeats", String(merged.minFreeSeats));
    if (merged.radiusKm !== DEFAULTS.radiusKm) params.set("radius", String(merged.radiusKm));
    if (merged.categories.length) params.set("cats", merged.categories.join(","));
    setSearchParams(params, { replace: true });
  };

  return { filters, setFilters };
}