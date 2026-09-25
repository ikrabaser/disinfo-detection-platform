import {
  ExternalLink,
  FileSearch,
  Sparkles,
  TriangleAlert,
} from "lucide-react";

import type {
  AIAnalysisResult,
} from "../api/client";


function statusLabel(
  status?: string
) {
  switch (status) {
    case "supported":
      return "Mevcut kanıtlarla destekleniyor";

    case "contradicted":
      return "Mevcut kanıtlarla çelişiyor";

    case "mixed":
      return "Kanıtlar çelişkili";

    default:
      return "Kanıt yetersiz";
  }
}


function stanceLabel(
  stance?: string
) {
  switch (stance) {
    case "support":
      return "Destekliyor";

    case "contradict":
      return "Çelişiyor";

    case "neutral":
      return "Nötr";

    default:
      return "Yetersiz";
  }
}


export default function AIEvidencePanel({
  result,
}: {
  result: AIAnalysisResult | null;
}) {
  const report = result?.report;

  if (!result) {
    return (
      <section className="rounded-xl border border-[#e7dfdc] bg-white p-5 shadow-soft-panel dark:border-white/[0.08] dark:bg-[#1c1219] dark:shadow-dark-panel">
        <div className="flex items-center gap-3">
          <Sparkles
            size={18}
            className="text-[#c86038] dark:text-[#ff895d]"
          />

          <div>
            <h2 className="text-sm font-semibold text-[#302529] dark:text-[#f8efec]">
              AI Evidence Analysis
            </h2>

            <p className="mt-1 text-xs text-[#93868a] dark:text-[#81747a]">
              Analiz sonucu henüz oluşturulmadı.
            </p>
          </div>
        </div>
      </section>
    );
  }

  if (
    result.status !== "completed" ||
    !report
  ) {
    return (
      <section className="rounded-xl border border-[#e7dfdc] bg-white p-5 shadow-soft-panel dark:border-white/[0.08] dark:bg-[#1c1219] dark:shadow-dark-panel">
        <div className="flex items-start gap-3">
          <TriangleAlert
            size={18}
            className="mt-0.5 text-[#b76a31] dark:text-[#e9a05f]"
          />

          <div>
            <h2 className="text-sm font-semibold text-[#302529] dark:text-[#f8efec]">
              AI Evidence Analysis
            </h2>

            <p className="mt-1 text-xs leading-5 text-[#887a80] dark:text-[#95878d]">
              AI evidence katmanı bu analiz için kullanılamadı.
            </p>

            {result.reason && (
              <p className="mt-2 text-[11px] text-[#a09398] dark:text-[#786b71]">
                {result.reason}
              </p>
            )}
          </div>
        </div>
      </section>
    );
  }

  const evidenceCount =
    Object.values(
      report.evidence
    ).reduce(
      (total, items) =>
        total + items.length,
      0
    );

  return (
    <section className="rounded-xl border border-[#e7dfdc] bg-white p-5 shadow-soft-panel dark:border-white/[0.08] dark:bg-[#1c1219] dark:shadow-dark-panel">
      <div className="flex flex-col gap-4 border-b border-[#eee7e3] pb-4 dark:border-white/[0.07] lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#fff0e8] text-[#bd5834] dark:bg-[#ff895d]/[0.09] dark:text-[#ff9a72]">
            <Sparkles size={18} />
          </div>

          <div>
            <h2 className="text-sm font-semibold text-[#302529] dark:text-[#f8efec]">
              AI Evidence Analysis
            </h2>

            <p className="mt-0.5 text-[11px] text-[#988b90] dark:text-[#81737a]">
              Claim extraction, kaynak taraması ve RAG tabanlı kanıt analizi
            </p>
          </div>
        </div>

        <div className="text-right">
          <p className="text-xs font-semibold text-[#5d4c52] dark:text-[#d4c6cb]">
            {statusLabel(
              report.overall_evidence_status
            )}
          </p>

          <p className="mt-1 text-[10px] text-[#9b8e93] dark:text-[#786b71]">
            {report.provider} • {report.model}
          </p>
        </div>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-lg border border-[#ebe3df] bg-[#fbf9f8] p-4 dark:border-white/[0.06] dark:bg-[#160f15]">
          <p className="text-[10px] uppercase tracking-[0.12em] text-[#9d9095]">
            Evidence Status
          </p>

          <p className="mt-2 text-sm font-semibold text-[#3c3034] dark:text-[#eee3e6]">
            {statusLabel(
              report.overall_evidence_status
            )}
          </p>
        </div>

        <div className="rounded-lg border border-[#ebe3df] bg-[#fbf9f8] p-4 dark:border-white/[0.06] dark:bg-[#160f15]">
          <p className="text-[10px] uppercase tracking-[0.12em] text-[#9d9095]">
            Claims
          </p>

          <p className="mt-2 text-xl font-semibold text-[#3c3034] dark:text-[#eee3e6]">
            {report.claims.length}
          </p>
        </div>

        <div className="rounded-lg border border-[#ebe3df] bg-[#fbf9f8] p-4 dark:border-white/[0.06] dark:bg-[#160f15]">
          <p className="text-[10px] uppercase tracking-[0.12em] text-[#9d9095]">
            Evidence
          </p>

          <p className="mt-2 text-xl font-semibold text-[#3c3034] dark:text-[#eee3e6]">
            {evidenceCount}
          </p>
        </div>

        <div className="rounded-lg border border-[#ebe3df] bg-[#fbf9f8] p-4 dark:border-white/[0.06] dark:bg-[#160f15]">
          <p className="text-[10px] uppercase tracking-[0.12em] text-[#9d9095]">
            Manipülasyon Sinyali
          </p>

          <p className="mt-2 text-xl font-semibold text-[#3c3034] dark:text-[#eee3e6]">
            {
              report
                .manipulation_signals
                .length
            }
          </p>
        </div>
      </div>

      <div className="mt-5 space-y-3">
        {report.claims.map(
          (claim) => {
            const assessment =
              report.assessments.find(
                (item) =>
                  item.claim_id ===
                  claim.id
              );

            const evidence =
              report.evidence[
                claim.id
              ] ?? [];

            return (
              <article
                key={claim.id}
                className="rounded-xl border border-[#e9e1de] bg-[#fcfaf9] p-4 dark:border-white/[0.07] dark:bg-[#160f15]"
              >
                <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                  <div>
                    <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[#a09398]">
                      {claim.id}
                    </p>

                    <p className="mt-1 text-sm font-semibold leading-6 text-[#3a2e32] dark:text-[#eee4e7]">
                      {claim.text}
                    </p>
                  </div>

                  <span className="shrink-0 rounded-md border border-[#e5d8d2] bg-white px-2.5 py-1 text-[10px] font-semibold text-[#795d51] dark:border-white/[0.08] dark:bg-white/[0.03] dark:text-[#c9ada0]">
                    {stanceLabel(
                      assessment?.stance
                    )}
                  </span>
                </div>

                {assessment?.reasoning && (
                  <p className="mt-3 text-xs leading-5 text-[#786a70] dark:text-[#a4969c]">
                    {
                      assessment.reasoning
                    }
                  </p>
                )}

                {evidence.length > 0 && (
                  <div className="mt-4 grid gap-2 lg:grid-cols-2">
                    {evidence.map(
                      (item) => (
                        <a
                          key={item.id}
                          href={item.url}
                          target="_blank"
                          rel="noreferrer"
                          className="group flex items-start gap-3 rounded-lg border border-[#e9e1de] bg-white p-3 transition hover:border-[#d7b6a7] dark:border-white/[0.06] dark:bg-white/[0.025] dark:hover:border-[#ff895d]/20"
                        >
                          <FileSearch
                            size={15}
                            className="mt-0.5 shrink-0 text-[#b45d3d] dark:text-[#ff936c]"
                          />

                          <div className="min-w-0 flex-1">
                            <p className="truncate text-xs font-semibold text-[#514348] dark:text-[#d8cbd0]">
                              {item.title ||
                                item.source}
                            </p>

                            <p className="mt-1 text-[10px] text-[#9a8d92] dark:text-[#7d7076]">
                              {item.source} •{" "}
                              {
                                item.evidence_type
                              }
                            </p>

                            {item.rating && (
                              <p className="mt-1 text-[10px] font-medium text-[#7b5a4d] dark:text-[#cda996]">
                                Rating:{" "}
                                {
                                  item.rating
                                }
                              </p>
                            )}
                          </div>

                          <ExternalLink
                            size={13}
                            className="shrink-0 text-[#aaa0a3]"
                          />
                        </a>
                      )
                    )}
                  </div>
                )}
              </article>
            );
          }
        )}
      </div>

      {report.manipulation_signals.length >
        0 && (
        <div className="mt-5">
          <h3 className="text-xs font-semibold text-[#56484d] dark:text-[#cfc1c6]">
            Manipülasyon Sinyalleri
          </h3>

          <div className="mt-2 grid gap-2 lg:grid-cols-2">
            {report.manipulation_signals.map(
              (signal, index) => (
                <div
                  key={`${signal.signal_type}-${index}`}
                  className="rounded-lg border border-[#eadfdb] bg-[#fffaf7] p-3 dark:border-white/[0.06] dark:bg-[#1a1117]"
                >
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-xs font-semibold text-[#59474d] dark:text-[#d8c9ce]">
                      {
                        signal.signal_type
                      }
                    </p>

                    <span className="text-[10px] uppercase text-[#a4735f] dark:text-[#c99982]">
                      {signal.severity}
                    </span>
                  </div>

                  <p className="mt-2 text-[11px] leading-5 text-[#7e7075] dark:text-[#96888e]">
                    {
                      signal.explanation
                    }
                  </p>

                  {signal.excerpt && (
                    <p className="mt-2 border-l-2 border-[#d9b3a2] pl-2 text-[10px] italic text-[#9b8d92] dark:border-[#ff895d]/30 dark:text-[#786b71]">
                      “{signal.excerpt}”
                    </p>
                  )}
                </div>
              )
            )}
          </div>
        </div>
      )}

      <div className="mt-5 rounded-lg border border-[#e9e1de] bg-[#faf7f5] p-3 dark:border-white/[0.06] dark:bg-white/[0.02]">
        <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-[#9b8e93]">
          Yöntem
        </p>

        <p className="mt-1 text-xs text-[#706268] dark:text-[#95878d]">
          {report.retrieval_mode}
        </p>

        {report.limitations.map(
          (limitation) => (
            <p
              key={limitation}
              className="mt-1 text-[10px] leading-4 text-[#9a8d92] dark:text-[#786b71]"
            >
              • {limitation}
            </p>
          )
        )}
      </div>
    </section>
  );
}
