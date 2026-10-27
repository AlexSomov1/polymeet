import { Search } from "lucide-react";

interface BannerProps {
  query: string;
  onQueryChange: (q: string) => void;
}

export function Banner({ query, onQueryChange }: BannerProps) {
  return (
    <section className="relative mb-6">
      <div className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500">
        <Search size={18} />
      </div>
      <input
        type="text"
        value={query}
        onChange={(e) => onQueryChange(e.target.value)}
        placeholder="поиск по названию или адресу"
        className="w-full rounded-xl border border-white/10 bg-white/5 py-3 pl-11 pr-4 text-sm text-white placeholder:text-slate-600 focus:border-blue-500 focus:outline-none"
      />
    </section>
  );
}