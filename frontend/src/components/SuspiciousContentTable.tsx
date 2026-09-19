import { Globe, MoreVertical } from "lucide-react";
import type { ComponentType } from "react";
import { FaFacebook, FaXTwitter, FaYoutube } from "react-icons/fa6";
import type { IconType } from "react-icons";

type RiskLevel = "Yuksek" | "Orta" | "Dusuk";
type ContentStatus = "Inceleniyor" | "Dogrulandi" | "Yanlis";
type Channel = "Web" | "X (Twitter)" | "YouTube" | "Facebook";

interface SuspiciousContentRow {
  title: string;
  source: string;
  sourceColor: string;
  channel: Channel;
  risk: RiskLevel;
  status: ContentStatus;
  timestamp: string;
}

const MOCK_ROWS: SuspiciousContentRow[] = [
  {
    title: "Ekonomi paketine iliskin yaniltici iddialar...",
    source: "Haber365",
    sourceColor: "bg-rose-500",
    channel: "Web",
    risk: "Yuksek",
    status: "Inceleniyor",
    timestamp: "30 Kas 2024 14:32",
  },
  {
    title: "Istanbul'da su kaynaklariyla ilgili dogrulanm...",
    source: "GundemPost",
    sourceColor: "bg-emerald-500",
    channel: "X (Twitter)",
    risk: "Yuksek",
    status: "Dogrulandi",
    timestamp: "30 Kas 2024 11:18",
  },
  {
    title: "Unlu isimle ilgili asilsiz saglik iddiasi...",
    source: "Vizyon Haber",
    sourceColor: "bg-violet-500",
    channel: "YouTube",
    risk: "Orta",
    status: "Inceleniyor",
    timestamp: "30 Kas 2024 09:41",
  },
  {
    title: "Avrupa ulkelerinde enerji krizi iddialari...",
    source: "Dunya Gundemi",
    sourceColor: "bg-sky-500",
    channel: "Web",
    risk: "Orta",
    status: "Yanlis",
    timestamp: "29 Kas 2024 22:17",
  },
  {
    title: "Yeni bir salgin hastalik kapida mi?",
    source: "Saglik Ajansi",
    sourceColor: "bg-amber-500",
    channel: "Facebook",
    risk: "Dusuk",
    status: "Dogrulandi",
    timestamp: "29 Kas 2024 18:03",
  },
];

const RISK_STYLES: Record<RiskLevel, string> = {
  Yuksek: "bg-red-50 text-red-600",
  Orta: "bg-amber-50 text-amber-600",
  Dusuk: "bg-slate-100 text-slate-500",
};

const STATUS_STYLES: Record<ContentStatus, string> = {
  Inceleniyor: "bg-amber-50 text-amber-600",
  Dogrulandi: "bg-emerald-50 text-emerald-600",
  Yanlis: "bg-red-50 text-red-600",
};

const CHANNEL_ICONS: Record<Channel, { Icon: ComponentType<{ size?: number; className?: string }> | IconType; className: string }> = {
  Web: { Icon: Globe, className: "text-slate-500" },
  "X (Twitter)": { Icon: FaXTwitter, className: "text-slate-900" },
  YouTube: { Icon: FaYoutube, className: "text-red-600" },
  Facebook: { Icon: FaFacebook, className: "text-blue-600" },
};

function SourceBadge({ name, color }: { name: string; color: string }) {
  const initial = name.trim().charAt(0).toUpperCase();
  return (
    <span className="flex items-center gap-2">
      <span
        className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[10px] font-semibold text-white ${color}`}
      >
        {initial}
      </span>
      {name}
    </span>
  );
}

const CHANNEL_LABELS: Record<Channel, string> = {
  Web: "Web",
  "X (Twitter)": "X",
  YouTube: "YouTube",
  Facebook: "Facebook",
};

function ChannelBadge({ channel }: { channel: Channel }) {
  const { Icon, className } = CHANNEL_ICONS[channel];
  return (
    <span className="flex items-center gap-1.5 whitespace-nowrap">
      <Icon size={14} className={`shrink-0 ${className}`} />
      {CHANNEL_LABELS[channel]}
    </span>
  );
}

export default function SuspiciousContentTable() {
  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3">
        <h3 className="text-sm font-semibold text-slate-700">Son Tespit Edilen Supheli Icerikler</h3>
        <a href="#" className="text-xs font-medium text-brand-600 hover:underline">
          Tumunu Gor
        </a>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="text-slate-400">
              <th className="px-4 py-2 font-medium">Baslik</th>
              <th className="px-4 py-2 font-medium">Kaynak</th>
              <th className="px-4 py-2 font-medium">Kanal</th>
              <th className="px-4 py-2 font-medium">Risk Seviyesi</th>
              <th className="px-4 py-2 font-medium">Durum</th>
              <th className="px-4 py-2 font-medium">Tarih / Saat</th>
              <th className="px-4 py-2" />
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {MOCK_ROWS.map((row) => (
              <tr key={row.title} className="hover:bg-slate-50">
                <td className="max-w-[220px] truncate px-4 py-3 font-medium text-slate-700">
                  {row.title}
                </td>
                <td className="px-4 py-3 text-slate-500">
                  <SourceBadge name={row.source} color={row.sourceColor} />
                </td>
                <td className="px-4 py-3 text-slate-500">
                  <ChannelBadge channel={row.channel} />
                </td>
                <td className="px-4 py-3">
                  <span className={`rounded-full px-2 py-0.5 font-medium ${RISK_STYLES[row.risk]}`}>
                    {row.risk}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className={`rounded-full px-2 py-0.5 font-medium ${STATUS_STYLES[row.status]}`}>
                    {row.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-400">{row.timestamp}</td>
                <td className="px-4 py-3 text-slate-400">
                  <MoreVertical size={14} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
