import {
  BarChart3,
  Bell,
  FileText,
  Home,
  Search,
  Settings,
  ShieldCheck,
} from "lucide-react";
import type {
  LucideIcon,
} from "lucide-react";
import {
  Link,
  useLocation,
} from "react-router-dom";


interface NavItem {
  label: string;
  to: string;
  icon: LucideIcon;
  badge?: number;
  enabled?: boolean;
}


const NAV_ITEMS: NavItem[] = [
  {
    label: "Genel Bakış",
    to: "/",
    icon: Home,
    enabled: true,
  },
  {
    label: "İçerik Analizi",
    to: "/icerik-analizi",
    icon: Search,
  },
  {
    label: "Kaynaklar",
    to: "/kaynaklar",
    icon: FileText,
  },
  {
    label: "Yayılım Analizi",
    to: "/yayilim",
    icon: BarChart3,
  },
  {
    label: "Raporlar",
    to: "/raporlar",
    icon: FileText,
  },
  {
    label: "Uyarılar",
    to: "/uyarilar",
    icon: Bell,
    badge: 3,
  },
  {
    label: "Ayarlar",
    to: "/ayarlar",
    icon: Settings,
  },
];


function NavRow({
  item,
  active,
}: {
  item: NavItem;
  active: boolean;
}) {
  const Icon = item.icon;

  const content = (
    <span
      className={[
        "group relative flex items-center gap-3 rounded-lg px-3 py-2.5",
        "text-[13px] font-medium transition",
        active
          ? "bg-[#fff0e7] text-[#9f4529] dark:bg-[#ff895d]/[0.11] dark:text-[#ff9a72]"
          : "text-[#75686d] hover:bg-[#f6f1ee] hover:text-[#2c2326] dark:text-[#aa9ba1] dark:hover:bg-white/[0.055] dark:hover:text-[#fff6f2]",
      ].join(" ")}
    >
      {active && (
        <span className="absolute inset-y-2 left-0 w-[2px] rounded-full bg-[#c86038] dark:bg-[#ff895d]" />
      )}

      <Icon
        size={17}
        strokeWidth={1.8}
        className={
          active
            ? "text-[#c86038] dark:text-[#ff895d]"
            : "text-[#97898e] group-hover:text-[#55474c] dark:text-[#82747b] dark:group-hover:text-[#cbbdc2]"
        }
      />

      <span className="flex-1">
        {item.label}
      </span>

      {item.badge !== undefined && (
        <span className="flex h-5 min-w-5 items-center justify-center rounded-md bg-[#fff0f1] px-1.5 text-[10px] font-semibold text-[#d84c5d] dark:bg-[#fb6674]/[0.12] dark:text-[#ff7b86]">
          {item.badge}
        </span>
      )}
    </span>
  );

  if (!item.enabled) {
    return (
      <div
        className="cursor-default opacity-45"
        title="Yakında"
      >
        {content}
      </div>
    );
  }

  return (
    <Link to={item.to}>
      {content}
    </Link>
  );
}


export default function Sidebar() {
  const location = useLocation();

  const isDashboard =
    location.pathname === "/";

  return (
    <aside className="hidden w-[238px] shrink-0 flex-col border-r border-[#e8e1de] bg-[#fdfcfa] md:flex dark:border-white/[0.07] dark:bg-[#160e14]">
      <div className="flex h-[68px] items-center border-b border-[#eee7e3] px-5 dark:border-white/[0.06]">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-[#f0cbb8] bg-[#fff0e6] text-[#b6512e] dark:border-[#ff895d]/20 dark:bg-[#ff895d]/[0.10] dark:text-[#ff9a70]">
            <ShieldCheck
              size={19}
              strokeWidth={1.9}
            />
          </div>

          <div>
            <p className="text-sm font-bold tracking-[0.04em] text-[#251c20] dark:text-[#fff7f4]">
              VERITAS
            </p>

            <p className="mt-0.5 text-[9px] font-medium uppercase tracking-[0.16em] text-[#9e9196] dark:text-[#796c72]">
              Analysis Platform
            </p>
          </div>
        </div>
      </div>

      <div className="px-3 py-5">
        <p className="mb-2.5 px-3 text-[10px] font-semibold uppercase tracking-[0.16em] text-[#aaa0a3] dark:text-[#665a60]">
          Çalışma Alanı
        </p>

        <nav className="flex flex-col gap-1">
          {NAV_ITEMS.map((item) => (
            <NavRow
              key={item.label}
              item={item}
              active={
                item.to === "/"
                  ? isDashboard
                  : location.pathname.startsWith(
                      item.to
                    )
              }
            />
          ))}
        </nav>
      </div>

      <div className="mt-auto p-3">
        <div className="rounded-xl border border-[#e8e1de] bg-white px-4 py-3.5 shadow-[0_10px_30px_rgba(52,38,44,0.04)] dark:border-white/[0.07] dark:bg-white/[0.025] dark:shadow-none">
          <div className="flex items-center gap-2">
            <span className="relative flex h-2.5 w-2.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-20" />
              <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-emerald-500" />
            </span>

            <span className="text-xs font-semibold text-[#4f4247] dark:text-[#d6c9ce]">
              Sistem operasyonel
            </span>
          </div>

          <p className="mt-1 pl-[18px] text-[10px] text-[#a09498] dark:text-[#706269]">
            İzleme servisleri aktif
          </p>
        </div>
      </div>
    </aside>
  );
}
