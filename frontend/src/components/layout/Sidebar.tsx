import {
  AlertTriangle,
  BarChart3,
  Bell,
  FileText,
  Home,
  Search,
  Settings,
  ShieldCheck,
  TrendingUp,
  type LucideIcon,
} from "lucide-react";
import { Link, useLocation } from "react-router-dom";

interface NavItem {
  label: string;
  to: string;
  icon: LucideIcon;
  badge?: number;
  enabled?: boolean;
}

const NAV_ITEMS: NavItem[] = [
  { label: "Ana Sayfa", to: "/", icon: Home, enabled: true },
  { label: "Icerik Analizi", to: "/icerik-analizi", icon: Search },
  { label: "Kaynaklar", to: "/kaynaklar", icon: FileText },
  { label: "Gundem & Narratifler", to: "/gundem", icon: BarChart3 },
  { label: "Raporlar", to: "/raporlar", icon: FileText },
  { label: "Uyarilar", to: "/uyarilar", icon: Bell, badge: 3 },
  { label: "Ayarlar", to: "/ayarlar", icon: Settings },
];

function NavRow({ item, active }: { item: NavItem; active: boolean }) {
  const Icon = item.icon;
  const classes = active
    ? "bg-brand-50 text-brand-700"
    : "text-slate-500 hover:bg-slate-50 hover:text-slate-700";

  const content = (
    <span className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium ${classes}`}>
      <Icon size={18} />
      <span className="flex-1">{item.label}</span>
      {item.badge !== undefined && (
        <span className="flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-[11px] font-semibold text-white">
          {item.badge}
        </span>
      )}
    </span>
  );

  if (!item.enabled) {
    return (
      <div className="cursor-default opacity-60" title="Yakinda">
        {content}
      </div>
    );
  }

  return <Link to={item.to}>{content}</Link>;
}

export default function Sidebar() {
  const location = useLocation();

  return (
    <aside className="hidden w-64 shrink-0 flex-col border-r border-slate-200 bg-white px-4 py-5 md:flex">
      <div className="mb-8 flex items-center gap-2 px-2">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-600 text-white">
          <ShieldCheck size={20} />
        </div>
        <div>
          <p className="text-sm font-bold leading-tight text-slate-800">VERITAS</p>
          <p className="text-[11px] leading-tight text-slate-400">Gercege Daha Yakin</p>
        </div>
      </div>

      <nav className="flex flex-1 flex-col gap-1">
        {NAV_ITEMS.map((item) => (
          <NavRow key={item.label} item={item} active={location.pathname === item.to} />
        ))}
      </nav>

      <div className="mt-6 rounded-xl bg-slate-50 p-4">
        <div className="mb-2 flex items-center gap-1 text-brand-500">
          <TrendingUp size={16} />
          <AlertTriangle size={16} />
        </div>
        <p className="text-xs italic leading-relaxed text-slate-500">
          "Daha saglikli bir kamuoyu icin, kanita dayali icgoruler."
        </p>
      </div>
    </aside>
  );
}
