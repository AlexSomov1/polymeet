import { Outlet } from "react-router-dom";
import { Navbar } from "@/widgets/navbar/Navbar";

export function AppLayout() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <Navbar />
      <div className="mx-auto max-w-350 px-4 py-6">
        <Outlet />
      </div>
    </div>
  );
}