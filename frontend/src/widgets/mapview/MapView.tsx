import { YMaps, Map, Placemark, Clusterer } from "@pbe/react-yandex-maps";
import type { Meeting } from "@/features/meetings/mock";

interface MapViewProps {
  meetings: Meeting[];
  onMeetingClick?: (id: string) => void;
}

export function MapView({ meetings, onMeetingClick }: MapViewProps) {
  const defaultState = {
    center: [59.9343, 30.3351], // St. Petersburg
    zoom: 11,
  };

  return (
    <div className="h-125 w-full overflow-hidden rounded-xl border border-white/10">
      <YMaps
        query={{
          apikey: "YOUR_API_KEY_HERE", // we'll handle this in Step 6
          lang: "ru_RU",
        }}
      >
        <Map
          defaultState={defaultState}
          width="100%"
          height="100%"
          options={{
            suppressMapOpenBlock: true, // removes "Open in Yandex Maps" button
            yandexMapDisablePoiInteractivity: true,
          }}
          modules={["templateLayoutFactory", "clusterer.addon.balloon"]}
        >
          <Clusterer
            options={{
              preset: "islands#invertedVioletClusterIcons",
              groupByCoordinates: false,
            }}
          >
            {meetings.map((meeting) => (
              <Placemark
                key={meeting.id}
                geometry={[meeting.lat, meeting.lng]}
                options={{
                  preset: "islands#blueDotIcon",
                }}
                properties={{
                  hintContent: meeting.title,
                  balloonContent: `<strong>${meeting.title}</strong><br/>${meeting.address}`,
                }}
                onClick={() => onMeetingClick?.(meeting.id)}
              />
            ))}
          </Clusterer>
        </Map>
      </YMaps>
    </div>
  );
}