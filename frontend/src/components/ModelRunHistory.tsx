import {
  Bot,
  Clock3,
  Database,
  Network,
} from "lucide-react";

import type {
  AnalysisModelRun,
} from "../api/client";


function formatDate(
  value: string
): string {
  return new Intl.DateTimeFormat(
    "tr-TR",
    {
      dateStyle: "medium",
      timeStyle: "short",
    }
  ).format(
    new Date(value)
  );
}


function sourceLabel(
  source: AnalysisModelRun["source"]
): string {
  switch (source) {
    case "pipeline":
      return "Analiz pipeline";

    case "agent_tool":
      return "AI agent";

    case "legacy_import":
      return "Legacy snapshot";

    default:
      return source;
  }
}


function kindLabel(
  kind: AnalysisModelRun["kind"]
): string {
  return (
    kind === "gnn"
      ? "GNN"
      : "Bot"
  );
}


function modelLabel(
  run: AnalysisModelRun
): string {
  if (run.model_name) {
    return run.model_name;
  }

  return "Provenance bilinmiyor";
}


export default function ModelRunHistory({
  runs,
  loading = false,
  error = null,
}: {
  runs: AnalysisModelRun[];
  loading?: boolean;
  error?: string | null;
}) {
  return (
    <section className="rounded-xl border border-[#e7dfdc] bg-white shadow-soft-panel dark:border-white/[0.08] dark:bg-[#1c1219] dark:shadow-dark-panel">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#eee7e3] px-5 py-4 dark:border-white/[0.07]">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-[#dfd4cf] bg-[#faf6f3] text-[#765f68] dark:border-white/[0.08] dark:bg-white/[0.04] dark:text-[#b7a6ad]">
            <Database
              size={17}
              strokeWidth={1.8}
            />
          </div>

          <div>
            <p className="text-sm font-semibold text-[#302529] dark:text-[#f8efec]">
              Model Run History
            </p>

            <p className="mt-0.5 text-[11px] text-[#988b90] dark:text-[#7d7076]">
              Model inference provenance ve geçmiş çalıştırmalar
            </p>
          </div>
        </div>

        <span className="rounded-md border border-[#e7dfdc] bg-[#faf8f6] px-2.5 py-1 text-[10px] font-semibold text-[#85777c] dark:border-white/[0.08] dark:bg-white/[0.035] dark:text-[#8e8087]">
          {runs.length} run
        </span>
      </div>

      <div className="p-4 sm:p-5">
        {loading && (
          <div className="rounded-lg border border-dashed border-[#ddd3cf] px-4 py-5 text-center text-xs text-[#95878c] dark:border-white/[0.10] dark:text-[#82747b]">
            Model geçmişi yükleniyor...
          </div>
        )}

        {!loading && error && (
          <div className="rounded-lg border border-[#e5d7d3] bg-[#fcf7f5] px-4 py-4 text-xs text-[#9b6254] dark:border-[#d98a74]/15 dark:bg-[#d98a74]/[0.05] dark:text-[#c38b7c]">
            {error}
          </div>
        )}

        {!loading &&
          !error &&
          runs.length === 0 && (
            <div className="rounded-lg border border-dashed border-[#ddd3cf] px-4 py-5 text-center dark:border-white/[0.10]">
              <p className="text-xs font-medium text-[#76686d] dark:text-[#aa9ca2]">
                Henüz model run kaydı yok.
              </p>

              <p className="mt-1 text-[10px] text-[#a19499] dark:text-[#75686e]">
                Yeni GNN veya bot inference çalışmaları burada görünecek.
              </p>
            </div>
          )}

        {!loading &&
          !error &&
          runs.length > 0 && (
            <div className="space-y-3">
              {runs.map(
                (run, index) => {
                  const Icon =
                    run.kind === "gnn"
                      ? Network
                      : Bot;

                  const legacy =
                    run.source ===
                    "legacy_import";

                  return (
                    <article
                      key={run.id}
                      className="relative rounded-lg border border-[#e9e1de] bg-[#fcfaf9] p-4 dark:border-white/[0.07] dark:bg-[#160f15]"
                    >
                      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                        <div className="flex min-w-0 items-start gap-3">
                          <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-[#e2d8d4] bg-white text-[#78656c] dark:border-white/[0.08] dark:bg-white/[0.035] dark:text-[#aa989f]">
                            <Icon
                              size={17}
                              strokeWidth={1.8}
                            />
                          </div>

                          <div className="min-w-0">
                            <div className="flex flex-wrap items-center gap-2">
                              <p className="text-xs font-semibold text-[#413439] dark:text-[#e8dcdf]">
                                {kindLabel(
                                  run.kind
                                )}
                              </p>

                              {index === 0 && (
                                <span className="rounded-md bg-[#f0ebe8] px-2 py-0.5 text-[9px] font-semibold uppercase tracking-[0.08em] text-[#716268] dark:bg-white/[0.06] dark:text-[#a99aa0]">
                                  Son run
                                </span>
                              )}

                              {legacy && (
                                <span className="rounded-md border border-[#dfd4cf] px-2 py-0.5 text-[9px] font-medium text-[#8e7d82] dark:border-white/[0.09] dark:text-[#8c7c83]">
                                  Legacy
                                </span>
                              )}

                              {run.cross_domain && (
                                <span className="rounded-md border border-[#e1d3ca] bg-[#fbf5f1] px-2 py-0.5 text-[9px] font-medium text-[#936d5c] dark:border-[#c58e72]/15 dark:bg-[#c58e72]/[0.05] dark:text-[#b78d79]">
                                  Cross-domain
                                </span>
                              )}
                            </div>

                            <p className="mt-1.5 break-all text-sm font-medium text-[#33272b] dark:text-[#f1e5e8]">
                              {modelLabel(run)}
                            </p>

                            <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-[10px] text-[#94868b] dark:text-[#796c72]">
                              <span>
                                Kaynak:{" "}
                                {sourceLabel(
                                  run.source
                                )}
                              </span>

                              <span>
                                Feature set:{" "}
                                {run.feature_set ||
                                  "bilinmiyor"}
                              </span>

                              <span>
                                Graph:{" "}
                                {run.graph_id_snapshot ??
                                  "bilinmiyor"}
                              </span>
                            </div>
                          </div>
                        </div>

                        <div className="flex shrink-0 items-center gap-1.5 text-[10px] text-[#9d9094] dark:text-[#776a70]">
                          <Clock3
                            size={12}
                            strokeWidth={1.8}
                          />

                          {formatDate(
                            run.generated_at
                          )}
                        </div>
                      </div>

                      <details className="mt-4 border-t border-[#eee7e4] pt-3 dark:border-white/[0.06]">
                        <summary className="cursor-pointer text-[10px] font-medium text-[#897b80] hover:text-[#5d4e53] dark:text-[#796b72] dark:hover:text-[#ada0a5]">
                          Ham model çıktısını göster
                        </summary>

                        <pre className="mt-3 max-h-[260px] overflow-auto whitespace-pre-wrap break-words rounded-lg bg-[#f7f4f2] p-3 text-[10px] leading-5 text-[#776a6f] dark:bg-[#100b0f] dark:text-[#84767c]">
                          {JSON.stringify(
                            run.result,
                            null,
                            2
                          )}
                        </pre>
                      </details>
                    </article>
                  );
                }
              )}
            </div>
          )}
      </div>
    </section>
  );
}
