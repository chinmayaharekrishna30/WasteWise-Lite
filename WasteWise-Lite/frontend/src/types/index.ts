export type Role = "admin" | "store_manager" | "inventory_staff" | "analyst";

export interface User { user_id: number; name: string; email: string; role: Role }

export interface Product {
  product_id: number; sku: string; product_name: string; category: string;
  shelf_life_days: number; selling_price: number; unit_cost: number; stock_on_hand: number;
}

export interface Batch {
  batch_id: number; product_id: number; category: string; received_at: string; expiry_date: string;
  initial_quantity: number; quantity_remaining: number; days_to_expiry: number;
  avg_daily_sales_7d: number; expected_demand_before_expiry: number; unit_price: number;
  unit_cost: number; discount_pct: number;
}

export interface RiskBatch extends Batch {
  expiry_risk_probability: number; expected_surplus_units: number;
  risk_level: "LOW" | "MEDIUM" | "HIGH" | "EXPIRED"; model_version: string; reason: string;
}

export interface Summary {
  inventory_value: number; active_batches: number;
  expiry_risk_units_predicted: number; expiry_risk_cost_predicted: number; high_risk_batches: number;
  expired_units_on_hand: number; waste_units_actual_30d: number; waste_cost_actual_30d: number;
  predicted_demand_7d: number;
  low_stock_alerts: { product_id: number; product_name: string; stock: number; forecast_7d: number }[];
  trend: { date: string; units_sold: number; waste_units: number }[];
  model_versions: { forecast: string; expiry_risk: string };
}

export interface Forecast {
  product_id: number; product_name: string; horizon_days: number; total_predicted_units: number;
  daily: { date: string; predicted_units: number }[];
  history: { date: string; units_sold: number }[]; model_version: string;
}

export interface Scenario {
  discount_pct: number; units_sold: number; revenue: number; margin: number;
  net_value?: number; feasible?: boolean; unsold_units?: number; source?: string;
}

export interface Recommendation {
  recommendation_id: number; batch_id: number;
  action_type: "DISCOUNT" | "REDUCE_REPLENISHMENT" | "TRANSFER" | "INSPECT_REMOVE" | "NONE";
  suggested_discount_pct: number | null; expected_units_sold: number | null;
  expected_revenue: number | null; expected_margin: number | null; rationale: string;
  scenarios: Scenario[]; status: "PENDING" | "APPROVED" | "REJECTED" | "MODIFIED";
  final_discount_pct: number | null; decided_at: string | null; created_at: string | null;
}

export interface SaleRow {
  product_id: number; date: string; category: string; opening_stock: number; units_received: number;
  units_sold: number; unit_price: number; discount_pct: number; waste_units: number; stockout_flag: number;
}

export interface WasteRow {
  waste_id: number; product_id: number; product_name: string; batch_id: number | null;
  waste_date: string; units_wasted: number; waste_cost: number; reason: string | null;
}
