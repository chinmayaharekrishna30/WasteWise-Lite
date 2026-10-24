import { ReactNode } from "react";

export interface Column<T> { header: string; render: (row: T) => ReactNode; align?: "right" }

export default function DataTable<T>({ rows, columns, empty = "No records" }:
  { rows: T[]; columns: Column<T>[]; empty?: string }) {
  if (!rows.length) return <div className="muted pad">{empty}</div>;
  return (
    <div className="table-wrap">
      <table>
        <thead><tr>{columns.map(c => <th key={c.header} className={c.align}>{c.header}</th>)}</tr></thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i}>{columns.map(c => <td key={c.header} className={c.align}>{c.render(r)}</td>)}</tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
