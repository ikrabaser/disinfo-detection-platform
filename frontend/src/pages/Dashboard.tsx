import {
  Activity,
  ArrowRight,
  CheckCircle2,
  Eye,
  FileSearch,
  LoaderCircle,
  Network,
  Search,
  ShieldCheck,
  Sparkles,
  TriangleAlert,
} from "lucide-react";
import {
  FormEvent,
  useEffect,
  useState,
} from "react";
import {
  useNavigate,
} from "react-router-dom";

import {
  createAnalysis,
  getLatestPropagationGraph,
  runAnalysis,
  type NLPSummary,
} from "../api/client";

import PropagationGraph from "../components/PropagationGraph";
import ScoreTrendChart from "../components/ScoreTrendChart";
import SourceTypeDonutChart from "../components/SourceTypeDonutChart";
import StatCard from "../components/StatCard";
import SuspiciousContentTable from "../components/SuspiciousContentTable";
import TrendingTopicsTable from "../components/TrendingTopicsTable";

import type {
  PropagationGraphData,
} from "../types";


export default function Dashboard() {
  const navigate =
    useNavigate();

  const [
    propagationGraph,
    setPropagationGraph,
  ] = useState<
    PropagationGraphData | undefined
  >();

  const [
    nlpSummary,
    setNlpSummary,
  ] =
    useState<NLPSummary | null>(
      null
    );

  const [query, setQuery] =
    useState("");

  const [
    analysisRunning,
    setAnalysisRunning,
  ] = useState(false);

  const [message, setMessage] =
    useState<string | null>(
      null
    );

  const [error, setError] =
    useState<string | null>(
      null
    );


  useEffect(() => {
    let cancelled = false;

    getLatestPropagationGraph()
      .then((data) => {
        if (cancelled) {
          return;
        }

        setPropagationGraph({
          nodes: data.nodes,
          edges: data.edges,
        });

        setNlpSummary(
          data.nlp_summary
        );
      })
      .catch(() => {
        if (!cancelled) {
          setError(
            "Son yayılım ağı backend üzerinden alınamadı."
          );
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);


  async function handleAnalysis(
    event:
      FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    const normalizedQuery =
      query.trim();

    if (!normalizedQuery) {
      setError(
        "Analiz için bir konu veya sorgu gir."
      );
      return;
    }

    setAnalysisRunning(true);
    setError(null);
    setMessage(null);

    try {
      const analysis =
        await createAnalysis({
          claim_text:
            normalizedQuery,
          query:
            normalizedQuery,
        });

      setMessage(
        `Analiz #${analysis.id} oluşturuldu. Kuyruğa ekleniyor...`
      );

      await runAnalysis(
        analysis.id
      );

      setMessage(
        `Analiz #${analysis.id} başlatıldı.`
      );

      navigate(
        `/analyses/${analysis.id}`
      );
    } catch {
      setError(
        "Analiz başlatılamadı. Oturum ve backend bağlantısını kontrol et."
      );
    } finally {
      setAnalysisRunning(
        false
      );
    }
  }


  return (
    <div className="mx-auto w-full max-w-[1600px] space-y-5">
      <section className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <div className="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-[#a09498] dark:text-[#75686e]">
            <ShieldCheck
              size={13}
              className="text-[#c86038] dark:text-[#ff895d]"
            />

            İzleme Merkezi
          </div>

          <h1 className="mt-2 text-[29px] font-semibold tracking-[-0.025em] text-[#241b1f] dark:text-[#fff8f5]">
            Analiz Paneli
          </h1>

          <p className="mt-2 max-w-2xl text-[13px] leading-6 text-[#817479] dark:text-[#8f8187]">
            Dijital içerikleri,
            metin sinyallerini ve
            yayılım davranışlarını
            tek merkezden analiz edin.
          </p>
        </div>

        <div className="flex items-center gap-3 rounded-xl border border-emerald-200 bg-emerald-50/70 px-4 py-3 dark:border-emerald-400/15 dark:bg-emerald-400/[0.06]">
          <span className="relative flex h-2.5 w-2.5">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-20" />

            <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-emerald-500" />
          </span>

          <div>
            <p className="text-xs font-semibold text-emerald-800 dark:text-emerald-300">
              Sistem çevrimiçi
            </p>

            <p className="mt-0.5 text-[10px] text-emerald-700/70 dark:text-emerald-300/60">
              API, worker ve realtime servisleri hazır
            </p>
          </div>
        </div>
      </section>

      <section className="overflow-hidden rounded-xl border border-[#e7dfdc] bg-white shadow-soft-panel dark:border-white/[0.08] dark:bg-[#1c1219] dark:shadow-dark-panel">
        <div className="flex items-start gap-3 border-b border-[#eee7e3] px-5 py-4 dark:border-white/[0.07]">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-[#f0cbbb] bg-[#fff2eb] text-[#c25b35] dark:border-[#ff895d]/15 dark:bg-[#ff895d]/[0.08] dark:text-[#ff956d]">
            <Sparkles
              size={17}
              strokeWidth={1.8}
            />
          </div>

          <div>
            <h2 className="text-sm font-semibold text-[#302529] dark:text-[#f8efec]">
              Yeni Analiz
            </h2>

            <p className="mt-0.5 text-[11px] text-[#988b90] dark:text-[#7e7077]">
              Konu veya anahtar kelime girerek
              asenkron analiz sürecini başlatın.
            </p>
          </div>
        </div>

        <form
          onSubmit={
            handleAnalysis
          }
          className="flex flex-col gap-3 p-5 md:flex-row"
        >
          <div className="relative flex-1">
            <Search
              size={17}
              className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#a4979b] dark:text-[#74676d]"
            />

            <input
              type="text"
              value={query}
              onChange={(
                event
              ) =>
                setQuery(
                  event.target
                    .value
                )
              }
              placeholder="Örn. yapay zeka, deprem, enerji krizi..."
              disabled={
                analysisRunning
              }
              className="h-11 w-full rounded-lg border border-[#e4dcda] bg-[#fbf9f8] pl-10 pr-4 text-sm text-[#403338] outline-none transition placeholder:text-[#aaa0a3] focus:border-[#d2b8ac] focus:bg-white disabled:opacity-60 dark:border-white/[0.08] dark:bg-white/[0.035] dark:text-[#f3eae7] dark:placeholder:text-[#6f6268] dark:focus:border-[#ff895d]/30 dark:focus:bg-white/[0.05]"
            />
          </div>

          <button
            type="submit"
            disabled={
              analysisRunning
            }
            className="flex h-11 items-center justify-center gap-2 rounded-lg bg-[#2b2024] px-5 text-sm font-semibold text-white transition hover:bg-[#3c2d32] disabled:cursor-not-allowed disabled:opacity-60 dark:bg-[#ff895d] dark:text-[#2a161b] dark:hover:bg-[#ff9a74]"
          >
            {analysisRunning ? (
              <>
                <LoaderCircle
                  size={16}
                  className="animate-spin"
                />
                Hazırlanıyor
              </>
            ) : (
              <>
                <Search
                  size={16}
                />
                Analizi Başlat
                <ArrowRight
                  size={15}
                />
              </>
            )}
          </button>
        </form>

        {(message ||
          error) && (
          <div className="border-t border-[#eee7e3] px-5 py-3 dark:border-white/[0.07]">
            {message && (
              <p className="text-xs text-emerald-700 dark:text-emerald-300">
                {message}
              </p>
            )}

            {error && (
              <p className="text-xs text-red-600 dark:text-red-300">
                {error}
              </p>
            )}
          </div>
        )}
      </section>

      <section className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          icon={FileSearch}
          label="Analiz Edilen İçerik"
          value="146.320"
          deltaPct={12}
          tone="orange"
          badge="Demo"
        />

        <StatCard
          icon={
            TriangleAlert
          }
          label="Şüpheli İçerik"
          value="2.841"
          deltaPct={18}
          tone="red"
          badge="Demo"
        />

        <StatCard
          icon={
            CheckCircle2
          }
          label="Doğrulanan İçerik"
          value="18.762"
          deltaPct={27}
          tone="green"
          badge="Demo"
        />

        <StatCard
          icon={Eye}
          label="İzlenen Kaynak"
          value="1.204"
          deltaPct={6}
          tone="neutral"
          badge="Demo"
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

      <section className="grid items-start grid-cols-1 gap-4 xl:grid-cols-12">
        <div className="xl:col-span-8">
          <PropagationGraph
            data={
              propagationGraph
            }
          />
        </div>

        <div className="xl:col-span-4">
          <div className="overflow-hidden rounded-xl border border-[#e7dfdc] bg-white shadow-soft-panel dark:border-white/[0.08] dark:bg-[#1c1219] dark:shadow-dark-panel">
            <div className="flex items-start gap-3 border-b border-[#eee7e3] px-5 py-4 dark:border-white/[0.07]">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#fff1e9] text-[#c25b35] dark:bg-[#ff895d]/[0.08] dark:text-[#ff956d]">
                <Activity
                  size={17}
                />
              </div>

              <div>
                <h2 className="text-sm font-semibold text-[#302529] dark:text-[#f8efec]">
                  Analiz Durumu
                </h2>

                <p className="mt-0.5 text-[11px] text-[#988b90] dark:text-[#7e7077]">
                  Son veri işleme görünümü
                </p>
              </div>
            </div>

            <div className="divide-y divide-[#eee7e3] dark:divide-white/[0.06]">
              <div className="flex items-center justify-between gap-4 px-5 py-4">
                <div>
                  <p className="text-xs font-semibold text-[#514348] dark:text-[#d2c4c9]">
                    Veri toplama
                  </p>

                  <p className="mt-1 text-[10px] text-[#9b8e92] dark:text-[#7d7076]">
                    X API / mock fallback
                  </p>
                </div>

                <span className="rounded-md border border-[#eadfd9] bg-[#faf5f2] px-2 py-1 text-[10px] font-semibold text-[#8c6757] dark:border-white/[0.07] dark:bg-white/[0.04] dark:text-[#aa9ba1]">
                  {analysisRunning
                    ? "Çalışıyor"
                    : "Hazır"}
                </span>
              </div>

              <div className="flex items-center justify-between gap-4 px-5 py-4">
                <div>
                  <p className="text-xs font-semibold text-[#514348] dark:text-[#d2c4c9]">
                    NLP sınıflandırma
                  </p>

                  <p className="mt-1 text-[10px] leading-4 text-[#9b8e92] dark:text-[#7d7076]">
                    {nlpSummary
                      ? `${nlpSummary.labels.sahte} şüpheli · ${nlpSummary.labels.belirsiz} belirsiz · ${nlpSummary.labels.gercek} güvenilir`
                      : "Metin tabanlı analiz"}
                  </p>
                </div>

                <span className="rounded-md bg-emerald-50 px-2 py-1 text-[10px] font-semibold text-emerald-700 dark:bg-emerald-400/[0.07] dark:text-emerald-300">
                  {nlpSummary
                    ? "Hazır"
                    : "Bekliyor"}
                </span>
              </div>

              <div className="flex items-center justify-between gap-4 px-5 py-4">
                <div>
                  <p className="text-xs font-semibold text-[#514348] dark:text-[#d2c4c9]">
                    Yayılım ağı
                  </p>

                  <p className="mt-1 text-[10px] text-[#9b8e92] dark:text-[#7d7076]">
                    Son graph verisi
                  </p>
                </div>

                <span className="rounded-md bg-[#fff1e9] px-2 py-1 text-[10px] font-semibold text-[#b95531] dark:bg-[#ff895d]/[0.08] dark:text-[#ff9872]">
                  {propagationGraph
                    ? `${propagationGraph.nodes.length} düğüm`
                    : "Bekliyor"}
                </span>
              </div>

              <div className="flex items-center justify-between gap-4 px-5 py-4">
                <div>
                  <p className="text-xs font-semibold text-[#514348] dark:text-[#d2c4c9]">
                    Async worker
                  </p>

                  <p className="mt-1 text-[10px] text-[#9b8e92] dark:text-[#7d7076]">
                    Procrastinate + Centrifugo
                  </p>
                </div>

                <span className="inline-flex items-center gap-1.5 rounded-md bg-emerald-50 px-2 py-1 text-[10px] font-semibold text-emerald-700 dark:bg-emerald-400/[0.07] dark:text-emerald-300">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                  Aktif
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <SuspiciousContentTable />

      <section className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <TrendingTopicsTable />

        <div className="overflow-hidden rounded-xl border border-[#e7dfdc] bg-white shadow-soft-panel dark:border-white/[0.08] dark:bg-[#1c1219] dark:shadow-dark-panel">
          <div className="flex items-start justify-between border-b border-[#eee7e3] px-5 py-4 dark:border-white/[0.07]">
            <div>
              <h2 className="text-sm font-semibold text-[#302529] dark:text-[#f8efec]">
                Sistem Özeti
              </h2>

              <p className="mt-0.5 text-[11px] text-[#988b90] dark:text-[#7e7077]">
                Operasyonel demo görünümü
              </p>
            </div>

            <span className="rounded-md border border-[#e9e1dd] bg-[#faf7f5] px-2 py-1 text-[9px] font-semibold uppercase tracking-[0.08em] text-[#9b8e92] dark:border-white/[0.07] dark:bg-white/[0.035] dark:text-[#786b71]">
              Demo veri
            </span>
          </div>

          <dl className="grid grid-cols-2 gap-px bg-[#eee7e3] dark:bg-white/[0.06]">
            {[
              [
                "Aktif analiz",
                "12",
              ],
              [
                "Yüksek riskli vaka",
                "57",
              ],
              [
                "İşlenen paylaşım",
                "38.4K",
              ],
              [
                "Tespit edilen küme",
                "24",
              ],
            ].map(
              ([label, value]) => (
                <div
                  key={label}
                  className="bg-white px-5 py-5 dark:bg-[#1c1219]"
                >
                  <dt className="text-[10px] text-[#998c91] dark:text-[#81747a]">
                    {label}
                  </dt>

                  <dd className="mt-1 text-xl font-semibold text-[#302529] dark:text-[#fff7f4]">
                    {value}
                  </dd>
                </div>
              )
            )}
          </dl>
        </div>
      </section>
    </div>
  );
}
