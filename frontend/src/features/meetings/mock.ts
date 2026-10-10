import type { Meeting } from "../../shared/api/types";

export const mockMeetings: Meeting[] = [
  {
    id: 1,
    title: "Настолки в «Кубе»",
    category: "games",
    starts_at: "2026-10-13T18:30:00+03:00",
    address: "Клуб «Куб», Литейный 12",
    lat: 59.9437, lon: 30.3506,
    geo_status: "resolved",
    capacity: 6, accepted_count: 3,
    status: "published",
    distance_km: 1.9,
  },
  // ...волейбол, концерт, лекция
];