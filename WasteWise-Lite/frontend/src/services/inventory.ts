import { api } from "./api";
import type { Batch, Summary, WasteRow } from "../types";

export const getSummary = () => api.get<Summary>("/dashboard/summary");

export const listBatches = (opts: { product_id?: number; status?: string; limit?: number; offset?: number } = {}) => {
  const p = new URLSearchParams();
  Object.entries(opts).forEach(([k, v]) => v !== undefined && v !== "" && p.set(k, String(v)));
  return api.get<{ total: number; items: Batch[] }>(`/batches?${p}`);
};

export const listWaste = () => api.get<WasteRow[]>("/waste-logs?days=3650&limit=300");
export const wasteSummary = () => api.get<{ product_name: string; units: number; cost: number }[]>("/waste-logs/summary");
