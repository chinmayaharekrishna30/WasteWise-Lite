export const money = (n: number) => "₹" + Math.round(n).toLocaleString("en-IN");
export const num = (n: number, d = 0) => n.toLocaleString("en-IN", { maximumFractionDigits: d });
export const pct = (n: number) => `${Math.round(n * 100)}%`;

export function downloadCsv(filename: string, rows: Record<string, unknown>[]) {
  if (!rows.length) return;
  const cols = Object.keys(rows[0]);
  const esc = (v: unknown) => `"${String(v ?? "").replace(/"/g, '""')}"`;
  const csv = [cols.join(","), ...rows.map(r => cols.map(c => esc(r[c])).join(","))].join("\n");
  const url = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
  const a = document.createElement("a");
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}
