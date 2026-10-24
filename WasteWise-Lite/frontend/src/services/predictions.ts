import { api } from "./api";
import type { Forecast, Recommendation, RiskBatch } from "../types";

export const runForecast = (product_id: number, horizon_days: number, discount_pct = 0) =>
  api.post<Forecast>("/forecast/run", { product_id, horizon_days, discount_pct });

export const atRisk = (limit = 100) => api.get<RiskBatch[]>(`/batches/at-risk?limit=${limit}`);

export const listRecommendations = (status = "") =>
  api.get<Recommendation[]>(`/recommendations${status ? `?status=${status}` : ""}`);
export const generateRecommendations = (limit = 50) =>
  api.post<{ created: number; items: Recommendation[] }>("/recommendations/generate", { limit });
export const decideRecommendation = (id: number, status: "APPROVED" | "REJECTED" | "MODIFIED",
                                     final_discount_pct?: number) =>
  api.patch<Recommendation>(`/recommendations/${id}`, { status, final_discount_pct });

export const modelMetrics = () =>
  api.get<{ active: { forecast: string; expiry_risk: string }; metrics: { forecast: any; expiry_risk: any };
            runs: { run_id: number; model_name: string; model_version: string; algorithm: string;
                    trained_at: string; is_active: boolean }[] }>("/models/metrics");
