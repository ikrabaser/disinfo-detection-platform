import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import { getAnalysis, type Analysis } from "../api/client";
import PropagationGraph from "../components/PropagationGraph";

export default function AnalysisDetail() {
  const { analysisId } = useParams<{ analysisId: string }>();
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!analysisId) return;
    getAnalysis(analysisId)
      .then(setAnalysis)
      .catch(() => setError("Analiz backend'den yuklenemedi (mock modda goruntuleniyor)."));
  }, [analysisId]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-800">Analiz Detayi #{analysisId}</h1>
        {error && <p className="mt-1 text-xs text-amber-600">{error}</p>}
      </div>

      {analysis && (
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-sm text-slate-700">{analysis.claim_text}</p>
          <div className="mt-3 grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
            <div>
              <p className="text-slate-400">Durum</p>
              <p className="font-medium">{analysis.status}</p>
            </div>
            <div>
              <p className="text-slate-400">Dogruluk Skoru</p>
              <p className="font-medium">
                {analysis.truth_score !== null ? `${(analysis.truth_score * 100).toFixed(0)}%` : "-"}
              </p>
            </div>
          </div>
        </div>
      )}

      <PropagationGraph />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <h3 className="text-sm font-medium text-slate-600">NLP Sonucu</h3>
          <pre className="mt-2 overflow-auto text-xs text-slate-500">
            {JSON.stringify(analysis?.nlp_result ?? { mock: true }, null, 2)}
          </pre>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <h3 className="text-sm font-medium text-slate-600">GNN Sonucu</h3>
          <pre className="mt-2 overflow-auto text-xs text-slate-500">
            {JSON.stringify(analysis?.gnn_result ?? { mock: true }, null, 2)}
          </pre>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <h3 className="text-sm font-medium text-slate-600">Bot Analizi</h3>
          <pre className="mt-2 overflow-auto text-xs text-slate-500">
            {JSON.stringify(analysis?.bot_analysis_result ?? { mock: true }, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  );
}
