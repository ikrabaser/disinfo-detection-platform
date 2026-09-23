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
    <div className="rounded-xl border border-[#e7dfdc] bg-white p-4 shadow-soft-panel dark:border-white/[0.08] dark:bg-[#1c1219] dark:shadow-dark-panel">
      <div className="mb-4 flex items-start justify-between">
        <div>
          <h3 className="text-sm font-semibold text-[#302529] dark:text-[#f8efec]">
            Dezenformasyon Eğilimi
          </h3>

          <p className="mt-0.5 text-[11px] text-[#988b90] dark:text-[#7e7077]">
            Dönemsel içerik dağılımı
          </p>
        </div>

        <span className="rounded-md border border-[#e9e1dd] bg-[#faf7f5] px-2 py-1 text-[9px] font-semibold uppercase tracking-[0.08em] text-[#9b8e92] dark:border-white/[0.07] dark:bg-white/[0.035] dark:text-[#786b71]">
          Demo veri
        </span>
      </div>

      <ResponsiveContainer
        width="100%"
        height={270}
      >
        <LineChart
          data={MOCK_TREND_DATA}
        >
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="var(--border)"
            vertical={false}
          />

          <XAxis
            dataKey="date"
            stroke="var(--text-soft)"
            fontSize={10}
            tickLine={false}
            axisLine={false}
          />

          <YAxis
            stroke="var(--text-soft)"
            fontSize={10}
            tickLine={false}
            axisLine={false}
          />

          <Tooltip
            contentStyle={{
              borderRadius: 10,
              border:
                "1px solid var(--border)",
              background:
                "var(--surface-elevated)",
              color:
                "var(--text)",
              fontSize: 11,
            }}
          />

          <Legend
            iconType="circle"
            wrapperStyle={{
              fontSize: 10,
              color:
                "var(--text-muted)",
            }}
            formatter={(
              value
            ) =>
              value ===
              "supheli"
                ? "Şüpheli"
                : value ===
                    "dogrulanan"
                  ? "Doğrulanan"
                  : "Diğer"
            }
          />

          <Line
            type="monotone"
            dataKey="supheli"
            stroke="#d84c5d"
            strokeWidth={2}
            dot={false}
          />

          <Line
            type="monotone"
            dataKey="dogrulanan"
            stroke="#d96b3f"
            strokeWidth={2}
            dot={false}
          />

          <Line
            type="monotone"
            dataKey="diger"
            stroke="#9a8d92"
            strokeWidth={1.5}
            dot={false}
            strokeDasharray="4 3"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
