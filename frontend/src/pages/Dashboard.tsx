import { CheckCircle2, Eye, FileSearch, Target, TriangleAlert } from "lucide-react";
import { useEffect, useState } from "react";

import { listAnalyses } from "../api/client";
import ScoreTrendChart from "../components/ScoreTrendChart";
import SourceTypeDonutChart from "../components/SourceTypeDonutChart";
import StatCard from "../components/StatCard";
import SuspiciousContentTable from "../components/SuspiciousContentTable";
import TrendingTopicsTable from "../components/TrendingTopicsTable";

export default function Dashboard() {
  const [backendError, setBackendError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    listAnalyses().catch(() => {
      // Backend henuz calismiyor/auth gerektiriyor olabilir - dashboard
      // asagidaki mock istatistiklerle calismaya devam eder.
      if (!cancelled) {
        setBackendError("Backend'e ulasilamadi, mock veriler gosteriliyor.");
      }
    });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-end">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-brand-600">
            Genel Bakis
          </p>
          <h1 className="mt-1 text-2xl font-bold text-slate-800 lg:text-3xl">
            Daha guvenilir bir bilgi ekosistemi icin.
          </h1>
          <p className="mt-2 max-w-2xl text-sm text-slate-500">
            VERITAS, dijital mecralardaki yanlis bilgi, manipulasyon ve dezenformasyonu tespit
            eder, analiz eder ve kurumlarin daha saglikli kararlar almasina yardimci olur.
          </p>
          {backendError && <p className="mt-2 text-xs text-amber-600">{backendError}</p>}
        </div>
        <p className="max-w-xs text-right text-sm italic text-slate-400">
          "Bilgi, daha guvenli yarinlarin temelidir."
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <StatCard
          icon={FileSearch}
          iconClassName="bg-brand-50 text-brand-600"
          label="Analiz Edilen Icerik"
          value="146.320"
          deltaPct={12}
        />
        <StatCard
          icon={TriangleAlert}
          iconClassName="bg-red-50 text-red-600"
          label="Supheli Iddia"
          value="2.841"
          deltaPct={18}
        />
        <StatCard
          icon={CheckCircle2}
          iconClassName="bg-emerald-50 text-emerald-600"
          label="Dogrulanan Icerik"
          value="18.762"
          deltaPct={27}
        />
        <StatCard
          icon={Eye}
          iconClassName="bg-sky-50 text-sky-600"
          label="Izlenen Kaynak"
          value="1.204"
          deltaPct={6}
        />
        <StatCard
          icon={Target}
          iconClassName="bg-violet-50 text-violet-600"
          label="Vaka Cozum Orani"
          value="%89"
          deltaPct={5}
        />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <ScoreTrendChart />
        </div>
        <SourceTypeDonutChart />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <SuspiciousContentTable />
        <TrendingTopicsTable />
      </div>
    </div>
  );
}
