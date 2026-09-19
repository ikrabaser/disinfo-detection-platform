import { TrendingDown, TrendingUp } from "lucide-react";

interface TrendingTopicRow {
  rank: number;
  topic: string;
  volume: string;
  changePct: number;
}

const MOCK_TOPICS: TrendingTopicRow[] = [
  { rank: 1, topic: "Ekonomi ve Vergi Politikalari", volume: "12.428", changePct: 42 },
  { rank: 2, topic: "Deprem ve Dogal Afetler", volume: "8.316", changePct: 28 },
  { rank: 3, topic: "Goc ve Siginmacilar", volume: "6.502", changePct: 17 },
  { rank: 4, topic: "Saglik ve Salgin Hastaliklar", volume: "5.981", changePct: -9 },
  { rank: 5, topic: "Dis Politika", volume: "5.406", changePct: 14 },
];

export default function TrendingTopicsTable() {
  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3">
        <h3 className="text-sm font-semibold text-slate-700">Gundemdeki Riskli Konular</h3>
        <a href="#" className="text-xs font-medium text-brand-600 hover:underline">
          Tumunu Gor
        </a>
      </div>
      <table className="w-full text-left text-xs">
        <thead>
          <tr className="text-slate-400">
            <th className="px-4 py-2 font-medium">#</th>
            <th className="px-4 py-2 font-medium">Konu</th>
            <th className="px-4 py-2 font-medium">Hacim</th>
            <th className="px-4 py-2 font-medium">Degisim</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {MOCK_TOPICS.map((row) => {
            const positive = row.changePct >= 0;
            const DeltaIcon = positive ? TrendingUp : TrendingDown;
            return (
              <tr key={row.rank} className="hover:bg-slate-50">
                <td className="px-4 py-3 text-slate-400">{row.rank}</td>
                <td className="px-4 py-3 font-medium text-slate-700">{row.topic}</td>
                <td className="px-4 py-3 text-slate-500">{row.volume}</td>
                <td className="px-4 py-3">
                  <span
                    className={`flex items-center gap-1 font-medium ${
                      positive ? "text-emerald-600" : "text-red-600"
                    }`}
                  >
                    <DeltaIcon size={12} />
                    %{Math.abs(row.changePct)}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
