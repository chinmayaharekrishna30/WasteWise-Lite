import { useState } from "react";
import { Badge, Card, Loading, PageHeader } from "../components/common/ui";
import DataTable from "../components/tables/DataTable";
import { useAsync } from "../hooks/useAsync";
import { listBatches } from "../services/inventory";
import { listProducts } from "../services/products";

const PAGE = 50;

export default function Inventory() {
  const [status, setStatus] = useState("active");
  const [productId, setProductId] = useState<number | undefined>();
  const [page, setPage] = useState(0);
  const products = useAsync(() => listProducts());
  const batches = useAsync(() => listBatches({ status, product_id: productId, limit: PAGE, offset: page * PAGE }),
                           [status, productId, page]);
  const name = (id: number) => products.data?.find(p => p.product_id === id)?.product_name ?? `#${id}`;
  const total = batches.data?.total ?? 0;

  return (
    <>
      <PageHeader title="Inventory" subtitle="Batches with quantity, expiry date and status." actions={<>
        <select value={productId ?? ""} onChange={e => { setProductId(e.target.value ? +e.target.value : undefined); setPage(0); }}>
          <option value="">All products</option>
          {products.data?.map(p => <option key={p.product_id} value={p.product_id}>{p.product_name}</option>)}
        </select>
        <select value={status} onChange={e => { setStatus(e.target.value); setPage(0); }}>
          <option value="active">Active</option><option value="expired">Expired (on hand)</option>
          <option value="empty">Sold out</option><option value="">All</option>
        </select></>} />
      <Card title={`Batches (${total})`}>
        {batches.loading && !batches.data ? <Loading error={batches.error} /> : (<>
          <DataTable rows={batches.data?.items ?? []} columns={[
            { header: "Batch", render: b => `#${b.batch_id}` }, { header: "Product", render: b => name(b.product_id) },
            { header: "Received", render: b => b.received_at }, { header: "Expiry", render: b => b.expiry_date },
            { header: "Days left", align: "right", render: b => b.days_to_expiry },
            { header: "Remaining", align: "right", render: b => `${b.quantity_remaining} / ${b.initial_quantity}` },
            { header: "Discount", align: "right", render: b => `${b.discount_pct}%` },
            { header: "Status", render: b => b.quantity_remaining === 0 ? <span className="muted">Sold out</span>
              : b.days_to_expiry < 0 ? <Badge level="EXPIRED" /> : b.days_to_expiry <= 2 ? <Badge level="HIGH" />
              : b.days_to_expiry <= 5 ? <Badge level="MEDIUM" /> : <Badge level="LOW" /> }]} />
          <div className="row pad">
            <button className="btn small" disabled={page === 0} onClick={() => setPage(page - 1)}>← Prev</button>
            <span className="muted small">Page {page + 1} of {Math.max(1, Math.ceil(total / PAGE))}</span>
            <button className="btn small" disabled={(page + 1) * PAGE >= total} onClick={() => setPage(page + 1)}>Next →</button>
          </div></>)}
      </Card>
    </>
  );
}
