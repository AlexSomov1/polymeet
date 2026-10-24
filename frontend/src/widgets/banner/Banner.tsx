// src/widgets/banner/Banner.tsx
import { Search } from "lucide-react";

interface BannerProps {
  query: string;
  onQueryChange: (q: string) => void;
}

export function Banner({ query, onQueryChange }: BannerProps) {
  return (
    <section
      role="search"
      className="relative overflow-hidden rounded-2xl bg-cover bg-center"
      style={{ backgroundImage: "url(/banner.png)" }}
    >
      {/* Readability overlay — darkens the left where text sits */}
      <div className="absolute inset-0 bg-linear-to-r from-black/80 via-black/40 to-transparent" />

      <div className="relative max-w-130 p-6 sm:p-10">
        <h1 className="text-2xl font-bold leading-tight text-white sm:text-3xl">
          Открывай возможности.
          <br />
          Общайся. Расти.
        </h1>
        <p className="mt-3 text-sm leading-relaxed text-white/80">
          Находи интересные мероприятия, знакомься с новыми людьми
          и создавай собственные события в PolyMeet.
        </p>

        {/* Search */}
        <div className="relative mt-5">
          <Search
            size={16}
            className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-300"
          />
          <input
            type="search"
            value={query}
            onChange={(e) => onQueryChange(e.target.value)}
            placeholder="поиск по названию или адресу"
            aria-label="Поиск по названию или адресу"
            className="w-full rounded-xl border border-white/20 bg-black/60 py-3 pl-11 pr-4 text-sm text-white placeholder:text-slate-400 outline-none transition-colors focus:border-blue-400/70 [&::-webkit-search-cancel-button]:invert"
          />
        </div>
      </div>
    </section>
  );
}