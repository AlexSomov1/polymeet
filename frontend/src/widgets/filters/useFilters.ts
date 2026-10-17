import { useMemo, useState } from "react";
import {
  allCategoriesSelected,
  type CategoryId,
  type FiltersState,
} from "@/features/meetings/filters/categories";

export const defaultFilters: FiltersState = {
  date: "",
  minSeats: 1,
  radiusKm: 10,
  categories: allCategoriesSelected(),
};

export function useFilters() {
  const [filters, setFilters] = useState<FiltersState>(defaultFilters);

  const set = <K extends keyof FiltersState>(key: K, value: FiltersState[K]) =>
    setFilters((f) => ({ ...f, [key]: value }));

  const toggleCategory = (id: CategoryId) =>
    setFilters((f) => ({
      ...f,
      categories: { ...f.categories, [id]: !f.categories[id] },
    }));

  const reset = () => setFilters(defaultFilters);

  const activeCount = useMemo(() => {
    const cats = Object.values(filters.categories).filter(Boolean).length;
    return (
      (filters.date ? 1 : 0) +
      (filters.minSeats > 0 ? 1 : 0) +
      (filters.radiusKm !== defaultFilters.radiusKm ? 1 : 0) +
      cats
    );
  }, [filters]);

  return { filters, set, toggleCategory, reset, activeCount };
}