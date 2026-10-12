import { z } from "zod";

export const CATEGORIES = [
  { value: "lecture", label: "Лекция" },
  { value: "games", label: "Игры" },
  { value: "concert", label: "Концерт" },
  { value: "sport", label: "Спорт" },
  { value: "walk", label: "Прогулка" },
  { value: "other", label: "Другое" },
] as const;

export const categoryValues = CATEGORIES.map((c) => c.value) as [
  string,
  ...string[],
];

export const meetingFiltersSchema = z.object({
  date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional(), // ISO date
  minFreeSeats: z.number().int().min(0).max(100).catch(0),
  radiusKm: z.number().min(1).max(50).catch(10),
  categories: z.array(z.enum(categoryValues)).catch([]), // [] = all
});

export type MeetingFilters = z.infer<typeof meetingFiltersSchema>;