import {
  GraduationCap, Gamepad2, Music, Dumbbell, Trees, MoreHorizontal,
} from "lucide-react";

export type CategoryId = "lecture" | "games" | "concert" | "sport" | "walk" | "other";

export const CATEGORIES: { id: CategoryId; label: string; icon: typeof Music }[] = [
  { id: "lecture", label: "Лекция", icon: GraduationCap },
  { id: "games", label: "Игры", icon: Gamepad2 },
  { id: "concert", label: "Концерт", icon: Music },
  { id: "sport", label: "Спорт", icon: Dumbbell },
  { id: "walk", label: "Прогулка", icon: Trees },
  { id: "other", label: "Другое", icon: MoreHorizontal },
];

export interface FiltersState {
  date: string;
  minSeats: number;
  radiusKm: number;
  categories: Record<CategoryId, boolean>;
}

/** All categories on — used as the initial state and for the "Все" chip */
export const allCategoriesSelected = (): Record<CategoryId, boolean> =>
  Object.fromEntries(CATEGORIES.map((c) => [c.id, true])) as Record<CategoryId, boolean>;