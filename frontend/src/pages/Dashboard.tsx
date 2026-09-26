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
  getAnalysisDashboardSummary,
  getLatestPropagationGraph,
  getSystemHealth,
  runAnalysis,
  type AnalysisDashboardSummary,
  type SystemHealth,
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
    dashboardSummary,
    setDashboardSummary,
  ] =
    useState<
      AnalysisDashboardSummary | null
    >(null);

  const [
    systemHealth,
    setSystemHealth,
  ] =
    useState<SystemHealth | null>(
      null
    );

  const [query, setQuery] =
    useState("");

  const [
    analysisMode,
    setAnalysisMode,
  ] = useState<
    "fast" | "deep"
  >("fast");

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

    async function refreshDashboardSummary() {
      try {
        const data =
          await getAnalysisDashboardSummary();

        if (!cancelled) {
          setDashboardSummary(
            data
          );
        }
      } catch {
        if (!cancelled) {
          setError(
            "Dashboard analiz özeti alınamadı."
          );
        }
      }
    }

    void refreshDashboardSummary();

    async function refreshHealth() {
      try {
        const health =
          await getSystemHealth();

        if (!cancelled) {
          setSystemHealth(
            health
          );
        }
      } catch {
        if (!cancelled) {
          setSystemHealth(
            null
          );
        }
      }
    }

    void refreshHealth();

    const healthInterval =
      window.setInterval(
        () => {
          if (
            document.visibilityState
            === "visible"
          ) {
            void refreshHealth();
          }
        },
        10000
      );

    const summaryInterval =
      window.setInterval(
        () => {
          if (
            document.visibilityState
            === "visible"
          ) {
            void refreshDashboardSummary();
          }
        },
        5000
      );

    getLatestPropagationGraph()
      .then((data) => {
        if (cancelled) {
          return;
        }

        setPropagationGraph({
          nodes: data.nodes,
          edges: data.edges,
        });
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

      window.clearInterval(
        summaryInterval
      );

      window.clearInterval(
        healthInterval
      );
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
          analysis_mode:
            analysisMode,
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


  const latestAnalysis =
    dashboardSummary
      ?.latest_analysis ?? null;

  const analysisStages = [
    {
      label: "NLP sınıflandırma",
      detail: "Metin tabanlı analiz",
      done:
        latestAnalysis
          ?.nlp_result != null,
    },
    {
      label: "Yayılım ağı",
      detail:
        "Sosyal veri ve graph",
      done:
        latestAnalysis
          ?.propagation_graph != null,
    },
    {
      label: "GNN analizi",
      detail:
        "Yayılım modeli",
      done:
        latestAnalysis
          ?.gnn_result != null,
    },
    {
      label: "Bot analizi",
      detail:
        "Davranış sinyalleri",
      done:
        latestAnalysis
          ?.bot_analysis_result != null,
    },
    {
      label: "AI Evidence",
      detail:
        "Kanıt ve RAG analizi",
      done:
        latestAnalysis
          ?.ai_analysis_result != null,
    },
  ];

  const currentStageIndex =
    analysisStages.findIndex(
      (item) => !item.done
    );


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

        <div
          className={[
            "flex items-center gap-3 rounded-xl border px-4 py-3",
            systemHealth?.status
              === "ok"
              ? "border-emerald-200 bg-emerald-50/70 dark:border-emerald-400/15 dark:bg-emerald-400/[0.06]"
              : systemHealth
                ? "border-amber-200 bg-amber-50/70 dark:border-amber-400/15 dark:bg-amber-400/[0.06]"
                : "border-[#e4dcda] bg-white dark:border-white/[0.08] dark:bg-white/[0.03]",
          ].join(" ")}
        >
          <span className="relative flex h-2.5 w-2.5">
            <span
              className={[
                "relative inline-flex h-2.5 w-2.5 rounded-full",
                systemHealth?.status
                  === "ok"
                  ? "bg-emerald-500"
                  : systemHealth
                    ? "bg-amber-500"
                    : "bg-[#b7aaae]",
              ].join(" ")}
            />
          </span>

          <div>
            <p
              className={[
                "text-xs font-semibold",
                systemHealth?.status
                  === "ok"
                  ? "text-emerald-800 dark:text-emerald-300"
                  : systemHealth
                    ? "text-amber-800 dark:text-amber-300"
                    : "text-[#75686d] dark:text-[#9b8d93]",
              ].join(" ")}
            >
              {systemHealth?.status
                === "ok"
                ? "Sistem çevrimiçi"
                : systemHealth
                  ? "Servis kontrolü gerekli"
                  : "Servisler kontrol ediliyor"}
            </p>

            <p className="mt-0.5 text-[10px] text-[#8f8187] dark:text-[#7d7076]">
              {systemHealth
                ? [
                    ["API", systemHealth.services.api],
                    ["DB", systemHealth.services.database],
                    ["Redis", systemHealth.services.redis],
                    ["Queue", systemHealth.services.queue],
                    ["Realtime", systemHealth.services.realtime],
                  ]
                    .map(
                      ([label, value]) =>
                        `${label} ${
                          value === "ok"
                            ? "✓"
                            : "×"
                        }`
                    )
                    .join(" · ")
                : "API ve altyapı servisleri kontrol ediliyor"}
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

          <div className="grid grid-cols-2 gap-1 rounded-lg border border-[#e4dcda] bg-[#f7f3f1] p-1 dark:border-white/[0.08] dark:bg-white/[0.035]">
            <button
              type="button"
              disabled={
                analysisRunning
              }
              onClick={() =>
                setAnalysisMode(
                  "fast"
                )
              }
              className={[
                "rounded-md px-3 py-2 text-[11px] font-semibold transition",
                analysisMode
                  === "fast"
                  ? "bg-white text-[#3f3237] shadow-sm dark:bg-white/[0.09] dark:text-white"
                  : "text-[#96888d] hover:text-[#594b50] dark:text-[#776a70]",
              ].join(" ")}
            >
              Hızlı
              <span className="ml-1 block text-[9px] font-normal opacity-70">
                OpenAI · hızlı tarama
              </span>
            </button>

            <button
              type="button"
              disabled={
                analysisRunning
              }
              onClick={() =>
                setAnalysisMode(
                  "deep"
                )
              }
              className={[
                "rounded-md px-3 py-2 text-[11px] font-semibold transition",
                analysisMode
                  === "deep"
                  ? "bg-white text-[#3f3237] shadow-sm dark:bg-white/[0.09] dark:text-white"
                  : "text-[#96888d] hover:text-[#594b50] dark:text-[#776a70]",
              ].join(" ")}
            >
              Derin
              <span className="ml-1 block text-[9px] font-normal opacity-70">
                Claude · geniş kanıt taraması
              </span>
            </button>
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
          label="Toplam Analiz"
          value={
            String(
              dashboardSummary
                ?.counts.total ?? 0
            )
          }
          tone="orange"
          badge="Canlı"
        />

        <StatCard
          icon={Activity}
          label="Devam Eden"
          value={
            String(
              (
                dashboardSummary
                  ?.counts.pending ?? 0
              )
              +
              (
                dashboardSummary
                  ?.counts.running ?? 0
              )
            )
          }
          tone="neutral"
          badge="Canlı"
        />

        <StatCard
          icon={CheckCircle2}
          label="Tamamlanan"
          value={
            String(
              dashboardSummary
                ?.counts.completed ?? 0
            )
          }
          tone="green"
          badge="Canlı"
        />

        <StatCard
          icon={TriangleAlert}
          label="Başarısız"
          value={
            String(
              dashboardSummary
                ?.counts.failed ?? 0
            )
          }
          tone="red"
          badge="Canlı"
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

            <div className="border-b border-[#eee7e3] px-5 py-3 dark:border-white/[0.06]">
              {latestAnalysis ? (
                <div className="flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-[10px] font-medium text-[#998c91] dark:text-[#81747a]">
                      Son analiz #{latestAnalysis.id}
                    </p>

                    <p className="mt-1 truncate text-xs font-semibold text-[#514348] dark:text-[#d2c4c9]">
                      {latestAnalysis.claim_text}
                    </p>
                  </div>

                  <button
                    type="button"
                    onClick={() =>
                      navigate(
                        `/analyses/${latestAnalysis.id}`
                      )
                    }
                    className="shrink-0 rounded-lg border border-[#e5dad5] px-2.5 py-1.5 text-[10px] font-semibold text-[#745f67] transition hover:bg-[#faf6f4] dark:border-white/[0.08] dark:text-[#a99aa0] dark:hover:bg-white/[0.04]"
                  >
                    Aç
                  </button>
                </div>
              ) : (
                <p className="text-xs text-[#998c91] dark:text-[#81747a]">
                  Henüz analiz kaydı yok.
                </p>
              )}
            </div>

            <div className="divide-y divide-[#eee7e3] dark:divide-white/[0.06]">
              {analysisStages.map(
                (
                  item,
                  index
                ) => {
                  const isCurrent =
                    latestAnalysis
                    &&
                    !item.done
                    &&
                    index ===
                      currentStageIndex
                    &&
                    (
                      latestAnalysis.status
                        === "running"
                      ||
                      latestAnalysis.status
                        === "pending"
                    );

                  const failed =
                    latestAnalysis
                      ?.status
                      === "failed"
                    &&
                    index ===
                      currentStageIndex;

                  const statusLabel =
                    item.done
                      ? "Tamamlandı"
                      : failed
                        ? "Başarısız"
                        : isCurrent
                          ? (
                              latestAnalysis
                                ?.status
                                === "pending"
                                ? "Kuyrukta"
                                : "Çalışıyor"
                            )
                          : "Bekliyor";

                  return (
                    <div
                      key={
                        item.label
                      }
                      className="flex items-center justify-between gap-4 px-5 py-3.5"
                    >
                      <div>
                        <p className="text-xs font-semibold text-[#514348] dark:text-[#d2c4c9]">
                          {item.label}
                        </p>

                        <p className="mt-1 text-[10px] text-[#9b8e92] dark:text-[#7d7076]">
                          {item.detail}
                        </p>
                      </div>

                      <span
                        className={[
                          "rounded-md px-2 py-1 text-[10px] font-semibold",
                          item.done
                            ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-400/[0.07] dark:text-emerald-300"
                            : failed
                              ? "bg-red-50 text-red-600 dark:bg-red-400/[0.07] dark:text-red-300"
                              : isCurrent
                                ? "bg-[#fff1e9] text-[#b95531] dark:bg-[#ff895d]/[0.08] dark:text-[#ff9872]"
                                : "bg-[#f5f1ef] text-[#8f8086] dark:bg-white/[0.04] dark:text-[#776a70]",
                        ].join(
                          " "
                        )}
                      >
                        {statusLabel}
                      </span>
                    </div>
                  );
                }
              )}
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
                Yetki kapsamındaki gerçek analiz kayıtları
              </p>
            </div>

            <span className="rounded-md border border-[#e9e1dd] bg-[#faf7f5] px-2 py-1 text-[9px] font-semibold uppercase tracking-[0.08em] text-[#9b8e92] dark:border-white/[0.07] dark:bg-white/[0.035] dark:text-[#786b71]">
              Canlı veri
            </span>
          </div>

          <dl className="grid grid-cols-2 gap-px bg-[#eee7e3] dark:bg-white/[0.06]">
            {[
              [
                "Toplam analiz",
                String(
                  dashboardSummary
                    ?.counts.total ?? 0
                ),
              ],
              [
                "Kuyrukta",
                String(
                  dashboardSummary
                    ?.counts.pending ?? 0
                ),
              ],
              [
                "Çalışıyor",
                String(
                  dashboardSummary
                    ?.counts.running ?? 0
                ),
              ],
              [
                "Tamamlandı",
                String(
                  dashboardSummary
                    ?.counts.completed ?? 0
                ),
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
