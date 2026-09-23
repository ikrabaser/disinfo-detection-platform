import {
  Globe,
  MoreHorizontal,
} from "lucide-react";

import type {
  ComponentType,
} from "react";

import {
  FaFacebook,
  FaXTwitter,
  FaYoutube,
} from "react-icons/fa6";

import type {
  IconType,
} from "react-icons";


type RiskLevel =
  | "Yuksek"
  | "Orta"
  | "Dusuk";

type ContentStatus =
  | "Inceleniyor"
  | "Dogrulandi"
  | "Yanlis";

type Channel =
  | "Web"
  | "X (Twitter)"
  | "YouTube"
  | "Facebook";


interface SuspiciousContentRow {
  title: string;
  source: string;
  sourceColor: string;
  channel: Channel;
  risk: RiskLevel;
  status: ContentStatus;
  timestamp: string;
}


const MOCK_ROWS:
  SuspiciousContentRow[] = [
    {
      title:
        "Ekonomi paketine ilişkin yanıltıcı iddialar...",
      source: "Haber365",
      sourceColor:
        "bg-rose-500",
      channel: "Web",
      risk: "Yuksek",
      status: "Inceleniyor",
      timestamp:
        "30 Kas 2024 14:32",
    },
    {
      title:
        "İstanbul'da su kaynaklarıyla ilgili doğrulanmamış paylaşım...",
      source: "GündemPost",
      sourceColor:
        "bg-emerald-500",
      channel:
        "X (Twitter)",
      risk: "Yuksek",
      status: "Dogrulandi",
      timestamp:
        "30 Kas 2024 11:18",
    },
    {
      title:
        "Ünlü isimle ilgili asılsız sağlık iddiası...",
      source: "Vizyon Haber",
      sourceColor:
        "bg-violet-500",
      channel: "YouTube",
      risk: "Orta",
      status: "Inceleniyor",
      timestamp:
        "30 Kas 2024 09:41",
    },
    {
      title:
        "Avrupa ülkelerinde enerji krizi iddiaları...",
      source: "Dünya Gündemi",
      sourceColor:
        "bg-sky-500",
      channel: "Web",
      risk: "Orta",
      status: "Yanlis",
      timestamp:
        "29 Kas 2024 22:17",
    },
    {
      title:
        "Yeni bir salgın hastalık kapıda mı?",
      source: "Sağlık Ajansı",
      sourceColor:
        "bg-amber-500",
      channel: "Facebook",
      risk: "Dusuk",
      status: "Dogrulandi",
      timestamp:
        "29 Kas 2024 18:03",
    },
  ];


const RISK_STYLES:
  Record<RiskLevel, string> = {
    Yuksek:
      "border-red-200 bg-red-50 text-red-600 dark:border-red-400/10 dark:bg-red-400/[0.07] dark:text-red-300",

    Orta:
      "border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-400/10 dark:bg-amber-400/[0.07] dark:text-amber-300",

    Dusuk:
      "border-[#e5dedb] bg-[#f5f1ef] text-[#75686d] dark:border-white/[0.07] dark:bg-white/[0.04] dark:text-[#a99ba1]",
  };


const STATUS_STYLES:
  Record<
    ContentStatus,
    string
  > = {
    Inceleniyor:
      "bg-[#fff3e8] text-[#b86a24] dark:bg-[#ff9d4d]/[0.08] dark:text-[#f3ad68]",

    Dogrulandi:
      "bg-emerald-50 text-emerald-700 dark:bg-emerald-400/[0.07] dark:text-emerald-300",

    Yanlis:
      "bg-red-50 text-red-600 dark:bg-red-400/[0.07] dark:text-red-300",
  };


const CHANNEL_ICONS:
  Record<
    Channel,
    {
      Icon:
        | ComponentType<{
            size?: number;
            className?: string;
          }>
        | IconType;

      className: string;
    }
  > = {
    Web: {
      Icon: Globe,
      className:
        "text-[#8c7f84] dark:text-[#9c8f95]",
    },

    "X (Twitter)": {
      Icon: FaXTwitter,
      className:
        "text-[#40353a] dark:text-[#d8ccd0]",
    },

    YouTube: {
      Icon: FaYoutube,
      className:
        "text-red-500 dark:text-red-400",
    },

    Facebook: {
      Icon: FaFacebook,
      className:
        "text-blue-600 dark:text-blue-400",
    },
  };


const CHANNEL_LABELS:
  Record<Channel, string> = {
    Web: "Web",
    "X (Twitter)": "X",
    YouTube: "YouTube",
    Facebook: "Facebook",
  };


function SourceBadge({
  name,
  color,
}: {
  name: string;
  color: string;
}) {
  const initial =
    name
      .trim()
      .charAt(0)
      .toUpperCase();

  return (
    <span className="flex items-center gap-2">
      <span
        className={[
          "flex h-6 w-6 shrink-0 items-center justify-center rounded-full",
          "text-[9px] font-semibold text-white",
          color,
        ].join(" ")}
      >
        {initial}
      </span>

      <span className="truncate">
        {name}
      </span>
    </span>
  );
}


