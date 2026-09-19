import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { listAnalyses, type Analysis } from "../api/client";
import ScoreTrendChart from "../components/ScoreTrendChart";

const MOCK_ANALYSES: Analysis[] = [
  {
    id: 1,
    claim_text: "Deprem sonrasi yardim kampanyasi hesabinin sahte oldugu iddiasi",
    source_url: null,
    query: "deprem yardim kampanyasi",
    status: "completed",
    nlp_result: null,
    gnn_result: null,
    bot_analysis_result: null,
    source_verification_result: null,
    truth_score: 0.34,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 2,
    claim_text: "Yeni asi karsiti icerigin organize botlar tarafindan yayildigi iddiasi",
    source_url: null,
    query: "asi karsiti",
    status: "running",
    nlp_result: null,
    gnn_result: null,
    bot_analysis_result: null,
    source_verification_result: null,
    truth_score: null,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

function StatusBadge({ status }: { status: Analysis["status"] }) {
  const colors: Record<Analysis["status"], string> = {
    pending: "bg-slate-100 text-slate-600",
    running: "bg-amber-100 text-amber-700",
    completed: "bg-emerald-100 text-emerald-700",
    failed: "bg-red-100 text-red-700",
  };
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${colors[status]}`}>
      {status}
    </span>
  );
}

export default function Dashboard() {
  const [analyses, setAnalyses] = useState<Analysis[]>(MOCK_ANALYSES);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    listAnalyses()
      .then((data) => {
        if (!cancelled && data.length > 0) {
          setAnalyses(data);
        }
      })
      .catch(() => {
        // Backend henuz calismiyor olabilir - mock veriyle devam et.
        if (!cancelled) {
          setError("Backend'e ulasilamadi, mock veriler gosteriliyor.");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-800">Analiz Paneli</h1>
        <p className="mt-1 text-sm text-slate-500">
          Sosyal medyada dezenformasyon ve sahte haber tespiti - gercek zamanli genel bakis.
        </p>
        {error && <p className="mt-2 text-xs text-amber-600">{error}</p>}
      </div>

      <ScoreTrendChart />

      <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-200 px-4 py-3">
          <h2 className="text-sm font-medium text-slate-600">
            Son Analizler {loading && "(yukleniyor...)"}
          </h2>
        </div>
        <ul className="divide-y divide-slate-100">
          {analyses.map((analysis) => (
            <li key={analysis.id} className="px-4 py-3 hover:bg-slate-50">
              <Link to={`/analyses/${analysis.id}`} className="flex items-center justify-between gap-4">
                <div>
                  <p className="text-sm font-medium text-slate-800">{analysis.claim_text}</p>
                  <p className="text-xs text-slate-400">{analysis.query}</p>
                </div>
                <div className="flex items-center gap-3">
                  {analysis.truth_score !== null && (
                    <span className="text-sm font-semibold text-brand-600">
                      {(analysis.truth_score * 100).toFixed(0)}%
                    </span>
                  )}
                  <StatusBadge status={analysis.status} />
                </div>
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
