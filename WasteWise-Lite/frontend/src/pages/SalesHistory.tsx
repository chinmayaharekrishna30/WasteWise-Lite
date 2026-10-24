import { useState } from "react";
import { Card, Loading, PageHeader } from "../components/common/ui";
import DataTable from "../components/tables/DataTable";
import { useAsync } from "../hooks/useAsync";
import { listProducts, listSales } from "../services/products";

export default function SalesHistory() {
  const [productId, setProductId] = useState<number | undefined>();
  const products = useAsync(() => listProducts());
  const sales = useAsync(() => listSales(productId, 300), [productId]);
  const name = (id: number) => products.data?.find(p => p.product_id === id)?.product_name ?? `#${id}`;

  return (
    <>
      <PageHeader title="Sales History" subtitle="Daily sales, discounts and stock-outs." actions={
        <select value={productId ?? ""} onChange={e => setProductId(e.target.value ? +e.target.value : undefined)}>
          <option value="">All products</option>
          {products.data?.map(p => <option key={p.product_id} value={p.product_id}>{p.product_name}</option>)}
        </select>} />
      <Card>
        {sales.loading && !sales.data ? <Loading error={sales.error} /> : (
          <DataTable rows={sales.data ?? []} columns={[
            { header: "Date", render: r => r.date }, { header: "Product", render: r => name(r.product_id) },
            { header: "Opening", align: "right", render: r => r.opening_stock },
            { header: "Received", align: "right", render: r => r.units_received },
            { header: "Sold", align: "right", render: r => r.units_sold },
            { header: "Price", align: "right", render: r => r.unit_price },
            { header: "Disc %", align: "right", render: r => r.discount_pct },
            { header: "Waste", align: "right", render: r => r.waste_units },
            { header: "Stock-out", render: r => (r.stockout_flag ? "Yes" : "") }]} />)}
      </Card>
    </>
  );
}
