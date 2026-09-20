import {
  BarChart3,
  Bell,
  FileText,
  Home,
  Search,
  Settings,
  ShieldCheck,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { Link, useLocation } from "react-router-dom";

interface NavItem {
  label: string;
  to: string;
  icon: LucideIcon;
  badge?: number;
  enabled?: boolean;
}

const NAV_ITEMS: NavItem[] = [
  { label: "Genel Bakış", to: "/", icon: Home, enabled: true },
  { label: "İçerik Analizi", to: "/icerik-analizi", icon: Search },
  { label: "Kaynaklar", to: "/kaynaklar", icon: FileText },
  { label: "Yayılım Analizi", to: "/yayilim", icon: BarChart3 },
  { label: "Raporlar", to: "/raporlar", icon: FileText },
  { label: "Uyarılar", to: "/uyarilar", icon: Bell, badge: 3 },
  { label: "Ayarlar", to: "/ayarlar", icon: Settings },
];

function NavRow({
  item,
  active,
}: {
  item: NavItem;
  active: boolean;
}) {
  const Icon = item.icon;

  const classes = active
    ? "bg-slate-900 text-white"
    : "text-slate-600 hover:bg-slate-100 hover:text-slate-950";

  const content = (
    <span
      className={`flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition ${classes}`}
    >
      <Icon size={17} strokeWidth={1.8} />

      <span className="flex-1">{item.label}</span>

      {item.badge !== undefined && (
        <span
          className={`flex h-5 min-w-5 items-center justify-center rounded px-1.5 text-[10px] font-semibold ${
            active ? "bg-white/15 text-white" : "bg-red-50 text-red-600"
          }`}
        >
          {item.badge}
        </span>
      )}
    </span>
  );

  if (!item.enabled) {
    return (
      <div className="cursor-default opacity-45" title="Yakında">
        {content}
      </div>
    );
  }

  return <Link to={item.to}>{content}</Link>;
}

export default function Sidebar() {
  const location = useLocation();

  return (
    <aside className="hidden w-64 shrink-0 flex-col border-r border-slate-200 bg-white md:flex">
      <div className="flex h-16 items-center border-b border-slate-100 px-5">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-slate-950 text-white">
            <ShieldCheck size={18} strokeWidth={1.8} />
          </div>

          <div>
            <p className="text-sm font-semibold tracking-tight text-slate-950">
              VERITAS
            </p>
            <p className="text-[10px] uppercase tracking-[0.12em] text-slate-400">
              Analysis Platform
            </p>
          </div>
        </div>
      </div>

      <div className="px-3 py-5">
        <p className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-400">
          Çalışma Alanı
        </p>

        <nav className="flex flex-col gap-1">
          {NAV_ITEMS.map((item) => (
            <NavRow
              key={item.label}
              item={item}
              active={location.pathname === item.to}
            />
          ))}
        </nav>
      </div>

      <div className="mt-auto border-t border-slate-100 px-5 py-4">
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-emerald-500" />
          <span className="text-xs font-medium text-slate-600">
            Sistem operasyonel
          </span>
        </div>

        <p className="mt-1 pl-4 text-[11px] text-slate-400">
          İzleme servisleri aktif
        </p>
      </div>
    </aside>
  );
}
