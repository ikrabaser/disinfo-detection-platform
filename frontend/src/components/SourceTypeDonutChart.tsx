import {
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
} from "recharts";


interface SourceSlice {
  label: string;
  pct: number;
  color: string;
}


const MOCK_SOURCE_DATA:
  SourceSlice[] = [
    {
      label: "Sosyal Medya",
      pct: 46,
      color: "#d96b3f",
    },
    {
      label: "Haber Siteleri",
      pct: 24,
      color: "#8b5c7e",
    },
    {
      label: "Blog / Forum",
      pct: 12,
      color: "#b9855b",
    },
    {
      label: "Geleneksel Medya",
      pct: 9,
      color: "#4f8f72",
    },
    {
      label: "Video",
      pct: 6,
      color: "#d84c5d",
    },
    {
      label: "Diğer",
      pct: 3,
      color: "#aaa0a3",
    },
  ];


export default function SourceTypeDonutChart() {
  return (
    <div className="h-full rounded-xl border border-[#e7dfdc] bg-white p-4 shadow-soft-panel dark:border-white/[0.08] dark:bg-[#1c1219] dark:shadow-dark-panel">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-sm font-semibold text-[#302529] dark:text-[#f8efec]">
            Kaynak Türü Dağılımı
          </h3>

          <p className="mt-0.5 text-[11px] text-[#988b90] dark:text-[#7e7077]">
            İzlenen içerik kaynakları
          </p>
        </div>

        <span className="rounded-md border border-[#e9e1dd] bg-[#faf7f5] px-2 py-1 text-[9px] font-semibold uppercase tracking-[0.08em] text-[#9b8e92] dark:border-white/[0.07] dark:bg-white/[0.035] dark:text-[#786b71]">
          Demo
        </span>
      </div>

      <div className="mt-4 flex items-center gap-4">
        <div className="relative h-40 w-40 shrink-0">
          <ResponsiveContainer
            width="100%"
            height="100%"
          >
            <PieChart>
              <Pie
                data={
                  MOCK_SOURCE_DATA
                }
                dataKey="pct"
                nameKey="label"
                innerRadius={47}
                outerRadius={68}
                paddingAngle={2}
                stroke="none"
              >
                {MOCK_SOURCE_DATA.map(
                  (slice) => (
                    <Cell
                      key={
                        slice.label
                      }
                      fill={
                        slice.color
                      }
                    />
                  )
                )}
              </Pie>
            </PieChart>
          </ResponsiveContainer>

          <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
            <p className="text-lg font-semibold text-[#302529] dark:text-[#fff7f4]">
              146K
            </p>

            <p className="text-[9px] text-[#9a8d92] dark:text-[#786b71]">
              içerik
            </p>
          </div>
        </div>

        <ul className="min-w-0 flex-1 space-y-2.5">
          {MOCK_SOURCE_DATA.map(
            (slice) => (
              <li
                key={
                  slice.label
                }
                className="flex items-center justify-between gap-3 text-[10px]"
              >
                <span className="flex min-w-0 items-center gap-2 text-[#76696e] dark:text-[#9b8d93]">
                  <span
                    className="h-2 w-2 shrink-0 rounded-full"
                    style={{
                      backgroundColor:
                        slice.color,
                    }}
                  />

                  <span className="truncate">
                    {
                      slice.label
                    }
                  </span>
                </span>

                <span className="font-semibold text-[#514348] dark:text-[#c8bac0]">
                  %{slice.pct}
                </span>
              </li>
            )
          )}
        </ul>
      </div>
    </div>
  );
}
