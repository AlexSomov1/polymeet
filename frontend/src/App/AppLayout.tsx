import { Outlet } from "react-router-dom";
import { Navbar } from "@/widgets/navbar/Navbar";
import { FilterSidebar } from "@/widgets/filters/FilterSidebar";

export function AppLayout() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <Navbar />
      <div className="mx-auto flex max-w-[1400px] gap-6 px-6 py-6">
        <aside className="hidden w-64 shrink-0 lg:block">
          <FilterSidebar />
        </aside>
        <main className="min-w-0 flex-1">
          <Outlet />
        </main>
      </div>
    </div>
  );
}