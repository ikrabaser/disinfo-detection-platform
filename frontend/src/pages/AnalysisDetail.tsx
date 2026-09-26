import {
  Activity,
  ArrowLeft,
  Bot,
  BrainCircuit,
  CalendarDays,
  Check,
  CircleCheck,
  Clock3,
  Database,
  Hash,
  MessageSquareText,
  Network,
} from "lucide-react";
import {
  useEffect,
  useRef,
  useState,
} from "react";
import {
  Link,
  useParams,
  useSearchParams,
} from "react-router-dom";

import {
  getAnalysis,
  getAnalysisModelRuns,
  getPropagationGraph,
  runAnalysis,
  type Analysis,
  type AnalysisModelRun,
} from "../api/client";

import ModelRunHistory from "../components/ModelRunHistory";
import PropagationGraph from "../components/PropagationGraph";
import AIEvidencePanel from "../components/AIEvidencePanel";

import type {
  PropagationGraphData,
} from "../types";

import {
  subscribeToAnalysisProgress,
  type AnalysisProgressEvent,
} from "../realtime/analysisProgress";


const STAGE_LABELS: Record<string, string> = {
  started: "Analiz başlatıldı",
  nlp: "NLP sınıflandırması",
  graph: "Yayılım grafiği oluşturuluyor",
  gnn: "GNN analizi",
  bot_detection: "Bot analizi",
  ai_evidence: "AI kanıt analizi",
  completed: "Analiz tamamlandı",
  failed: "Analiz başarısız",
};


const STEPS = [
  { value: 5, label: "Başlatıldı" },
  { value: 15, label: "NLP" },
  { value: 35, label: "Graph" },
  { value: 60, label: "GNN" },
  { value: 80, label: "Bot" },
  { value: 90, label: "AI" },
  { value: 100, label: "Tamamlandı" },
];


function asNumber(
  value: unknown,
  fallback = 0
): number {
  return typeof value === "number"
    ? value
    : fallback;
}


function formatPercent(
  value: number
): string {
  return `${(value * 100).toFixed(1)}%`;
}


function formatDate(
  value?: string
): string {
  if (!value) {
    return "-";
  }

  return new Intl.DateTimeFormat(
    "tr-TR",
    {
      dateStyle: "medium",
      timeStyle: "short",
    }
  ).format(new Date(value));
}


function MetricCard({
  icon: Icon,
  title,
  subtitle,
  value,
  note,
  tone,
}: {
  icon: typeof BrainCircuit;
  title: string;
  subtitle: string;
  value: string;
  note?: string;
  tone:
    | "purple"
    | "orange"
    | "red"
    | "neutral";
}) {
  const toneClasses = {
    purple:
      "border-[#8c55b7]/20 bg-[#f8f1fc] text-[#75479a] dark:border-[#b36fdc]/20 dark:bg-[#a855f7]/[0.08] dark:text-[#c88deb]",
    orange:
      "border-[#d96b3f]/20 bg-[#fff3ec] text-[#b95430] dark:border-[#ff895d]/20 dark:bg-[#ff895d]/[0.08] dark:text-[#ff9c78]",
    red:
      "border-[#d84c5d]/20 bg-[#fff0f2] text-[#c74656] dark:border-[#fb6674]/20 dark:bg-[#fb6674]/[0.08] dark:text-[#ff8390]",
    neutral:
      "border-[#a47a68]/20 bg-[#f7f2ef] text-[#76594c] dark:border-[#d6a184]/15 dark:bg-[#d6a184]/[0.06] dark:text-[#d9ad96]",
  };

  return (
    <div
      className={[
        "rounded-xl border p-4",
        "shadow-[0_10px_28px_rgba(40,25,31,0.035)]",
        "dark:shadow-none",
        toneClasses[tone],
      ].join(" ")}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-current/10 bg-white/60 dark:bg-white/[0.04]">
            <Icon
              size={18}
              strokeWidth={1.8}
            />
          </div>

          <div>
            <p className="text-sm font-semibold text-[#302529] dark:text-[#f8efed]">
              {title}
            </p>

            <p className="mt-0.5 text-[11px] text-[#988b90] dark:text-[#81737a]">
              {subtitle}
            </p>
          </div>
        </div>
      </div>

      <div className="mt-4">
        <p className="text-2xl font-semibold tracking-tight text-[#2b2024] dark:text-[#fff7f4]">
          {value}
        </p>

        {note && (
          <p className="mt-1.5 text-[11px] leading-4 text-[#9b8d92] dark:text-[#95878d]">
            {note}
          </p>
        )}
      </div>
    </div>
  );
}


