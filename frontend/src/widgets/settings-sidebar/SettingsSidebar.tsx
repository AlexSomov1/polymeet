import { User, GraduationCap, Bell, MapPin, Shield, LogOut } from "lucide-react";
import { cn } from "@/lib/utils";

export type SettingsTab =
  | "profile"
  | "verification"
  | "notifications"
  | "privacy"
  | "security";

const TABS: { id: SettingsTab; label: string; icon: typeof User }[] = [
  { id: "profile", label: "Профиль", icon: User },
  { id: "verification", label: "Верификация студента", icon: GraduationCap },
  { id: "notifications", label: "Уведомления", icon: Bell },
  { id: "privacy", label: "Приватность и Геолокация", icon: MapPin },
  { id: "security", label: "Безопасность", icon: Shield },
];

interface SettingsSidebarProps {
  activeTab: SettingsTab;
  onTabChange: (tab: SettingsTab) => void;
  onLogout: () => void;
}

export function SettingsSidebar({ activeTab, onTabChange, onLogout }: SettingsSidebarProps) {
  return (
    <nav className="flex w-full flex-col gap-1 lg:w-64">
      {TABS.map(({ id, label, icon: Icon }) => {
        const isActive = activeTab === id;
        return (
          <button
            key={id}
            onClick={() => onTabChange(id)}
            className={cn(
              "flex items-center gap-3 rounded-lg px-4 py-3 text-sm font-medium transition-colors",
              isActive
                ? "bg-blue-600 text-white"
                : "text-slate-400 hover:bg-white/5 hover:text-slate-200"
            )}
          >
            <Icon size={18} />
            {label}
          </button>
        );
      })}

      <button
        onClick={onLogout}
        className="mt-4 flex items-center gap-3 rounded-lg px-4 py-3 text-sm font-medium text-red-400 transition-colors hover:bg-red-500/10"
      >
        <LogOut size={18} />
        Выйти из аккаунта
      </button>
    </nav>
  );
}