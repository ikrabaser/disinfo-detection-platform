import {
  TrendingDown,
  TrendingUp,
  type LucideIcon,
} from "lucide-react";


interface StatCardProps {
  icon: LucideIcon;
  label: string;
  value: string;
  deltaPct?: number;
  deltaLabel?: string;
  tone?:
    | "orange"
    | "red"
    | "green"
    | "neutral";
  badge?: string;
}


export default function StatCard({
  icon: Icon,
  label,
  value,
  deltaPct,
  deltaLabel = "önceki döneme göre",
  tone = "neutral",
  badge,
}: StatCardProps) {
  const toneClasses = {
    orange:
      "bg-[#fff1e9] text-[#bc572f] dark:bg-[#ff895d]/[0.08] dark:text-[#ff986f]",
    red:
      "bg-[#fff0f2] text-[#c74656] dark:bg-[#fb6674]/[0.08] dark:text-[#ff8290]",
    green:
      "bg-[#edf8f1] text-[#2e8e54] dark:bg-emerald-400/[0.07] dark:text-emerald-300",
    neutral:
      "bg-[#f3efed] text-[#68575d] dark:bg-white/[0.055] dark:text-[#b5a6ac]",
  };

  const hasDelta =
    typeof deltaPct === "number";

  const positive =
    (deltaPct ?? 0) >= 0;

  const DeltaIcon =
    positive
      ? TrendingUp
      : TrendingDown;

  return (
    <div className="rounded-xl border border-[#e7dfdc] bg-white p-4 shadow-soft-panel dark:border-white/[0.08] dark:bg-[#1c1219] dark:shadow-dark-panel">
      <div className="flex items-start justify-between">
        <div
          className={[
            "flex h-9 w-9 items-center justify-center rounded-lg",
            toneClasses[tone],
          ].join(" ")}
        >
          <Icon
            size={17}
            strokeWidth={1.8}
          />
        </div>

        {badge && (
          <span className="rounded-md border border-[#e9e1dd] bg-[#faf7f5] px-2 py-1 text-[9px] font-semibold uppercase tracking-[0.08em] text-[#9b8e92] dark:border-white/[0.07] dark:bg-white/[0.035] dark:text-[#786b71]">
            {badge}
          </span>
        )}
      </div>

      <p className="mt-4 text-[11px] font-medium text-[#8e8186] dark:text-[#8d7f85]">
        {label}
      </p>

      <p className="mt-1 text-[25px] font-semibold tracking-tight text-[#2b2024] dark:text-[#fff7f4]">
        {value}
      </p>

      {hasDelta && (
        <div
          className={[
            "mt-2 flex items-center gap-1 text-[10px] font-medium",
            positive
              ? "text-emerald-600 dark:text-emerald-300"
              : "text-red-600 dark:text-red-300",
          ].join(" ")}
        >
          <DeltaIcon size={12} />

          <span>
            %{Math.abs(
              deltaPct ?? 0
            )}{" "}
            {deltaLabel}
          </span>
        </div>
      )}
    </div>
  );
}