export default function AnalysisDetail() {
  const { analysisId } =
    useParams<{ analysisId: string }>();

  const [
    searchParams,
    setSearchParams,
  ] = useSearchParams();

  const autoRunRef = useRef(
    searchParams.get("run") === "1"
  );

  const runTriggeredRef =
    useRef(false);

  const [analysis, setAnalysis] =
    useState<Analysis | null>(null);


  const [
    modelRuns,
    setModelRuns,
  ] = useState<AnalysisModelRun[]>([]);

  const [
    modelRunsLoading,
    setModelRunsLoading,
  ] = useState(true);

  const [
    modelRunsError,
    setModelRunsError,
  ] = useState<string | null>(null);

  const [
    propagationGraph,
    setPropagationGraph,
  ] = useState<
    PropagationGraphData | undefined
  >();

  const [error, setError] =
    useState<string | null>(null);

  const [progress, setProgress] =
    useState(0);

  const [stage, setStage] =
    useState("Bağlantı hazırlanıyor");


  async function loadAnalysis(
    id: number
  ) {
    const data = await getAnalysis(id);

    setAnalysis(data);

    setModelRunsLoading(true);
    setModelRunsError(null);

    try {
      const runs =
        await getAnalysisModelRuns(id);

      setModelRuns(runs);
    } catch {
      setModelRunsError(
        "Model run geçmişi yüklenemedi."
      );
    } finally {
      setModelRunsLoading(false);
    }

    if (data.propagation_graph) {
      const graph =
        await getPropagationGraph(
          data.propagation_graph
        );

      setPropagationGraph({
        nodes: graph.nodes,
        edges: graph.edges,
      });
    }

    if (data.status === "completed") {
      setProgress(100);
      setStage(
        STAGE_LABELS.completed
      );
    }

    if (data.status === "failed") {
      setStage(
        STAGE_LABELS.failed
      );
    }
  }


  useEffect(() => {
    if (!analysisId) {
      return;
    }

    let cancelled = false;

    const numericId =
      Number(analysisId);

    loadAnalysis(numericId)
      .catch(() => {
        if (!cancelled) {
          setError(
            "Analiz backend'den yüklenemedi."
          );
        }
      });

    const cleanup =
      subscribeToAnalysisProgress(
        numericId,
        {
          onSubscribed: async () => {
            if (cancelled) {
              return;
            }

            setStage(
              "Gerçek zamanlı bağlantı hazır"
            );

            if (
              !autoRunRef.current ||
              runTriggeredRef.current
            ) {
              return;
            }

            runTriggeredRef.current =
              true;

            try {
              await runAnalysis(
                numericId
              );

              setError(null);

              setSearchParams(
                {},
                {
                  replace: true,
                }
              );
            } catch {
              const current =
                await getAnalysis(
                  numericId
                ).catch(() => null);

              if (
                current?.status ===
                  "running" ||
                current?.status ===
                  "completed"
              ) {
                setError(null);

                setSearchParams(
                  {},
                  {
                    replace: true,
                  }
                );

                return;
              }

              setError(
                "Analiz kuyruğa eklenemedi."
              );
            }
          },

          onProgress: (
            event:
              AnalysisProgressEvent
          ) => {
            if (cancelled) {
              return;
            }

            const percentage =
              Math.round(
                event.progress * 100
              );

            setProgress(
              Math.max(
                0,
                Math.min(
                  100,
                  percentage
                )
              )
            );

            setStage(
              STAGE_LABELS[
                event.stage
              ] ?? event.stage
            );

            if (
              event.stage ===
                "completed" ||
              event.stage ===
                "failed"
            ) {
              loadAnalysis(
                numericId
              ).catch(() => {
                if (!cancelled) {
                  setError(
                    "Son analiz sonucu alınamadı."
                  );
                }
              });
            }
          },
        }
      );

    return () => {
      cancelled = true;
      cleanup();
    };
  }, [
    analysisId,
    setSearchParams,
  ]);


  const nlpConfidence =
    asNumber(
      analysis?.nlp_result
        ?.confidence
    );

  const nlpLabel =
    typeof analysis?.nlp_result
      ?.label === "string"
      ? analysis.nlp_result.label
      : "-";

  const gnnConfidence =
    asNumber(
      analysis?.gnn_result
        ?.confidence
    );

  const gnnLabel =
    typeof analysis?.gnn_result
      ?.predicted_label ===
      "string"
      ? analysis.gnn_result
          .predicted_label
      : "-";

  const botResult =
    analysis?.bot_analysis_result;

  const botUserCount =
    asNumber(
      botResult?.user_count
    );

  const botFlaggedCount =
    asNumber(
      botResult?.flagged_count
    );

  const botModel =
    typeof botResult?.model ===
      "string"
      ? botResult.model
      : null;

  const botCrossDomain =
    botResult?.cross_domain ===
    true;

  const botScoreCalibrated =
    botResult?.score_calibrated ===
    true;

  const nodeCount =
    propagationGraph?.nodes.length ??
    0;

  const edgeCount =
    propagationGraph?.edges.length ??
    0;

  const completed =
    analysis?.status ===
    "completed";


  return (
    <div className="mx-auto w-full max-w-[1600px] space-y-5">
      <section>
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-xs font-medium text-[#8b7d82] transition hover:text-[#4c3e43] dark:text-[#786a71] dark:hover:text-[#d7c9ce]"
        >
          <ArrowLeft
            size={14}
          />
          Analizler
        </Link>

        <div className="mt-3 flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="text-[28px] font-semibold tracking-[-0.025em] text-[#241b1f] dark:text-[#fff8f5]">
                Analiz Detayı #{analysisId}
              </h1>

              <span
                className={[
                  "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-semibold",
                  completed
                    ? "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-400/20 dark:bg-emerald-400/[0.08] dark:text-emerald-300"
                    : "border-[#e5d6cd] bg-[#faf3ef] text-[#9b5c40] dark:border-[#ff895d]/15 dark:bg-[#ff895d]/[0.07] dark:text-[#ff9b75]",
                ].join(" ")}
              >
                <span className="h-1.5 w-1.5 rounded-full bg-current" />

                {completed
                  ? "Tamamlandı"
                  : analysis?.status ??
                    "Bekliyor"}
              </span>
            </div>

            <div className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-[#84777c] dark:text-[#8e8087]">
              <span className="flex items-center gap-1.5">
                <BrainCircuit
                  size={14}
                  className="text-[#c86038] dark:text-[#ff895d]"
                />

                Konu:
                <strong className="font-semibold text-[#514348] dark:text-[#cfc1c6]">
                  {analysis?.claim_text ??
                    "-"}
                </strong>
              </span>

              <span className="hidden h-4 w-px bg-[#ddd4d0] dark:bg-white/[0.08] sm:block" />

              <span className="flex items-center gap-1.5">
                <CalendarDays
                  size={14}
                />
                {formatDate(
                  analysis?.created_at
                )}
              </span>

              <span className="flex items-center gap-1.5">
                <Hash size={14} />
                Analiz ID:
                {analysisId}
              </span>
            </div>
          </div>
        </div>

        {analysisId && (
          <div className="mt-4">
            <Link
              to={`/assistant?analysis=${analysisId}`}
              className="inline-flex items-center gap-2 rounded-lg border border-[#e0d4cf] bg-white px-3 py-2 text-xs font-semibold text-[#59484e] transition hover:border-[#cda897] hover:bg-[#fff8f4] dark:border-white/[0.09] dark:bg-white/[0.025] dark:text-[#d8cbd0] dark:hover:border-[#ff895d]/20"
            >
              <MessageSquareText
                size={15}
              />
              Assistant'a Sor
            </Link>
          </div>
        )}

        {error && (
          <div className="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-xs text-red-700 dark:border-red-400/15 dark:bg-red-400/[0.07] dark:text-red-300">
            {error}
          </div>
        )}
      </section>

      <section className="overflow-hidden rounded-xl border border-[#e7dfdc] bg-white shadow-soft-panel dark:border-white/[0.08] dark:bg-[#1c1219] dark:shadow-dark-panel">
        <div className="grid gap-6 p-5 lg:grid-cols-[260px_1fr_90px] lg:items-center">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl border border-[#f0cbbb] bg-[#fff2eb] text-[#c25b35] dark:border-[#ff895d]/15 dark:bg-[#ff895d]/[0.08] dark:text-[#ff976e]">
              <Activity
                size={20}
                strokeWidth={1.8}
              />
            </div>

            <div>
              <p className="text-sm font-semibold text-[#302529] dark:text-[#f8efec]">
                Analiz Süreci
              </p>

              <p className="mt-0.5 text-[11px] text-[#93868a] dark:text-[#81747a]">
                {stage}
              </p>
            </div>
          </div>

          <div className="relative">
            <div className="absolute left-4 right-4 top-[15px] h-px bg-[#e4dad6] dark:bg-white/[0.09]" />

            <div
              className="absolute left-4 top-[15px] h-px bg-[#d96b3f] transition-all duration-500 dark:bg-[#ff895d]"
              style={{
                width:
                  progress <= 5
                    ? "0%"
                    : `${Math.min(
                        100,
                        progress
                      )}%`,
              }}
            />

            <div className="relative grid grid-cols-7 gap-1">
              {STEPS.map(
                (step) => {
                  const active =
                    progress >=
                    step.value;

                  return (
                    <div
                      key={
                        step.value
                      }
                      className="text-center"
                    >
                      <div
                        className={[
                          "mx-auto flex h-8 w-8 items-center justify-center rounded-full border text-[10px] transition",
                          active
                            ? "border-[#d96b3f] bg-[#d96b3f] text-white shadow-[0_4px_14px_rgba(217,107,63,0.22)] dark:border-[#ff895d] dark:bg-[#ff895d] dark:text-[#271218]"
                            : "border-[#ded4d0] bg-white text-[#aaa0a3] dark:border-white/[0.12] dark:bg-[#251820] dark:text-[#796c72]",
                        ].join(
                          " "
                        )}
                      >
                        {active ? (
                          <Check
                            size={
                              14
                            }
                            strokeWidth={
                              2.2
                            }
                          />
                        ) : (
                          step.value
                        )}
                      </div>

                      <p className="mt-2 text-[10px] font-medium text-[#81747a] dark:text-[#a79aa0]">
                        {step.value}%{" "}
                        {
                          step.label
                        }
                      </p>
                    </div>
                  );
                }
              )}
            </div>
          </div>

          <div className="text-right">
            <p className="text-[28px] font-semibold tracking-tight text-[#2b2024] dark:text-[#fff8f5]">
              {progress}%
            </p>

            <p className="mt-0.5 text-[10px] text-[#9d9095] dark:text-[#75686f]">
              {completed
                ? "Tamamlandı"
                : "Devam ediyor"}
            </p>
          </div>
        </div>
      </section>

      <section className="grid items-start gap-4 xl:grid-cols-[1fr_320px]">
        <div className="rounded-xl border border-[#e7dfdc] bg-white p-4 shadow-soft-panel dark:border-white/[0.08] dark:bg-[#1c1219] dark:shadow-dark-panel">
          <div className="mb-4 flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#f5eef7] text-[#7c4d94] dark:bg-[#a855f7]/[0.08] dark:text-[#c689e7]">
              <Database
                size={17}
              />
            </div>

            <div>
              <h2 className="text-sm font-semibold text-[#302529] dark:text-[#f8efec]">
                Genel Sonuç
              </h2>

              <p className="mt-0.5 text-[11px] text-[#988b90] dark:text-[#7e7077]">
                Analiz çıktılarının özet görünümü
              </p>
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <MetricCard
              icon={
                BrainCircuit
              }
              title="NLP Sonucu"
              subtitle={`Sınıf: ${nlpLabel}`}
              value={
                nlpConfidence
                  ? formatPercent(
                      nlpConfidence
                    )
                  : "-"
              }
              tone="purple"
            />

            <MetricCard
              icon={Network}
              title="GNN Sonucu"
              subtitle={`Tahmin: ${gnnLabel}`}
              value={
                gnnConfidence
                  ? formatPercent(
                      gnnConfidence
                    )
                  : "-"
              }
              note="Cross-domain deneysel model sinyali"
              tone="orange"
            />

            <MetricCard
              icon={Bot}
              title="Bot Analizi"
              subtitle={
                botModel
                  ? "Random Forest"
                  : "Model bekleniyor"
              }
              value={
                botModel
                  ? `${botFlaggedCount}/${botUserCount} işaretli`
                  : "-"
              }
              note={
                botModel
                  ? [
                      botCrossDomain
                        ? "Cross-domain"
                        : "In-domain",
                      botScoreCalibrated
                        ? "Kalibre edilmiş"
                        : "Kalibre edilmemiş model skoru",
                    ].join(" • ")
                  : "Bot analizi henüz tamamlanmadı"
              }
              tone="orange"
            />

            <MetricCard
              icon={Database}
              title="Ağ Özeti"
              subtitle={`${edgeCount} bağlantı`}
              value={`${nodeCount} düğüm`}
              tone="neutral"
            />
          </div>
        </div>

        <aside className="rounded-xl border border-[#e7dfdc] bg-white p-4 shadow-soft-panel dark:border-white/[0.08] dark:bg-[#1c1219] dark:shadow-dark-panel">
          <div className="flex items-center gap-3 border-b border-[#eee7e3] pb-3 dark:border-white/[0.07]">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#fff1ea] text-[#bf5a35] dark:bg-[#ff895d]/[0.08] dark:text-[#ff956d]">
              <CircleCheck
                size={16}
              />
            </div>

            <h2 className="text-sm font-semibold text-[#302529] dark:text-[#f8efec]">
              Analiz Özeti
            </h2>
          </div>

          <dl className="mt-2 divide-y divide-[#eee7e3] text-xs dark:divide-white/[0.06]">
            <div className="flex justify-between gap-4 py-2.5">
              <dt className="text-[#96898e] dark:text-[#97898f]">
                Konu
              </dt>

              <dd className="max-w-[170px] truncate font-medium text-[#4b3e43] dark:text-[#d4c6cb]">
                {analysis?.claim_text ??
                  "-"}
              </dd>
            </div>

            <div className="flex justify-between gap-4 py-2.5">
              <dt className="text-[#96898e] dark:text-[#97898f]">
                Durum
              </dt>

              <dd className="font-medium text-emerald-700 dark:text-emerald-300">
                {completed
                  ? "Tamamlandı"
                  : analysis?.status ??
                    "-"}
              </dd>
            </div>

            <div className="flex justify-between gap-4 py-2.5">
              <dt className="text-[#96898e] dark:text-[#97898f]">
                Başlangıç
              </dt>

              <dd className="font-medium text-[#4b3e43] dark:text-[#d4c6cb]">
                {formatDate(
                  analysis?.created_at
                )}
              </dd>
            </div>

            <div className="flex justify-between gap-4 py-2.5">
              <dt className="text-[#96898e] dark:text-[#97898f]">
                Son güncelleme
              </dt>

              <dd className="font-medium text-[#4b3e43] dark:text-[#d4c6cb]">
                {formatDate(
                  analysis?.updated_at
                )}
              </dd>
            </div>

            <div className="flex justify-between gap-4 py-2.5">
              <dt className="text-[#96898e] dark:text-[#97898f]">
                Analiz ID
              </dt>

              <dd className="font-medium text-[#4b3e43] dark:text-[#d4c6cb]">
                #{analysisId}
              </dd>
            </div>

            <div className="flex justify-between gap-4 py-2.5">
              <dt className="text-[#96898e] dark:text-[#97898f]">
                Birleşik skor
              </dt>

              <dd className="font-medium text-[#8d7f84] dark:text-[#82747b]">
                Hesaplanmıyor
              </dd>
            </div>
          </dl>
        </aside>
      </section>

      <AIEvidencePanel
        result={
          analysis?.ai_analysis_result ??
          null
        }
      />

      <PropagationGraph
        data={propagationGraph}
      />

      <ModelRunHistory
        runs={modelRuns}
        loading={modelRunsLoading}
        error={modelRunsError}
      />

      <details className="group rounded-xl border border-[#e7dfdc] bg-white shadow-soft-panel dark:border-white/[0.08] dark:bg-[#1c1219] dark:shadow-dark-panel">
        <summary className="flex cursor-pointer list-none items-center justify-between px-5 py-4">
          <div>
            <p className="text-sm font-semibold text-[#302529] dark:text-[#f8efec]">
              Teknik Detaylar
            </p>

            <p className="mt-0.5 text-[11px] text-[#988b90] dark:text-[#7d7076]">
              Ham NLP, GNN, bot ve AI analiz çıktıları
            </p>
          </div>

          <span className="text-xs text-[#9b8e92] dark:text-[#74676d]">
            JSON çıktıları
          </span>
        </summary>

        <div className="grid gap-3 border-t border-[#eee7e3] p-4 dark:border-white/[0.07] lg:grid-cols-2 xl:grid-cols-4">
          {[
            [
              "NLP Sonucu",
              analysis?.nlp_result,
            ],
            [
              "GNN Sonucu",
              analysis?.gnn_result,
            ],
            [
              "Bot Analizi",
              analysis?.bot_analysis_result,
            ],
            [
              "AI Evidence",
              analysis?.ai_analysis_result,
            ],
          ].map(
            ([title, data]) => (
              <div
                key={
                  title as string
                }
                className="min-w-0 rounded-lg border border-[#ebe3df] bg-[#fbf9f8] p-4 dark:border-white/[0.06] dark:bg-[#160f15]"
              >
                <p className="mb-3 text-xs font-semibold text-[#594b50] dark:text-[#c5b7bc]">
                  {title as string}
                </p>

                <pre className="max-h-[300px] overflow-auto whitespace-pre-wrap break-words text-[10px] leading-5 text-[#7f7176] dark:text-[#91838a]">
                  {JSON.stringify(
                    data ?? {
                      durum:
                        "Analiz bekleniyor",
                    },
                    null,
                    2
                  )}
                </pre>
              </div>
            )
          )}
        </div>
      </details>
    </div>
  );
}
