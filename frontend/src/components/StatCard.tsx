import { TrendingDown, TrendingUp, type LucideIcon } from "lucide-react";

interface StatCardProps {
  icon: LucideIcon;
  iconClassName?: string;
  label: string;
  value: string;
  deltaPct: number;
  deltaLabel?: string;
}

export default function StatCard({
  icon: Icon,
  iconClassName = "bg-brand-50 text-brand-600",
  label,
  value,
  deltaPct,
  deltaLabel = "Onceki doneme gore",
}: StatCardProps) {
  const isPositive = deltaPct >= 0;
  const DeltaIcon = isPositive ? TrendingUp : TrendingDown;
  const deltaColor = isPositive ? "text-emerald-600" : "text-red-600";

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <div className={`flex h-9 w-9 items-center justify-center rounded-lg ${iconClassName}`}>
          <Icon size={18} />
        </div>
      </div>
      <p className="text-xs text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-slate-800">{value}</p>
      <div className={`mt-2 flex items-center gap-1 text-xs font-medium ${deltaColor}`}>
        <DeltaIcon size={14} />
        <span>
          %{Math.abs(deltaPct)} {deltaLabel}
        </span>
      </div>
    </div>
  );
}
