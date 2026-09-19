import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

// Mock trend verisi - gercek implementasyonda /api/analyses/ uzerinden
// zaman serisi halinde truth_score degerleri cekilmelidir.
const MOCK_TREND_DATA = [
  { date: "Pzt", truthScore: 0.62 },
  { date: "Sal", truthScore: 0.58 },
  { date: "Çar", truthScore: 0.71 },
  { date: "Per", truthScore: 0.45 },
  { date: "Cum", truthScore: 0.53 },
  { date: "Cmt", truthScore: 0.67 },
  { date: "Paz", truthScore: 0.6 },
];

export default function ScoreTrendChart() {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h3 className="mb-3 text-sm font-medium text-slate-600">
        Haftalik Ortalama Dogruluk Skoru (mock veri)
      </h3>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={MOCK_TREND_DATA}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="date" stroke="#64748b" fontSize={12} />
          <YAxis domain={[0, 1]} stroke="#64748b" fontSize={12} />
          <Tooltip
            formatter={(value: number) => [`${(value * 100).toFixed(0)}%`, "Dogruluk Skoru"]}
          />
          <Line
            type="monotone"
            dataKey="truthScore"
            stroke="#4f46e5"
            strokeWidth={2}
            dot={{ r: 3 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
