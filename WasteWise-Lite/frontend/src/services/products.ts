import { api } from "./api";
import type { Product, SaleRow } from "../types";

export const listProducts = (q = "", category = "") => {
  const p = new URLSearchParams();
  if (q) p.set("q", q);
  if (category) p.set("category", category);
  return api.get<Product[]>(`/products?${p}`);
};

export const listSales = (productId?: number, limit = 200) =>
  api.get<SaleRow[]>(`/sales?limit=${limit}${productId ? `&product_id=${productId}` : ""}`);
