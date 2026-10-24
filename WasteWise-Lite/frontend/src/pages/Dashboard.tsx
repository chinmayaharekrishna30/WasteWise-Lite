import { Card, Kpi, Loading, PageHeader } from "../components/common/ui";
import LineChartCard from "../components/charts/LineChartCard";
import DataTable from "../components/tables/DataTable";
import { useAsync } from "../hooks/useAsync";
import { getSummary } from "../services/inventory";
import { money, num } from "../utils/format";

export default function Dashboard() {
  const { data: s, error, loading } = useAsync(getSummary);
  if (loading || !s) return <Loading error={error} />;
  return (
    <>
      <PageHeader title="Dashboard" subtitle="Predicted risk and actual waste are shown separately." />
      <div className="grid k4">
        <Kpi label="Inventory value (at cost)" value={money(s.inventory_value)} hint={`${s.active_batches} active batches`} />
        <Kpi tone="warn" label="Units at expiry risk (predicted)" value={num(s.expiry_risk_units_predicted)}
             hint={`≈ ${money(s.expiry_risk_cost_predicted)} · ${s.high_risk_batches} HIGH batches`} />
        <Kpi tone="bad" label="Actual waste, last 30 days" value={money(s.waste_cost_actual_30d)} hint={`${num(s.waste_units_actual_30d)} units recorded`} />
        <Kpi tone="info" label="Predicted demand, next 7 days" value={num(s.predicted_demand_7d)} hint="units, all products" />
        <Kpi tone="bad" label="Expired units still on hand" value={num(s.expired_units_on_hand)} hint="inspect & remove – never sell" />
      </div>
      <div className="grid two">
        <Card title="Units sold vs actual waste (last 30 days)">
          <LineChartCard data={s.trend} xKey="date" series={[
            { key: "units_sold", label: "Units sold", color: "#16a34a" },
            { key: "waste_units", label: "Waste units", color: "#dc2626" }]} />
        </Card>
        <Card title={`Low-stock alerts (${s.low_stock_alerts.length})`}>
          <DataTable rows={s.low_stock_alerts} empty="No low-stock alerts 🎉" columns={[
            { header: "Product", render: r => r.product_name },
            { header: "Stock", align: "right", render: r => num(r.stock) },
            { header: "7-day forecast", align: "right", render: r => num(r.forecast_7d) }]} />
        </Card>
      </div>
      <p className="muted small">Models: forecast {s.model_versions.forecast} · expiry-risk {s.model_versions.expiry_risk}</p>
    </>
  );
}
