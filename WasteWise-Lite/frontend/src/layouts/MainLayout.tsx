import { NavLink, Outlet } from "react-router-dom";

const NAV = [
  ["/", "Dashboard"], ["/products", "Products"], ["/inventory", "Inventory"], ["/sales", "Sales History"],
  ["/forecast", "Demand Forecast"], ["/expiry-risk", "Expiry Risk"], ["/recommendations", "Recommendations"],
  ["/waste", "Waste Reports"], ["/models", "Model Metrics"],
] as const;

export default function MainLayout() {
  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">🥬 WasteWise <span>AI</span></div>
        <nav>
          {NAV.map(([to, label]) => (
            <NavLink key={to} to={to} end={to === "/"} className={({ isActive }) => (isActive ? "active" : "")}>{label}</NavLink>
          ))}
        </nav>
        <div className="sidebar-foot"><div className="muted small">Demo data from CSV files</div></div>
      </aside>
      <main className="content"><Outlet /></main>
    </div>
  );
}
