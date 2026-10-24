import { ReactNode } from "react";

export function PageHeader({ title, subtitle, actions }: { title: string; subtitle?: string; actions?: ReactNode }) {
  return (
    <div className="page-header">
      <div><h1>{title}</h1>{subtitle && <p className="muted">{subtitle}</p>}</div>
      <div className="row">{actions}</div>
    </div>
  );
}

export function Card({ title, children, className = "" }: { title?: string; children: ReactNode; className?: string }) {
  return <section className={`card ${className}`}>{title && <h3>{title}</h3>}{children}</section>;
}

export function Kpi({ label, value, hint, tone = "" }: { label: string; value: string; hint?: string; tone?: string }) {
  return (
    <div className={`kpi ${tone}`}>
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">{value}</div>
      {hint && <div className="kpi-hint">{hint}</div>}
    </div>
  );
}

export function Badge({ level }: { level: string }) {
  return <span className={`badge badge-${level.toLowerCase()}`}>{level}</span>;
}

export function Loading({ error }: { error?: string | null }) {
  return error ? <div className="alert error">{error}</div> : <div className="muted">Loading…</div>;
}

export function Alert({ kind = "info", children }: { kind?: "info" | "error" | "ok"; children: ReactNode }) {
  return <div className={`alert ${kind}`}>{children}</div>;
}
