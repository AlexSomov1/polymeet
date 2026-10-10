
import './App.css'
export default function App() {
  return (
    <div className="min-h-screen bg-base p-10">
      <h1 className="text-3xl font-bold text-ink">PolyMeet</h1>
      <p className="mt-2 text-mute">тёплый белый на почти чёрном</p>
      <button className="mt-4 rounded-lg bg-accent px-4 py-2 font-semibold text-base">
        Подать заявку
      </button>
      <div className="mt-4 h-24 w-64 rounded-xl border border-edge bg-raised p-4">
        <span className="text-success">3 МЕСТА</span>{" "}
        <span className="text-warning">8 МЕСТ</span>
      </div>
    </div>
  );
}