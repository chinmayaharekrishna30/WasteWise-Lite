import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export interface Series { key: string; label: string; color: string; dashed?: boolean }

export default function LineChartCard({ data, xKey, series, height = 280 }:
  { data: Record<string, any>[]; xKey: string; series: Series[]; height?: number }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis dataKey={xKey} tick={{ fontSize: 11 }} minTickGap={24} />
        <YAxis tick={{ fontSize: 11 }} />
        <Tooltip />
        <Legend />
        {series.map(s => (
          <Line key={s.key} type="monotone" dataKey={s.key} name={s.label} stroke={s.color} dot={false}
                strokeWidth={2} strokeDasharray={s.dashed ? "6 4" : undefined} connectNulls={false} />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
