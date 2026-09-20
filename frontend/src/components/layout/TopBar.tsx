import { Bell, ChevronDown, Search } from "lucide-react";

interface TopBarProps {
  userName?: string;
  userRole?: string;
  notificationCount?: number;
}

export default function TopBar({
  userName = "Deniz Karaca",
  userRole = "Analist",
  notificationCount = 3,
}: TopBarProps) {
  const initials = userName
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-slate-200 bg-white px-6">
      <div className="flex w-full max-w-md items-center gap-2 rounded-md border border-slate-200 bg-slate-50 px-3 py-2 transition focus-within:border-slate-300 focus-within:bg-white">
        <Search size={16} className="text-slate-400" />

        <input
          type="text"
          placeholder="İçerik, kaynak veya analiz ara..."
          className="w-full bg-transparent text-sm text-slate-700 placeholder:text-slate-400 focus:outline-none"
        />
      </div>

      <div className="flex items-center gap-3">
        <button
          type="button"
          aria-label="Bildirimler"
          className="relative rounded-md p-2 text-slate-500 transition hover:bg-slate-100 hover:text-slate-900"
        >
          <Bell size={18} />

          {notificationCount > 0 && (
            <span className="absolute right-1 top-1 h-2 w-2 rounded-full bg-red-500 ring-2 ring-white" />
          )}
        </button>

        <div className="mx-1 h-7 w-px bg-slate-200" />

        <button
          type="button"
          className="flex items-center gap-3 rounded-md px-2 py-1.5 transition hover:bg-slate-50"
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-200 text-xs font-semibold text-slate-700">
            {initials}
          </div>

          <div className="hidden text-left sm:block">
            <p className="text-sm font-medium leading-tight text-slate-800">
              {userName}
            </p>
            <p className="mt-0.5 text-xs leading-tight text-slate-400">
              {userRole}
            </p>
          </div>

          <ChevronDown size={15} className="text-slate-400" />
        </button>
      </div>
    </header>
  );
}
