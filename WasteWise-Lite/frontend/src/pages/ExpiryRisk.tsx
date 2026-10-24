import { Badge, Card, Loading, PageHeader } from "../components/common/ui";
import DataTable from "../components/tables/DataTable";
import { useAsync } from "../hooks/useAsync";
import { atRisk } from "../services/predictions";
import { listProducts } from "../services/products";
import { pct } from "../utils/format";

export default function ExpiryRisk() {
  const risk = useAsync(() => atRisk(150));
  const products = useAsync(() => listProducts());
  const name = (id: number) => products.data?.find(p => p.product_id === id)?.product_name ?? `#${id}`;
  return (
    <>
      <PageHeader title="Expiry Risk Monitor" subtitle="Predicted risk only – this is NOT recorded waste. Sorted by risk probability."
                  actions={<button className="btn" onClick={risk.reload}>Refresh</button>} />
      <Card>
        {risk.loading && !risk.data ? <Loading error={risk.error} /> : (
          <DataTable rows={risk.data ?? []} empty="No medium/high-risk batches" columns={[
            { header: "Batch", render: b => `#${b.batch_id}` }, { header: "Product", render: b => name(b.product_id) },
            { header: "Days left", align: "right", render: b => b.days_to_expiry },
            { header: "In stock", align: "right", render: b => b.quantity_remaining },
            { header: "Predicted surplus", align: "right", render: b => b.expected_surplus_units.toFixed(0) },
            { header: "Risk", align: "right", render: b => pct(b.expiry_risk_probability) },
            { header: "Level", render: b => <Badge level={b.risk_level} /> },
            { header: "Why flagged", render: b => <span className="muted small">{b.reason}</span> }]} />)}
      </Card>
    </>
  );
}
