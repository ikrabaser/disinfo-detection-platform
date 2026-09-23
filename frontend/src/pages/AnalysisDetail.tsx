import {
  useEffect,
  useRef,
  useState,
} from "react";
import {
  useParams,
  useSearchParams,
} from "react-router-dom";

import {
  getAnalysis,
  getPropagationGraph,
  runAnalysis,
  type Analysis,
} from "../api/client";

import PropagationGraph from "../components/PropagationGraph";

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
  graph: "Yayılım grafiği",
  gnn: "GNN analizi",
  bot_detection: "Bot analizi",
  completed: "Analiz tamamlandı",
  failed: "Analiz başarısız",
};


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


  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-800">
          Analiz Detayı #{analysisId}
        </h1>

        {error && (
          <p className="mt-1 text-xs text-red-600">
            {error}
          </p>
        )}
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-xs font-medium uppercase tracking-[0.12em] text-slate-400">
              Canlı analiz süreci
            </p>

            <p className="mt-1 text-sm font-medium text-slate-800">
              {stage}
            </p>
          </div>

          <span className="text-lg font-semibold text-slate-900">
            {progress}%
          </span>
        </div>

        <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-100">
          <div
            className="h-full rounded-full bg-slate-900 transition-all duration-500"
            style={{
              width: `${progress}%`,
            }}
          />
        </div>

        <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-500">
          <span>5% Başlatıldı</span>
          <span>•</span>
          <span>15% NLP</span>
          <span>•</span>
          <span>35% Graph</span>
          <span>•</span>
          <span>60% GNN</span>
          <span>•</span>
          <span>80% Bot</span>
          <span>•</span>
          <span>100% Tamamlandı</span>
        </div>
      </div>

      {analysis && (
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-sm text-slate-700">
            {analysis.claim_text}
          </p>

          <div className="mt-3 grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
            <div>
              <p className="text-slate-400">
                Durum
              </p>

              <p className="font-medium">
                {analysis.status}
              </p>
            </div>

            <div>
              <p className="text-slate-400">
                Doğruluk Skoru
              </p>

              <p className="font-medium">
                {analysis.truth_score !==
                null
                  ? `${(
                      analysis.truth_score *
                      100
                    ).toFixed(0)}%`
                  : "-"}
              </p>
            </div>
          </div>
        </div>
      )}

      <PropagationGraph
        data={propagationGraph}
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <h3 className="text-sm font-medium text-slate-600">
            NLP Sonucu
          </h3>

          <pre className="mt-2 overflow-auto text-xs text-slate-500">
            {JSON.stringify(
              analysis?.nlp_result ??
                {
                  durum:
                    "Analiz bekleniyor",
                },
              null,
              2
            )}
          </pre>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <h3 className="text-sm font-medium text-slate-600">
            GNN Sonucu
          </h3>

          <pre className="mt-2 overflow-auto text-xs text-slate-500">
            {JSON.stringify(
              analysis?.gnn_result ??
                {
                  durum:
                    "Analiz bekleniyor",
                },
              null,
              2
            )}
          </pre>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <h3 className="text-sm font-medium text-slate-600">
            Bot Analizi
          </h3>

          <pre className="mt-2 overflow-auto text-xs text-slate-500">
            {JSON.stringify(
              analysis?.bot_analysis_result ??
                {
                  durum:
                    "Analiz bekleniyor",
                },
              null,
              2
            )}
          </pre>
        </div>
      </div>
    </div>
  );
}
