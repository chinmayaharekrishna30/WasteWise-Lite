import { useState } from "react";
import { Card, Loading, PageHeader } from "../components/common/ui";
import DataTable from "../components/tables/DataTable";
import { useAsync } from "../hooks/useAsync";
import { listProducts } from "../services/products";
import { money, num } from "../utils/format";

export default function Products() {
  const [q, setQ] = useState("");
  const [category, setCategory] = useState("");
  const { data, error, loading } = useAsync(() => listProducts(q, category), [q, category]);
  return (
    <>
      <PageHeader title="Products" subtitle="Product master with current non-expired stock." actions={<>
        <input placeholder="Search name or SKU…" value={q} onChange={e => setQ(e.target.value)} />
        <select value={category} onChange={e => setCategory(e.target.value)}>
          <option value="">All categories</option>
          {["Bakery", "Beverage", "Dairy", "Produce"].map(c => <option key={c}>{c}</option>)}
        </select></>} />
      <Card>
        {loading && !data ? <Loading error={error} /> : (
          <DataTable rows={data ?? []} columns={[
            { header: "SKU", render: p => p.sku }, { header: "Product", render: p => p.product_name },
            { header: "Category", render: p => p.category },
            { header: "Shelf life (d)", align: "right", render: p => p.shelf_life_days },
            { header: "Price", align: "right", render: p => money(p.selling_price) },
            { header: "Cost", align: "right", render: p => money(p.unit_cost) },
            { header: "Stock on hand", align: "right", render: p => num(p.stock_on_hand) }]} />
        )}
      </Card>
    </>
  );
}
