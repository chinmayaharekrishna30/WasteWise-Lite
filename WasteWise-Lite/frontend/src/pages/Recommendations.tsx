import { useState } from "react";
import { Alert, Badge, Card, Loading, PageHeader } from "../components/common/ui";
import { useAsync } from "../hooks/useAsync";
import { decideRecommendation, generateRecommendations, listRecommendations } from "../services/predictions";
import type { Recommendation } from "../types";
import { money, num } from "../utils/format";

function RecCard({ r, canDecide, onChange }: { r: Recommendation; canDecide: boolean; onChange: () => void }) {
  const [disc, setDisc] = useState<number>(r.suggested_discount_pct ?? 10);
  const [err, setErr] = useState<string | null>(null);
  const act = async (s: "APPROVED" | "REJECTED" | "MODIFIED") => {
    try { await decideRecommendation(r.recommendation_id, s, s === "MODIFIED" ? disc : undefined); onChange(); }
    catch (e: any) { setErr(e.message); }
  };
  const bestDisc = r.suggested_discount_pct;
  return (
    <div className="rec-card">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <strong>Batch #{r.batch_id} · {r.action_type.replace("_", " ")}{bestDisc ? ` · ${bestDisc}% off` : ""}</strong>
        <Badge level={r.status} />
      </div>
      <p>{r.rationale}</p>
      {r.scenarios.length > 0 && (
        <div className="scenario-grid">
          {r.scenarios.map(s => (
            <div key={s.discount_pct} className={`scenario ${s.discount_pct === bestDisc || (!bestDisc && s.discount_pct === 0) ? "best" : ""} ${s.feasible === false ? "infeasible" : ""}`}>
              <strong>{s.discount_pct}% off</strong><br />
              Sold {num(s.units_sold)} · Rev {money(s.revenue)}<br />Margin {money(s.margin)}
              {s.feasible === false && <><br /><em>below min margin</em></>}
            </div>))}
        </div>)}
      {r.scenarios[0]?.source && <p className="muted small">Scenario source: {r.scenarios[0].source} (simulated – not learned elasticity)</p>}
      {canDecide && r.status === "PENDING" && r.action_type !== "INSPECT_REMOVE" && (
        <div className="row">
          <button className="btn primary small" onClick={() => act("APPROVED")}>Approve</button>
          <button className="btn danger small" onClick={() => act("REJECTED")}>Reject</button>
          <input type="number" min={0} max={50} value={disc} onChange={e => setDisc(+e.target.value)} style={{ width: 70 }} />
          <button className="btn small" onClick={() => act("MODIFIED")}>Modify discount</button>
        </div>)}
      {canDecide && r.status === "PENDING" && r.action_type === "INSPECT_REMOVE" && (
        <button className="btn danger small" onClick={() => act("APPROVED")}>Acknowledge – removing stock</button>)}
      {err && <Alert kind="error">{err}</Alert>}
    </div>
  );
}

export default function Recommendations() {
  const [tab, setTab] = useState<"PENDING" | "">("PENDING");
  const [msg, setMsg] = useState<string | null>(null);
  const recs = useAsync(() => listRecommendations(tab), [tab]);
  const gen = async () => {
    try { const r = await generateRecommendations(50); setMsg(`${r.created} new recommendation(s) generated.`); recs.reload(); }
    catch (e: any) { setMsg(e.message); }
  };
  return (
    <>
      <PageHeader title="Recommendations" subtitle="Approve, reject or modify. Expired stock is never discounted – it is flagged for removal."
        actions={<>
          <select value={tab} onChange={e => setTab(e.target.value as any)}>
            <option value="PENDING">Pending</option><option value="">History (all)</option></select>
          <button className="btn primary" onClick={gen}>Generate recommendations</button></>} />
      {msg && <Alert>{msg}</Alert>}
      {recs.loading && !recs.data ? <Loading error={recs.error} /> :
        recs.data?.length ? recs.data.map(r => <RecCard key={r.recommendation_id} r={r} canDecide={true} onChange={recs.reload} />)
          : <Card><span className="muted">No recommendations. Click “Generate recommendations”.</span></Card>}
    </>
  );
}
