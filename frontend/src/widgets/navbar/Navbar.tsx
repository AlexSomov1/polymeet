import { NavLink } from "react-router-dom";
import { CalendarDays, Heart, Settings2, Bell, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const tabs = [
  { to: "/", label: "Встречи", icon: CalendarDays },
  { to: "/my", label: "Мои события", icon: Heart },
  { to: "/moderation", label: "настройки", icon: Settings2 },
];

export function Navbar() {
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/80 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-[1400px] items-center gap-6 px-6">
        {/* Logo: plain wordmark like the design */}
        <NavLink to="/" className="text-[15px] font-medium tracking-tight text-foreground">
          PolyMeet
        </NavLink>

        {/* Tabs */}
        <nav className="flex items-center gap-1">
          {tabs.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to}>
              {({ isActive }) => (
                <Button
                  variant="ghost"
                  size="sm"
                  className={
                    isActive
                      ? "gap-2 rounded-full bg-secondary text-foreground hover:bg-secondary"
                      : "gap-2 rounded-full text-muted-foreground hover:text-foreground"
                  }
                >
                  <Icon className="size-4" />
                  {label}
                </Button>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Right side */}
        <div className="ml-auto flex items-center gap-4">
          {/* Notifications */}
          <button className="relative rounded-full p-2 text-muted-foreground transition hover:bg-secondary hover:text-foreground">
            <Bell className="size-4" />
            <span className="absolute right-1 top-1 size-1.5 rounded-full bg-primary" />
          </button>

          {/* Reliability: label on top, green value below */}
          <div className="hidden flex-col items-end leading-tight sm:flex">
            <span className="text-[11px] text-muted-foreground">надёжность</span>
            <span className="text-[13px] font-semibold text-success">
              96% · 12 встреч
            </span>
          </div>

          {/* Avatar: bordered circle with user icon */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button className="grid size-8 place-items-center rounded-full border border-border text-muted-foreground transition hover:text-foreground">
                <User className="size-4" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-48">
              <DropdownMenuLabel>Привет, GR</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem>
                <User className="mr-2 size-4" /> Профиль
              </DropdownMenuItem>
              <DropdownMenuItem>
                <Settings2 className="mr-2 size-4" /> Настройки
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem className="text-danger focus:text-danger">
                Выйти
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  );
}