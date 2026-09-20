import {
  Activity,
  CheckCircle2,
  Eye,
  FileSearch,
  TriangleAlert,
} from "lucide-react";
import { useEffect, useState } from "react";

import { listAnalyses } from "../api/client";
import PropagationGraph from "../components/PropagationGraph";
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
      if (!cancelled) {
        setBackendError(
          "Backend bağlantısı kurulamadı. Gösterim verileri kullanılıyor."
        );
      }
    });

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="mx-auto w-full max-w-[1600px] space-y-6">
      <section className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">
            İzleme Merkezi
          </p>

          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">
            Analiz Paneli
          </h1>

          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">
            Sosyal medya ve dijital kaynaklardaki şüpheli içerikleri,
            yayılım davranışlarını ve doğrulama süreçlerini tek merkezden izleyin.
          </p>
        </div>

        <div className="flex min-w-[290px] items-center gap-3 rounded-lg border border-emerald-200 bg-emerald-50/70 px-4 py-3">
          <span className="relative flex h-2.5 w-2.5">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-40" />
            <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-emerald-500" />
          </span>

          <div>
            <p className="text-sm font-medium text-emerald-900">
              Sistem çevrimiçi
            </p>
            <p className="mt-0.5 text-xs text-emerald-700">
              Veri işleme servisleri hazır
            </p>
          </div>
        </div>
      </section>

      {backendError && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          {backendError}
        </div>
      )}

      <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          icon={FileSearch}
          iconClassName="bg-blue-50 text-blue-700"
          label="Analiz Edilen İçerik"
          value="146.320"
          deltaPct={12}
          deltaLabel="önceki döneme göre"
        />

        <StatCard
          icon={TriangleAlert}
          iconClassName="bg-red-50 text-red-600"
          label="Şüpheli İçerik"
          value="2.841"
          deltaPct={18}
          deltaLabel="önceki döneme göre"
        />

        <StatCard
          icon={CheckCircle2}
          iconClassName="bg-emerald-50 text-emerald-700"
          label="Doğrulanan İçerik"
          value="18.762"
          deltaPct={27}
          deltaLabel="önceki döneme göre"
        />

        <StatCard
          icon={Eye}
          iconClassName="bg-slate-100 text-slate-700"
          label="İzlenen Kaynak"
          value="1.204"
          deltaPct={6}
          deltaLabel="önceki döneme göre"
        />
      </section>

      <section className="grid grid-cols-1 gap-4 xl:grid-cols-12">
        <div className="xl:col-span-8">
          <ScoreTrendChart />
        </div>

        <div className="xl:col-span-4">
          <SourceTypeDonutChart />
        </div>
      </section>

      <section className="grid grid-cols-1 gap-4 xl:grid-cols-12">
        <div className="xl:col-span-7">
          <PropagationGraph />
        </div>

        <div className="xl:col-span-5">
          <div className="h-full rounded-lg border border-slate-200 bg-white">
            <div className="border-b border-slate-100 px-5 py-4">
              <div className="flex items-center gap-2">
                <Activity size={17} className="text-slate-500" />
                <h2 className="text-sm font-semibold text-slate-900">
                  Analiz Durumu
                </h2>
              </div>

              <p className="mt-1 text-xs text-slate-500">
                Aktif veri işleme ve doğrulama süreçleri
              </p>
            </div>

            <div className="divide-y divide-slate-100">
              <div className="flex items-center justify-between px-5 py-4">
                <div>
                  <p className="text-sm font-medium text-slate-800">
                    Sosyal medya veri toplama
                  </p>
                  <p className="mt-1 text-xs text-slate-400">
                    X ve diğer dijital kaynaklar
                  </p>
                </div>

                <span className="rounded-md bg-blue-50 px-2 py-1 text-xs font-medium text-blue-700">
                  Devam ediyor
                </span>
              </div>

              <div className="flex items-center justify-between px-5 py-4">
                <div>
                  <p className="text-sm font-medium text-slate-800">
                    NLP sınıflandırma
                  </p>
                  <p className="mt-1 text-xs text-slate-400">
                    Metin tabanlı risk analizi
                  </p>
                </div>

                <span className="rounded-md bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-700">
                  Hazır
                </span>
              </div>

              <div className="flex items-center justify-between px-5 py-4">
                <div>
                  <p className="text-sm font-medium text-slate-800">
                    Yayılım ağı analizi
                  </p>
                  <p className="mt-1 text-xs text-slate-400">
                    Graph oluşturma ve ilişki analizi
                  </p>
                </div>

                <span className="rounded-md bg-amber-50 px-2 py-1 text-xs font-medium text-amber-700">
                  Bekliyor
                </span>
              </div>

              <div className="flex items-center justify-between px-5 py-4">
                <div>
                  <p className="text-sm font-medium text-slate-800">
                    Agent değerlendirmesi
                  </p>
                  <p className="mt-1 text-xs text-slate-400">
                    Analiz çıktılarının birleştirilmesi
                  </p>
                </div>

                <span className="rounded-md bg-slate-100 px-2 py-1 text-xs font-medium text-slate-600">
                  Pasif
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <SuspiciousContentTable />

      <section className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <TrendingTopicsTable />

        <div className="rounded-lg border border-slate-200 bg-white">
          <div className="border-b border-slate-100 px-5 py-4">
            <h2 className="text-sm font-semibold text-slate-900">
              Sistem Özeti
            </h2>
            <p className="mt-1 text-xs text-slate-500">
              Son 24 saatteki operasyonel görünüm
            </p>
          </div>

          <dl className="grid grid-cols-2 gap-px bg-slate-100">
            <div className="bg-white px-5 py-4">
              <dt className="text-xs text-slate-500">Aktif analiz</dt>
              <dd className="mt-1 text-xl font-semibold text-slate-900">12</dd>
            </div>

            <div className="bg-white px-5 py-4">
              <dt className="text-xs text-slate-500">Yüksek riskli vaka</dt>
              <dd className="mt-1 text-xl font-semibold text-slate-900">57</dd>
            </div>

            <div className="bg-white px-5 py-4">
              <dt className="text-xs text-slate-500">İşlenen paylaşım</dt>
              <dd className="mt-1 text-xl font-semibold text-slate-900">38.4K</dd>
            </div>

            <div className="bg-white px-5 py-4">
              <dt className="text-xs text-slate-500">
                Tespit edilen küme
              </dt>
              <dd className="mt-1 text-xl font-semibold text-slate-900">24</dd>
            </div>
          </dl>
        </div>
      </section>
    </div>
  );
}
