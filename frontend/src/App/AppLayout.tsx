import { useState } from "react";
import { Outlet } from "react-router-dom";
import { Navbar } from "@/widgets/navbar/Navbar";
import { FilterSidebar} from "@/widgets/filters/FilterSidebar";
import type { FiltersState } from "@/features/meetings/filters/categories";

export function AppLayout() {
  const [appliedFilters, setAppliedFilters] = useState<FiltersState | null>(null);

  const handleApply = (filters: FiltersState) => {
    setAppliedFilters(filters);
    
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Navbar />
      <div className="mx-auto flex max-w-350 flex-col gap-6 px-4 py-6 lg:flex-row">
        <aside className="w-full shrink-0 lg:w-75">
          <FilterSidebar onApply={handleApply} />
        </aside>
        <main className="min-w-0 flex-1">
          <Outlet context={{ appliedFilters }} />
        </main>
      </div>
    </div>
  );
}