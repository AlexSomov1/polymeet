import { NavLink, useNavigate } from "react-router-dom";
import {
  CalendarDays,
  Heart,
  Settings2,
  Bell,
  User,
  Plus,
  Menu,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const tabs = [
  { to: "/", label: "Встречи", icon: CalendarDays },
  { to: "/my", label: "Мои события", icon: Heart },
  { to: "/moderation", label: "настройки", icon: Settings2 },
];

export function Navbar() {
  const navigate = useNavigate();

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/80 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-350 items-center gap-3 px-4 md:gap-6 md:px-6">
        {/* Logo — always visible */}
        <NavLink
          to="/"
          className="text-[15px] font-medium tracking-tight text-foreground"
        >
          PolyMeet
        </NavLink>

        {/* Tabs — desktop only */}
        <nav className="hidden items-center gap-1 md:flex">
          {tabs.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to}>
              {({ isActive }) => (
                <Button
                  variant="ghost"
                  size="sm"
                  className={
                    isActive
                      ? "gap-2 rounded-full bg-secondary text-foreground hover:bg-secondary"
                      : "gap-2 rounded-full text-muted-foreground hover:bg-blue-600/10 hover:text-blue-400"
                  }
                >
                  <Icon className="size-4" />
                  {label}
                </Button>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Right side — pushed to the far edge */}
        <div className="ml-auto flex items-center gap-2 md:gap-4">
          {/* Create: icon-only on mobile, full button on desktop */}
          <button
            onClick={() => navigate("/create")}
            className="grid size-9 place-items-center rounded-xl bg-linear-to-r from-indigo-600 to-blue-500 text-white shadow-lg shadow-indigo-900/40 transition-transform hover:scale-[1.05] active:scale-[0.95] md:hidden"
            aria-label="Создать встречу"
          >
            <Plus size={18} strokeWidth={2.5} />
          </button>
          <button
            onClick={() => navigate("/create")}
            className="hidden items-center gap-2 rounded-xl bg-linear-to-r from-indigo-600 to-blue-500 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-900/40 transition-transform hover:scale-[1.03] active:scale-[0.97] md:flex"
          >
            <Plus size={16} strokeWidth={2.5} />
            Создать встречу
          </button>

          {/* Bell — always visible */}
          <button className="relative rounded-full p-2 text-muted-foreground transition hover:bg-secondary hover:text-foreground">
            <Bell className="size-4" />
            <span className="absolute right-1 top-1 size-1.5 rounded-full bg-primary" />
          </button>

          {/* Reliability — hidden on small phones, visible from sm */}
          <div className="hidden flex-col items-end leading-tight sm:flex">
            <span className="text-[11px] text-muted-foreground">надёжность</span>
            <span className="text-[13px] font-semibold text-success">
              96% · 12 встреч
            </span>
          </div>

          {/* Avatar — always visible */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button className="grid size-8 place-items-center rounded-full border border-border text-muted-foreground transition hover:text-blue-500">
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
              <DropdownMenuItem className="text-danger focus:text-white">
                Выйти
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          {/* Hamburger — mobile only, holds the hidden tabs */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                className="rounded-full p-2 text-muted-foreground transition hover:bg-secondary hover:text-foreground md:hidden"
                aria-label="Меню"
              >
                <Menu className="size-5" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-48">
              {tabs.map(({ to, label, icon: Icon }) => (
                <DropdownMenuItem key={to} asChild>
                  <NavLink
                    to={to}
                    className="flex cursor-pointer items-center gap-2"
                  >
                    <Icon className="size-4" /> {label}
                  </NavLink>
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  );
}