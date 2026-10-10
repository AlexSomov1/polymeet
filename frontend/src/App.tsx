
import './App.css'
import { mockMeetings } from "./features/meetings/mock";

export default function App() {
return (
    <div className="min-h-screen bg-base p-10">
      <h1 className="text-2xl font-bold">Contract test</h1>
      <pre className="mt-4 overflow-auto rounded-lg bg-raised p-4 text-xs text-mute">
        {JSON.stringify(mockMeetings[0], null, 2)}
      </pre>
    </div>
  );
}