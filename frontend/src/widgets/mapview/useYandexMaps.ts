import { useEffect, useState } from "react";

const SCRIPT_ID = "yandex-maps-api";

export function useYandexMaps(apiKey: string): boolean {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (window.ymaps) {
      window.ymaps.ready(() => setReady(true));
      return;
    }

    const existing = document.getElementById(SCRIPT_ID);
    if (existing) {
      const check = setInterval(() => {
        if (window.ymaps) {
          clearInterval(check);
          window.ymaps.ready(() => setReady(true));
        }
      }, 50);
      return () => clearInterval(check);
    }

    const script = document.createElement("script");
    script.id = SCRIPT_ID;
    script.src = `https://api-maps.yandex.com/2.1/?apikey=${apiKey}&lang=ru_RU`;
    script.type = "text/javascript";
    script.onload = () => {
      window.ymaps.ready(() => setReady(true));
    };
    document.head.appendChild(script);
  }, [apiKey]);

  return ready;
}