function ChannelBadge({
  channel,
}: {
  channel: Channel;
}) {
  const {
    Icon,
    className,
  } =
    CHANNEL_ICONS[
      channel
    ];

  return (
    <span className="flex items-center gap-1.5 whitespace-nowrap">
      <Icon
        size={13}
        className={className}
      />

      {
        CHANNEL_LABELS[
          channel
        ]
      }
    </span>
  );
}


export default function SuspiciousContentTable() {
  return (
    <section className="overflow-hidden rounded-xl border border-[#e7dfdc] bg-white shadow-soft-panel dark:border-white/[0.08] dark:bg-[#1c1219] dark:shadow-dark-panel">
      <div className="flex items-start justify-between border-b border-[#eee7e3] px-5 py-4 dark:border-white/[0.07]">
        <div>
          <h3 className="text-sm font-semibold text-[#302529] dark:text-[#f8efec]">
            Son Tespit Edilen Şüpheli İçerikler
          </h3>

          <p className="mt-0.5 text-[11px] text-[#988b90] dark:text-[#7e7077]">
            İnceleme kuyruğundaki son örnek içerikler
          </p>
        </div>

        <div className="flex items-center gap-3">
          <span className="rounded-md border border-[#e9e1dd] bg-[#faf7f5] px-2 py-1 text-[9px] font-semibold uppercase tracking-[0.08em] text-[#9b8e92] dark:border-white/[0.07] dark:bg-white/[0.035] dark:text-[#786b71]">
            Demo veri
          </span>

          <button
            type="button"
            className="text-[10px] font-semibold text-[#bd5a34] transition hover:text-[#8f4025] dark:text-[#ff9269] dark:hover:text-[#ffac8c]"
          >
            Tümünü Gör
          </button>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[980px] text-left text-[11px]">
          <thead>
            <tr className="border-b border-[#eee7e3] bg-[#fbf9f8] text-[#9a8d92] dark:border-white/[0.06] dark:bg-white/[0.018] dark:text-[#786b71]">
              <th className="px-5 py-3 font-medium">
                Başlık
              </th>

              <th className="px-4 py-3 font-medium">
                Kaynak
              </th>

              <th className="px-4 py-3 font-medium">
                Kanal
              </th>

              <th className="px-4 py-3 font-medium">
                Risk Seviyesi
              </th>

              <th className="px-4 py-3 font-medium">
                Durum
              </th>

              <th className="px-4 py-3 font-medium">
                Tarih / Saat
              </th>

              <th className="w-12 px-3 py-3" />
            </tr>
          </thead>

          <tbody className="divide-y divide-[#eee7e3] dark:divide-white/[0.055]">
            {MOCK_ROWS.map(
              (row) => (
                <tr
                  key={
                    row.title
                  }
                  className="transition hover:bg-[#faf7f5] dark:hover:bg-white/[0.025]"
                >
                  <td className="max-w-[300px] truncate px-5 py-3.5 font-medium text-[#514348] dark:text-[#d3c5ca]">
                    {
                      row.title
                    }
                  </td>

                  <td className="px-4 py-3.5 text-[#786b70] dark:text-[#9b8e93]">
                    <SourceBadge
                      name={
                        row.source
                      }
                      color={
                        row.sourceColor
                      }
                    />
                  </td>

                  <td className="px-4 py-3.5 text-[#786b70] dark:text-[#9b8e93]">
                    <ChannelBadge
                      channel={
                        row.channel
                      }
                    />
                  </td>

                  <td className="px-4 py-3.5">
                    <span
                      className={[
                        "inline-flex rounded-full border px-2 py-1 text-[9px] font-semibold",
                        RISK_STYLES[
                          row.risk
                        ],
                      ].join(" ")}
                    >
                      {
                        row.risk ===
                        "Yuksek"
                          ? "Yüksek"
                          : row.risk ===
                              "Dusuk"
                            ? "Düşük"
                            : "Orta"
                      }
                    </span>
                  </td>

                  <td className="px-4 py-3.5">
                    <span
                      className={[
                        "inline-flex rounded-md px-2 py-1 text-[9px] font-semibold",
                        STATUS_STYLES[
                          row.status
                        ],
                      ].join(" ")}
                    >
                      {
                        row.status ===
                        "Inceleniyor"
                          ? "İnceleniyor"
                          : row.status ===
                              "Dogrulandi"
                            ? "Doğrulandı"
                            : "Yanlış"
                      }
                    </span>
                  </td>

                  <td className="whitespace-nowrap px-4 py-3.5 text-[#9b8e92] dark:text-[#786b71]">
                    {
                      row.timestamp
                    }
                  </td>

                  <td className="px-3 py-3.5">
                    <button
                      type="button"
                      aria-label="İşlemler"
                      className="flex h-7 w-7 items-center justify-center rounded-md text-[#a4979b] transition hover:bg-[#f3eeeb] hover:text-[#514348] dark:text-[#71646a] dark:hover:bg-white/[0.05] dark:hover:text-[#cfc1c6]"
                    >
                      <MoreHorizontal
                        size={15}
                      />
                    </button>
                  </td>
                </tr>
              )
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
