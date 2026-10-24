import { Card, Loading, PageHeader } from "../components/common/ui";
import BarChartCard from "../components/charts/BarChartCard";
import DataTable from "../components/tables/DataTable";
import { useAsync } from "../hooks/useAsync";
import { listWaste, wasteSummary } from "../services/inventory";
import { downloadCsv, money } from "../utils/format";

export default function WasteReports() {
  const logs = useAsync(listWaste);
  const summary = useAsync(wasteSummary);
  return (
    <>
      <PageHeader title="Waste Reports" subtitle="ACTUAL recorded waste (not predictions)." actions={
        <button className="btn" onClick={() => downloadCsv("waste_report.csv", (logs.data ?? []) as any)}>Export CSV</button>} />
      <div className="grid two">
        <Card title="Waste cost by product">
          {summary.data ? <BarChartCard data={summary.data} xKey="product_name" yKey="cost" color="#dc2626" /> : <Loading error={summary.error} />}
        </Card>
        <Card title="Recent waste logs">
          {logs.loading && !logs.data ? <Loading error={logs.error} /> : (
            <DataTable rows={(logs.data ?? []).slice(0, 15)} columns={[
              { header: "Date", render: w => w.waste_date }, { header: "Product", render: w => w.product_name },
              { header: "Units", align: "right", render: w => w.units_wasted },
              { header: "Cost", align: "right", render: w => money(w.waste_cost) }]} />)}
        </Card>
      </div>
    </>
  );
}
