import {
  Activity,
  CheckCircle2,
  Eye,
  FileSearch,
  LoaderCircle,
  Search,
  TriangleAlert,
} from "lucide-react";
import {
  FormEvent,
  useEffect,
  useState,
} from "react";

import {
  getLatestPropagationGraph,
  ingestSocialQuery,
  type NLPSummary,
} from "../api/client";

import PropagationGraph from "../components/PropagationGraph";
import ScoreTrendChart from "../components/ScoreTrendChart";
import SourceTypeDonutChart from "../components/SourceTypeDonutChart";
import StatCard from "../components/StatCard";
import SuspiciousContentTable from "../components/SuspiciousContentTable";
import TrendingTopicsTable from "../components/TrendingTopicsTable";

import type { PropagationGraphData } from "../types";

export default function Dashboard() {
  const [propagationGraph, setPropagationGraph] =
    useState<PropagationGraphData | undefined>();

  const [nlpSummary, setNlpSummary] =
    useState<NLPSummary | null>(null);

  const [query, setQuery] = useState("");
  const [analysisRunning, setAnalysisRunning] =
    useState(false);

  const [message, setMessage] =
    useState<string | null>(null);

  const [error, setError] =
    useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    getLatestPropagationGraph()
      .then((data) => {
        if (cancelled) return;

        setPropagationGraph({
          nodes: data.nodes,
          edges: data.edges,
        });

        setNlpSummary(data.nlp_summary);
      })
      .catch(() => {
        if (!cancelled) {
          setError(
            "Yayılım ağı backend üzerinden alınamadı."
          );
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  async function handleAnalysis(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    const normalizedQuery = query.trim();

    if (!normalizedQuery) {
      setError("Analiz için bir konu veya sorgu gir.");
      return;
    }

    setAnalysisRunning(true);
    setError(null);
    setMessage(null);

    try {
      const result = await ingestSocialQuery(
        normalizedQuery,
        10
      );

      setPropagationGraph(result.graph);
      setNlpSummary(result.nlp_summary);

      setMessage(
        `"${result.query}" için ${result.post_count} paylaşım işlendi. ` +
          `${result.node_count} düğüm ve ${result.edge_count} bağlantı oluşturuldu.`
      );
    } catch {
      setError(
        "Analiz başlatılamadı. Backend bağlantısını kontrol et."
      );
    } finally {
      setAnalysisRunning(false);
    }
  }

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
            Sosyal medya ve dijital kaynaklardaki
            şüpheli içerikleri, yayılım davranışlarını
            ve doğrulama süreçlerini tek merkezden izleyin.
          </p>
        </div>

        <div className="flex min-w-[290px] items-center gap-3 rounded-lg border border-emerald-200 bg-emerald-50/70 px-4 py-3">
          <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" />

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

      <section className="rounded-lg border border-slate-200 bg-white">
        <div className="border-b border-slate-100 px-5 py-4">
          <h2 className="text-sm font-semibold text-slate-900">
            Yeni Analiz
          </h2>

          <p className="mt-1 text-xs text-slate-500">
            Bir konu veya anahtar kelime girerek sosyal
            veri toplama ve yayılım grafiği oluşturma
            sürecini başlatın.
          </p>
        </div>

        <form
          onSubmit={handleAnalysis}
          className="flex flex-col gap-3 p-5 md:flex-row"
        >
          <div className="relative flex-1">
            <Search
              size={17}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
            />

            <input
              type="text"
              value={query}
              onChange={(event) =>
                setQuery(event.target.value)
              }
              placeholder="Örn. deprem, yapay zeka, enerji krizi..."
              disabled={analysisRunning}
              className="h-11 w-full rounded-md border border-slate-200 bg-white pl-10 pr-4 text-sm text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-slate-400 disabled:bg-slate-50"
            />
          </div>

          <button
            type="submit"
            disabled={analysisRunning}
            className="flex h-11 items-center justify-center gap-2 rounded-md bg-slate-950 px-5 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {analysisRunning ? (
              <>
                <LoaderCircle
                  size={16}
                  className="animate-spin"
                />
                İşleniyor
              </>
            ) : (
              <>
                <Search size={16} />
                Analizi Başlat
              </>
            )}
          </button>
        </form>

        {(message || error) && (
          <div className="border-t border-slate-100 px-5 py-3">
            {message && (
              <p className="text-sm text-emerald-700">
                {message}
              </p>
            )}

            {error && (
              <p className="text-sm text-red-600">
                {error}
              </p>
            )}
          </div>
        )}
      </section>

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
          <PropagationGraph
            data={propagationGraph}
          />
        </div>

        <div className="xl:col-span-5">
          <div className="h-full rounded-lg border border-slate-200 bg-white">
            <div className="border-b border-slate-100 px-5 py-4">
              <div className="flex items-center gap-2">
                <Activity
                  size={17}
                  className="text-slate-500"
                />

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
                  {analysisRunning
                    ? "Çalışıyor"
                    : "Hazır"}
                </span>
              </div>

              <div className="flex items-center justify-between px-5 py-4">
                <div>
                  <p className="text-sm font-medium text-slate-800">
                    NLP sınıflandırma
                  </p>

                  <p className="mt-1 text-xs text-slate-400">
                    {nlpSummary
                      ? `${nlpSummary.labels.sahte} şüpheli · ${nlpSummary.labels.belirsiz} belirsiz · ${nlpSummary.labels.gercek} güvenilir`
                      : "Metin tabanlı risk analizi"}
                  </p>
                </div>

                <span
                  className={
                    nlpSummary
                      ? "rounded-md bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-700"
                      : "rounded-md bg-slate-100 px-2 py-1 text-xs font-medium text-slate-600"
                  }
                >
                  {nlpSummary ? "Tamamlandı" : "Hazır"}
                </span>
              </div>

              <div className="flex items-center justify-between px-5 py-4">
                <div>
                  <p className="text-sm font-medium text-slate-800">
                    Yayılım ağı oluşturma
                  </p>

                  <p className="mt-1 text-xs text-slate-400">
                    Graph oluşturma ve ilişki analizi
                  </p>
                </div>

                <span className="rounded-md bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-700">
                  Aktif
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
                  Sonraki aşama
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
              <dt className="text-xs text-slate-500">
                Aktif analiz
              </dt>

              <dd className="mt-1 text-xl font-semibold text-slate-900">
                12
              </dd>
            </div>

            <div className="bg-white px-5 py-4">
              <dt className="text-xs text-slate-500">
                Yüksek riskli vaka
              </dt>

              <dd className="mt-1 text-xl font-semibold text-slate-900">
                57
              </dd>
            </div>

            <div className="bg-white px-5 py-4">
              <dt className="text-xs text-slate-500">
                İşlenen paylaşım
              </dt>

              <dd className="mt-1 text-xl font-semibold text-slate-900">
                38.4K
              </dd>
            </div>

            <div className="bg-white px-5 py-4">
              <dt className="text-xs text-slate-500">
                Tespit edilen küme
              </dt>

              <dd className="mt-1 text-xl font-semibold text-slate-900">
                24
              </dd>
            </div>
          </dl>
        </div>
      </section>
    </div>
  );
}
