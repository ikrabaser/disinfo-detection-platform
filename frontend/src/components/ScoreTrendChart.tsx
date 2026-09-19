import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

// Mock trend verisi - gercek implementasyonda /api/analyses/ uzerinden
// zaman serisi halinde supheli/dogrulanan icerik sayilari cekilmelidir.
const MOCK_TREND_DATA = [
  { date: "1 Kas", supheli: 620, dogrulanan: 410, diger: 180 },
  { date: "5 Kas", supheli: 710, dogrulanan: 460, diger: 210 },
  { date: "9 Kas", supheli: 940, dogrulanan: 520, diger: 240 },
  { date: "13 Kas", supheli: 860, dogrulanan: 610, diger: 220 },
  { date: "17 Kas", supheli: 1120, dogrulanan: 640, diger: 260 },
  { date: "21 Kas", supheli: 980, dogrulanan: 700, diger: 250 },
  { date: "25 Kas", supheli: 1480, dogrulanan: 780, diger: 300 },
  { date: "30 Kas", supheli: 1260, dogrulanan: 820, diger: 280 },
];

export default function ScoreTrendChart() {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-700">Dezenformasyon Egilimi</h3>
      </div>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={MOCK_TREND_DATA}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
          <XAxis dataKey="date" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
          <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
          <Tooltip
            contentStyle={{ borderRadius: 8, borderColor: "#e2e8f0", fontSize: 12 }}
          />
          <Legend
            iconType="circle"
            wrapperStyle={{ fontSize: 12, color: "#64748b" }}
            formatter={(value) =>
              value === "supheli" ? "Supheli Icerik" : value === "dogrulanan" ? "Dogrulanan Icerik" : "Diger Icerik"
            }
          />
          <Line type="monotone" dataKey="supheli" stroke="#ef4444" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="dogrulanan" stroke="#4f46e5" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="diger" stroke="#94a3b8" strokeWidth={2} dot={false} strokeDasharray="4 3" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
