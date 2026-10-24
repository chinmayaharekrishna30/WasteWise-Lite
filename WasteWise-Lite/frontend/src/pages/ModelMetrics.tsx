import { Card, Kpi, Loading, PageHeader } from "../components/common/ui";
import BarChartCard from "../components/charts/BarChartCard";
import DataTable from "../components/tables/DataTable";
import { useAsync } from "../hooks/useAsync";
import { modelMetrics } from "../services/predictions";

export default function ModelMetrics() {
  const { data, error, loading } = useAsync(modelMetrics);
  if (loading || !data) return <Loading error={error} />;
  const f = data.metrics.forecast, r = data.metrics.expiry_risk;
  const imp = r?.feature_importance
    ? Object.entries(r.feature_importance as Record<string, number>).slice(0, 8).map(([feature, value]) => ({ feature, value })) : [];
  return (
    <>
      <PageHeader title="Model Metrics" subtitle="Evaluated on a held-out, chronologically LATER test period." />
      <div className="grid k4">
        <Kpi label="Active forecast model" value={data.active.forecast} hint={f?.algorithm} />
        <Kpi tone="info" label="Active expiry-risk model" value={data.active.expiry_risk} hint={r?.algorithm} />
        {f && <><Kpi label="Forecast MAE (test)" value={String(f.model.test.MAE)} hint={`baseline ${f.baseline_last7_mean.test.MAE}`} />
          <Kpi label="Forecast RMSE (test)" value={String(f.model.test.RMSE)} hint={`baseline ${f.baseline_last7_mean.test.RMSE}`} />
          <Kpi tone="warn" label="Forecast WAPE (test)" value={`${(f.model.test.WAPE * 100).toFixed(1)}%`} hint={`baseline ${(f.baseline_last7_mean.test.WAPE * 100).toFixed(1)}%`} /></>}
        {r && <><Kpi label="Risk precision (test)" value={String(r.model.test.precision)} />
          <Kpi label="Risk recall (test)" value={String(r.model.test.recall)} />
          <Kpi label="Risk PR-AUC (test)" value={String(r.model.test.pr_auc)} hint={`rule baseline ${r.baseline_rule_surplus_gt_0.test.pr_auc}`} /></>}
      </div>
      {r?.label_note && <div className="alert">⚠ {r.label_note}</div>}
      <div className="grid two">
        <Card title="Expiry-risk feature importance">
          {imp.length ? <BarChartCard data={imp} xKey="feature" yKey="value" color="#2563eb" /> : <span className="muted">Not available</span>}
        </Card>
        <Card title="Registered model runs">
          <DataTable rows={data.runs} empty="Run scripts/import_dataset.py after training to register runs" columns={[
            { header: "Model", render: m => m.model_name }, { header: "Version", render: m => m.model_version },
            { header: "Algorithm", render: m => m.algorithm }, { header: "Trained", render: m => m.trained_at.slice(0, 10) },
            { header: "Active", render: m => (m.is_active ? "Yes" : "No") }]} />
        </Card>
      </div>
    </>
  );
}
