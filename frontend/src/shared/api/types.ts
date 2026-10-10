// Contract derived from the team's README (ER diagram §3.4 + API table §3.3).
// When the backend implements GET /meetings, regenerate schema.ts from
// openapi.json and reconcile these types with the generated ones.

export type GeoStatus = "pending" | "resolved" | "failed";
export type MeetingStatus = "draft" | "published" | "finished" | "cancelled";
export type Category =
  | "lecture"   // Лекция
  | "games"     // Игры
  | "concert"   // Концерт
  | "sport"     // Спорт
  | "walk"      // Прогулка
  | "other";    // Другое

export interface Meeting {
  id: number;
  title: string;
  category: Category;
  starts_at: string;        // ISO 8601, e.g. "2026-10-14T18:30:00+03:00"
  address: string;          // human-readable, e.g. "Клуб «Куб», Литейный 12"
  lat: number | null;       // null while geo_status = "pending"
  lon: number | null;
  geo_status: GeoStatus;
  capacity: number;         // 2..100
  accepted_count: number;
  status: MeetingStatus;
  distance_km: number | null; // computed by backend when lat/lon given
}

// GET /api/v1/meetings?lat&lon&radius_km&category&date&cursor
export interface MeetingsResponse {
  items: Meeting[];
  next_cursor: string | null; // null = no more pages
}