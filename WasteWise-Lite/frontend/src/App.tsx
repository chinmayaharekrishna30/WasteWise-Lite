import { Navigate, Route, Routes } from "react-router-dom";
import MainLayout from "./layouts/MainLayout";
import Dashboard from "./pages/Dashboard";
import Products from "./pages/Products";
import Inventory from "./pages/Inventory";
import SalesHistory from "./pages/SalesHistory";
import DemandForecast from "./pages/DemandForecast";
import ExpiryRisk from "./pages/ExpiryRisk";
import Recommendations from "./pages/Recommendations";
import WasteReports from "./pages/WasteReports";
import ModelMetrics from "./pages/ModelMetrics";

export default function App() {
  return (
    <Routes>
      <Route element={<MainLayout />}>
        <Route index element={<Dashboard />} />
        <Route path="products" element={<Products />} />
        <Route path="inventory" element={<Inventory />} />
        <Route path="sales" element={<SalesHistory />} />
        <Route path="forecast" element={<DemandForecast />} />
        <Route path="expiry-risk" element={<ExpiryRisk />} />
        <Route path="recommendations" element={<Recommendations />} />
        <Route path="waste" element={<WasteReports />} />
        <Route path="models" element={<ModelMetrics />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
