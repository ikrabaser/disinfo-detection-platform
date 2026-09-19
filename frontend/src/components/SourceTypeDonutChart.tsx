import { Cell, Pie, PieChart, ResponsiveContainer } from "recharts";

interface SourceSlice {
  label: string;
  pct: number;
  color: string;
}

const MOCK_SOURCE_DATA: SourceSlice[] = [
  { label: "Sosyal Medya", pct: 46, color: "#4f46e5" },
  { label: "Haber Siteleri", pct: 24, color: "#38bdf8" },
  { label: "Bloglar / Forumlar", pct: 12, color: "#a3e635" },
  { label: "Geleneksel Medya", pct: 9, color: "#14b8a6" },
  { label: "Video Platformlari", pct: 6, color: "#f59e0b" },
  { label: "Diger", pct: 3, color: "#cbd5e1" },
];

const TOTAL_CONTENT = "146.320";

export default function SourceTypeDonutChart() {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-1 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-700">Kaynak Turu Dagilimi</h3>
        <a href="#" className="text-xs font-medium text-brand-600 hover:underline">
          Tumunu Gor
        </a>
      </div>

      <div className="flex items-center gap-4">
        <div className="relative h-40 w-40 shrink-0">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={MOCK_SOURCE_DATA}
                dataKey="pct"
                nameKey="label"
                innerRadius={45}
                outerRadius={70}
                paddingAngle={2}
                stroke="none"
              >
                {MOCK_SOURCE_DATA.map((slice) => (
                  <Cell key={slice.label} fill={slice.color} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
          <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
            <p className="text-base font-semibold text-slate-800">{TOTAL_CONTENT}</p>
            <p className="text-[11px] text-slate-400">Toplam Icerik</p>
          </div>
        </div>

        <ul className="flex-1 space-y-2">
          {MOCK_SOURCE_DATA.map((slice) => (
            <li key={slice.label} className="flex items-center justify-between text-xs">
              <span className="flex items-center gap-2 text-slate-600">
                <span
                  className="h-2.5 w-2.5 rounded-full"
                  style={{ backgroundColor: slice.color }}
                />
                {slice.label}
              </span>
              <span className="font-medium text-slate-700">%{slice.pct}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
