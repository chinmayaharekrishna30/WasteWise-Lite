import { useState } from "react";
import { Alert, Card, Kpi, PageHeader } from "../components/common/ui";
import LineChartCard from "../components/charts/LineChartCard";
import { useAsync } from "../hooks/useAsync";
import { listProducts } from "../services/products";
import { runForecast } from "../services/predictions";
import type { Forecast } from "../types";
import { num } from "../utils/format";

export default function DemandForecast() {
  const products = useAsync(() => listProducts());
  const [productId, setProductId] = useState<number>(0);
  const [horizon, setHorizon] = useState(7);
  const [discount, setDiscount] = useState(0);
  const [result, setResult] = useState<Forecast | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const run = async () => {
    const id = productId || products.data?.[0]?.product_id;
    if (!id) return;
    setBusy(true); setError(null);
    try { setResult(await runForecast(id, horizon, discount)); } catch (e: any) { setError(e.message); } finally { setBusy(false); }
  };

  const chart = result ? [
    ...result.history.map(h => ({ date: h.date, actual: h.units_sold, forecast: null as number | null })),
    ...result.daily.map(d => ({ date: d.date, actual: null as number | null, forecast: d.predicted_units })),
  ] : [];

  return (
    <>
      <PageHeader title="Demand Forecast" subtitle="Pick a product and horizon; compare history with predicted sales." />
      <Card>
        <div className="form">
          <label>Product
            <select value={productId} onChange={e => setProductId(+e.target.value)}>
              {products.data?.map(p => <option key={p.product_id} value={p.product_id}>{p.product_name}</option>)}
            </select></label>
          <label>Horizon
            <select value={horizon} onChange={e => setHorizon(+e.target.value)}>
              {[7, 14, 21].map(h => <option key={h} value={h}>{h} days</option>)}</select></label>
          <label>What-if discount %
            <input type="number" min={0} max={50} value={discount} onChange={e => setDiscount(+e.target.value)} /></label>
          <button className="btn primary" onClick={run} disabled={busy}>{busy ? "Forecasting…" : "Run forecast"}</button>
        </div>
        {error && <Alert kind="error">{error}</Alert>}
      </Card>
      {result && (<>
        <div className="grid k4">
          <Kpi label={`Predicted demand, ${result.horizon_days} days`} value={num(result.total_predicted_units)} hint={result.product_name} />
          <Kpi tone="info" label="Average per day" value={num(result.total_predicted_units / result.horizon_days, 1)} />
          <Kpi tone="warn" label="Model" value={result.model_version} />
        </div>
        <Card title="Historical sales vs forecast">
          <LineChartCard data={chart} xKey="date" series={[
            { key: "actual", label: "Actual sales", color: "#0f766e" },
            { key: "forecast", label: "Forecast", color: "#f59e0b", dashed: true }]} />
          <p className="muted small">Point forecast only – no uncertainty range yet. The what-if discount uses the learned price feature; treat it as indicative.</p>
        </Card>
      </>)}
    </>
  );
}
