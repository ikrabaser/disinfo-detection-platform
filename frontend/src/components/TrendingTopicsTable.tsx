import {
  TrendingDown,
  TrendingUp,
} from "lucide-react";


interface TrendingTopicRow {
  rank: number;
  topic: string;
  volume: string;
  changePct: number;
}


const MOCK_TOPICS:
  TrendingTopicRow[] = [
    {
      rank: 1,
      topic:
        "Ekonomi ve Vergi Politikaları",
      volume: "12.428",
      changePct: 42,
    },
    {
      rank: 2,
      topic:
        "Deprem ve Doğal Afetler",
      volume: "8.316",
      changePct: 28,
    },
    {
      rank: 3,
      topic:
        "Göç ve Sığınmacılar",
      volume: "6.502",
      changePct: 17,
    },
    {
      rank: 4,
      topic:
        "Sağlık ve Salgın Hastalıklar",
      volume: "5.981",
      changePct: -9,
    },
    {
      rank: 5,
      topic:
        "Dış Politika",
      volume: "5.406",
      changePct: 14,
    },
  ];


export default function TrendingTopicsTable() {
  return (
    <section className="h-full overflow-hidden rounded-xl border border-[#e7dfdc] bg-white shadow-soft-panel dark:border-white/[0.08] dark:bg-[#1c1219] dark:shadow-dark-panel">
      <div className="flex items-start justify-between border-b border-[#eee7e3] px-5 py-4 dark:border-white/[0.07]">
        <div>
          <h3 className="text-sm font-semibold text-[#302529] dark:text-[#f8efec]">
            Gündemdeki Riskli Konular
          </h3>

          <p className="mt-0.5 text-[11px] text-[#988b90] dark:text-[#7e7077]">
            İçerik hacmine göre öne çıkan başlıklar
          </p>
        </div>

        <div className="flex items-center gap-3">
          <span className="rounded-md border border-[#e9e1dd] bg-[#faf7f5] px-2 py-1 text-[9px] font-semibold uppercase tracking-[0.08em] text-[#9b8e92] dark:border-white/[0.07] dark:bg-white/[0.035] dark:text-[#786b71]">
            Demo
          </span>

          <button
            type="button"
            className="text-[10px] font-semibold text-[#bd5a34] transition hover:text-[#8f4025] dark:text-[#ff9269]"
          >
            Tümünü Gör
          </button>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-[11px]">
          <thead>
            <tr className="border-b border-[#eee7e3] bg-[#fbf9f8] text-[#9a8d92] dark:border-white/[0.06] dark:bg-white/[0.018] dark:text-[#786b71]">
              <th className="w-12 px-5 py-3 font-medium">
                #
              </th>

              <th className="px-3 py-3 font-medium">
                Konu
              </th>

              <th className="px-3 py-3 font-medium">
                Hacim
              </th>

              <th className="px-5 py-3 font-medium">
                Değişim
              </th>
            </tr>
          </thead>

          <tbody className="divide-y divide-[#eee7e3] dark:divide-white/[0.055]">
            {MOCK_TOPICS.map(
              (row) => {
                const positive =
                  row.changePct >=
                  0;

                const DeltaIcon =
                  positive
                    ? TrendingUp
                    : TrendingDown;

                return (
                  <tr
                    key={
                      row.rank
                    }
                    className="transition hover:bg-[#faf7f5] dark:hover:bg-white/[0.025]"
                  >
                    <td className="px-5 py-3.5">
                      <span className="flex h-6 w-6 items-center justify-center rounded-md bg-[#f5efec] text-[9px] font-semibold text-[#887a7f] dark:bg-white/[0.045] dark:text-[#93858b]">
                        {
                          row.rank
                        }
                      </span>
                    </td>

                    <td className="px-3 py-3.5 font-medium text-[#514348] dark:text-[#d3c5ca]">
                      {
                        row.topic
                      }
                    </td>

                    <td className="px-3 py-3.5 font-medium text-[#817479] dark:text-[#97898f]">
                      {
                        row.volume
                      }
                    </td>

                    <td className="px-5 py-3.5">
                      <span
                        className={[
                          "inline-flex items-center gap-1 font-semibold",
                          positive
                            ? "text-emerald-600 dark:text-emerald-300"
                            : "text-red-600 dark:text-red-300",
                        ].join(
                          " "
                        )}
                      >
                        <DeltaIcon
                          size={12}
                        />

                        %
                        {Math.abs(
                          row.changePct
                        )}
                      </span>
                    </td>
                  </tr>
                );
              }
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
