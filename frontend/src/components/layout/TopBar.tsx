import {
  Bell,
  ChevronDown,
  Moon,
  Search,
  Sun,
} from "lucide-react";
import {
  useEffect,
  useState,
} from "react";


interface TopBarProps {
  userName?: string;
  userRole?: string;
  notificationCount?: number;
}


type Theme = "light" | "dark";


function getInitialTheme(): Theme {
  const stored =
    localStorage.getItem(
      "veritas-theme"
    );

  if (
    stored === "light" ||
    stored === "dark"
  ) {
    return stored;
  }

  return window.matchMedia(
    "(prefers-color-scheme: dark)"
  ).matches
    ? "dark"
    : "light";
}


export default function TopBar({
  userName = "Deniz Karaca",
  userRole = "Analist",
  notificationCount = 3,
}: TopBarProps) {
  const [theme, setTheme] =
    useState<Theme>(
      getInitialTheme
    );

  useEffect(() => {
    document.documentElement.classList.toggle(
      "dark",
      theme === "dark"
    );

    document.documentElement.classList.add(
      "theme-transition"
    );

    localStorage.setItem(
      "veritas-theme",
      theme
    );
  }, [theme]);

  const initials = userName
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  function toggleTheme() {
    setTheme((current) =>
      current === "dark"
        ? "light"
        : "dark"
    );
  }

  return (
    <header className="flex h-[68px] shrink-0 items-center justify-between border-b border-[#e8e1de] bg-white/95 px-6 backdrop-blur dark:border-white/[0.07] dark:bg-[#171016]/95 lg:px-8">
      <div className="flex w-full max-w-[430px] items-center gap-2 rounded-lg border border-[#e5dedb] bg-[#faf8f7] px-3.5 py-2.5 transition focus-within:border-[#cbbdb7] focus-within:bg-white dark:border-white/[0.08] dark:bg-white/[0.035] dark:focus-within:border-white/[0.16] dark:focus-within:bg-white/[0.055]">
        <Search
          size={16}
          strokeWidth={1.8}
          className="text-[#988b90] dark:text-[#81747b]"
        />

        <input
          type="text"
          placeholder="İçerik, kaynak veya analiz ara..."
          className="w-full bg-transparent text-sm text-[#352b2f] outline-none placeholder:text-[#a4979b] dark:text-[#f7efed] dark:placeholder:text-[#776a71]"
        />
      </div>

      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={toggleTheme}
          aria-label="Tema değiştir"
          title={
            theme === "dark"
              ? "Açık temaya geç"
              : "Koyu temaya geç"
          }
          className="flex h-9 w-9 items-center justify-center rounded-lg border border-transparent text-[#786b70] transition hover:border-[#e8e1de] hover:bg-[#faf7f5] hover:text-[#2c2226] dark:text-[#ab9ca2] dark:hover:border-white/[0.08] dark:hover:bg-white/[0.05] dark:hover:text-white"
        >
          {theme === "dark" ? (
            <Sun
              size={17}
              strokeWidth={1.8}
            />
          ) : (
            <Moon
              size={17}
              strokeWidth={1.8}
            />
          )}
        </button>

        <button
          type="button"
          aria-label="Bildirimler"
          className="relative flex h-9 w-9 items-center justify-center rounded-lg text-[#786b70] transition hover:bg-[#faf7f5] hover:text-[#2c2226] dark:text-[#ab9ca2] dark:hover:bg-white/[0.05] dark:hover:text-white"
        >
          <Bell
            size={18}
            strokeWidth={1.8}
          />

          {notificationCount > 0 && (
            <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-[#e45360] ring-2 ring-white dark:ring-[#171016]" />
          )}
        </button>

        <div className="mx-2 h-7 w-px bg-[#e8e1de] dark:bg-white/[0.08]" />

        <button
          type="button"
          className="flex items-center gap-3 rounded-lg px-2 py-1.5 transition hover:bg-[#faf7f5] dark:hover:bg-white/[0.045]"
        >
          <div className="flex h-9 w-9 items-center justify-center rounded-full border border-[#e7dfdc] bg-[#f2ece9] text-xs font-semibold text-[#57494e] dark:border-white/[0.08] dark:bg-white/[0.08] dark:text-[#f5e9e6]">
            {initials}
          </div>

          <div className="hidden text-left sm:block">
            <p className="text-sm font-semibold leading-tight text-[#2b2225] dark:text-[#f8f1ee]">
              {userName}
            </p>

            <p className="mt-0.5 text-[11px] leading-tight text-[#9a8d92] dark:text-[#85777e]">
              {userRole}
            </p>
          </div>

          <ChevronDown
            size={15}
            className="text-[#a2959a] dark:text-[#796c73]"
          />
        </button>
      </div>
    </header>
  );
}
