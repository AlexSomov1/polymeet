import { useQuery } from "@tanstack/react-query";
import { api } from "./client";
import type { paths } from "./schema";

type HealthReady = paths["/health/ready"]["get"]["responses"][200]["content"]["application/json"];

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: async () => (await api.get<HealthReady>("/health/ready")).data,
    retry: false,
  });
}