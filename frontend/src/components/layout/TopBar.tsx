import { Bell, Calendar, Search } from "lucide-react";

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
    <header className="flex items-center justify-between gap-4 border-b border-slate-200 bg-white px-6 py-3">
      <div className="flex max-w-md flex-1 items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
        <Search size={16} className="text-slate-400" />
        <input
          type="text"
          placeholder="Icerik, kaynak veya konu ara..."
          className="w-full bg-transparent text-sm text-slate-600 placeholder:text-slate-400 focus:outline-none"
        />
      </div>

      <div className="flex items-center gap-4">
        <button className="flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-600 hover:bg-slate-50">
          <Calendar size={16} />
          <span>1 Kas 2024 - 30 Kas 2024</span>
        </button>

        <button className="relative rounded-lg p-2 text-slate-500 hover:bg-slate-50">
          <Bell size={18} />
          {notificationCount > 0 && (
            <span className="absolute -right-0.5 -top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-semibold text-white">
              {notificationCount}
            </span>
          )}
        </button>

        <div className="flex items-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-brand-100 text-sm font-semibold text-brand-700">
            {initials}
          </div>
          <div className="hidden text-left sm:block">
            <p className="text-sm font-medium leading-tight text-slate-700">{userName}</p>
            <p className="text-xs leading-tight text-slate-400">{userRole}</p>
          </div>
        </div>
      </div>
    </header>
  );
}
