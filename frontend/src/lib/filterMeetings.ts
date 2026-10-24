import type { Meeting } from "../features/meetings/mock";
import type { FiltersState } from "../features/meetings/filters/categories";

/**
 * Pure function — no React, no side effects.
 * filters === null means "nothing applied yet" → only search applies.
 */
export function filterMeetings(
  meetings: Meeting[],
  filters: FiltersState | null,
  query: string
): Meeting[] {
  const q = query.trim().toLowerCase();

  return meetings.filter((m) => {
    if (filters) {
      if (!filters.categories[m.categoryId]) return false;
      if (m.distanceKm > filters.radiusKm) return false;
      if (m.freeSeats < filters.minSeats) return false;
      if (filters.date && !m.date.startsWith(filters.date)) return false;
    }

    if (
      q &&
      !m.title.toLowerCase().includes(q) &&
      !m.address.toLowerCase().includes(q)
    ) {
      return false;
    }

    return true;
  });
}