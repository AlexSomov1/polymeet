// Minimal Yandex Maps API types — expand as needed
export interface YandexMapInstance {
  geoObjects: YandexGeoObjectManager;
  destroy(): void;
}

export interface YandexPlacemark {
  events: {
    add(event: string, callback: () => void): void;
  };
}

export interface YandexClusterer {
  add(objects: YandexPlacemark[]): void;
}

export interface YandexGeoObjectManager {
  removeAll(): void;
  add(object: YandexClusterer | YandexPlacemark): void;
  remove(object: YandexClusterer): void;
}

export interface YandexMapsAPI {
  ready(callback: () => void): void;
  Map: new (container: HTMLElement, state: Record<string, unknown>) => YandexMapInstance;
  Placemark: new (
    geometry: number[],
    properties: Record<string, string>,
    options: Record<string, string>
  ) => YandexPlacemark;
  Clusterer: new (options: Record<string, unknown>) => YandexClusterer;
}

declare global {
  interface Window {
    ymaps: YandexMapsAPI;
  }
}