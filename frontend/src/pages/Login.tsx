import {
  ArrowRight,
  Eye,
  EyeOff,
  FileSearch,
  LockKeyhole,
  ShieldCheck,
  UserRound,
} from "lucide-react";

import {
  useEffect,
  useState,
  type FormEvent,
} from "react";

import {
  useLocation,
  useNavigate,
} from "react-router-dom";

import {
  login,
} from "../api/client";


export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();

  const from =
    (
      location.state as {
        from?: string;
      } | null
    )?.from ?? "/";

  const [
    username,
    setUsername,
  ] = useState("");

  const [
    password,
    setPassword,
  ] = useState("");

  const [
    showPassword,
    setShowPassword,
  ] = useState(false);

  const [
    rememberMe,
    setRememberMe,
  ] = useState(false);

  const [
    forgotMessage,
    setForgotMessage,
  ] = useState<string | null>(
    null
  );

  const [
    error,
    setError,
  ] = useState<string | null>(
    null
  );

  const [
    submitting,
    setSubmitting,
  ] = useState(false);


  useEffect(() => {
    const rememberedUsername =
      localStorage.getItem(
        "veritas_remembered_username"
      );

    if (rememberedUsername) {
      setUsername(
        rememberedUsername
      );

      setRememberMe(true);
    }
  }, []);


  async function handleSubmit(
    event: FormEvent
  ) {
    event.preventDefault();

    setSubmitting(true);
    setError(null);

    try {
      await login(
        username,
        password
      );

      if (rememberMe) {
        localStorage.setItem(
          "veritas_remembered_username",
          username
        );
      } else {
        localStorage.removeItem(
          "veritas_remembered_username"
        );
      }

      navigate(
        from,
        {
          replace: true,
        }
      );
    } catch {
      setError(
        "Kullanıcı adı veya şifre hatalı. Bilgilerinizi kontrol edip tekrar deneyin."
      );
    } finally {
      setSubmitting(false);
    }
  }


  return (
    <div className="min-h-screen bg-[#f6f4f2] text-[#302529] dark:bg-[#120c12] dark:text-[#f8efec]">
      <div className="grid min-h-screen lg:grid-cols-[0.95fr_1.05fr]">

        {/* Brand panel */}
        <section className="relative hidden overflow-hidden border-r border-[#e5dcd8] bg-[#1b1218] lg:flex lg:flex-col lg:justify-between dark:border-white/[0.06]">

          <div className="absolute inset-x-0 top-0 h-px bg-[#e85f32]/60" />

          <div className="pointer-events-none absolute -left-40 -top-40 h-[420px] w-[420px] rounded-full bg-[#8b315b]/10 blur-3xl" />

          <div className="pointer-events-none absolute -bottom-52 right-[-120px] h-[420px] w-[420px] rounded-full bg-[#e85f32]/[0.07] blur-3xl" />

          <div className="relative z-10 p-10 xl:p-14">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-[#e85f32]/30 bg-[#e85f32]/10">
                <span className="text-lg font-bold text-[#ff895d]">
                  V
                </span>
              </div>

              <div>
                <div className="text-[15px] font-semibold tracking-[0.18em] text-[#fff8f5]">
                  VERITAS
                </div>

                <div className="mt-0.5 text-[9px] font-medium uppercase tracking-[0.2em] text-[#807178]">
                  Intelligence Platform
                </div>
              </div>
            </div>
          </div>

          <div className="relative z-10 max-w-xl px-10 pb-12 xl:px-14 xl:pb-16">
            <div className="mb-6 h-px w-10 bg-[#e85f32]" />

            <h1 className="max-w-lg text-[30px] font-semibold leading-[1.15] tracking-[-0.03em] text-[#f8efec] xl:text-[36px]">
              Bilgiyi analiz et.
              <br />
              Kanıtla doğrula.
            </h1>

            <p className="mt-5 max-w-md text-[13px] leading-6 text-[#95878d]">
              Dezenformasyon analizi, kanıt değerlendirme
              ve araştırma süreçlerini tek çalışma alanında
              yönetin.
            </p>

            <div className="mt-10 space-y-3">
              <div className="flex items-center gap-3 border-t border-white/[0.06] py-3">
                <FileSearch
                  size={16}
                  className="text-[#d26c48]"
                />

                <span className="text-[11px] text-[#a99ca1]">
                  Evidence destekli analiz
                </span>
              </div>

              <div className="flex items-center gap-3 border-t border-white/[0.06] py-3">
                <ShieldCheck
                  size={16}
                  className="text-[#d26c48]"
                />

                <span className="text-[11px] text-[#a99ca1]">
                  Güvenli analist çalışma alanı
                </span>
              </div>
            </div>
          </div>

          <div className="relative z-10 flex items-center justify-between border-t border-white/[0.06] px-10 py-5 text-[9px] uppercase tracking-[0.14em] text-[#665960] xl:px-14">
            <span>
              VERITAS Platform
            </span>

            <span>
              Secure Access
            </span>
          </div>
        </section>


        {/* Login panel */}
        <section className="relative flex min-h-screen items-center justify-center px-5 py-10 sm:px-8 lg:px-12">

          <div className="pointer-events-none absolute right-0 top-0 h-64 w-64 bg-[#e85f32]/[0.025] blur-3xl dark:bg-[#e85f32]/[0.035]" />

          <div className="relative w-full max-w-[420px]">

            {/* Mobile brand */}
            <div className="mb-10 flex items-center gap-3 lg:hidden">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-[#d9cdc8] bg-white shadow-sm dark:border-white/[0.08] dark:bg-[#1c1319]">
                <span className="text-lg font-bold text-[#c86038] dark:text-[#ff895d]">
                  V
                </span>
              </div>

              <div>
                <div className="text-sm font-semibold tracking-[0.18em]">
                  VERITAS
                </div>

                <div className="mt-0.5 text-[9px] uppercase tracking-[0.18em] text-[#988b90]">
                  Intelligence Platform
                </div>
              </div>
            </div>


            <div className="mb-8">
              <div className="mb-3 flex items-center gap-2 text-[10px] font-medium uppercase tracking-[0.14em] text-[#a75a40] dark:text-[#d97956]">
                <LockKeyhole size={13} />
                Güvenli erişim
              </div>

              <h2 className="text-[27px] font-semibold tracking-[-0.035em] text-[#302529] dark:text-[#f8efec]">
                Tekrar hoş geldiniz
              </h2>

              <p className="mt-2 text-[12px] leading-5 text-[#988b90] dark:text-[#84767c]">
                VERITAS çalışma alanına devam etmek için
                hesabınızla giriş yapın.
              </p>
            </div>


            <form
              onSubmit={handleSubmit}
              className="rounded-2xl border border-[#e2d9d5] bg-white p-6 shadow-[0_18px_55px_rgba(65,42,49,0.06)] sm:p-7 dark:border-white/[0.08] dark:bg-[#1a1218] dark:shadow-none"
            >
              <div>
                <label
                  htmlFor="username"
                  className="mb-2 block text-[11px] font-medium text-[#66585d] dark:text-[#aa9da2]"
                >
                  Kullanıcı adı
                </label>

                <div className="group relative">
                  <UserRound
                    size={15}
                    className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-[#a99ca1] transition group-focus-within:text-[#c86038]"
                  />

                  <input
                    id="username"
                    name="username"
                    autoComplete="username"
                    value={username}
                    onChange={(event) =>
                      setUsername(
                        event.target.value
                      )
                    }
                    placeholder="Kullanıcı adınızı girin"
                    className="h-11 w-full rounded-lg border border-[#ded4d0] bg-[#fbfaf9] pl-10 pr-3 text-[12px] text-[#3f3337] outline-none transition placeholder:text-[#b9afb2] focus:border-[#c86038]/60 focus:bg-white focus:ring-2 focus:ring-[#c86038]/[0.06] dark:border-white/[0.09] dark:bg-[#21171e] dark:text-[#eee4e7] dark:placeholder:text-[#65585e] dark:focus:border-[#e87950]/40 dark:focus:bg-[#21171e]"
                    required
                  />
                </div>
              </div>


              <div className="mt-5">
                <label
                  htmlFor="password"
                  className="mb-2 block text-[11px] font-medium text-[#66585d] dark:text-[#aa9da2]"
                >
                  Şifre
                </label>

                <div className="group relative">
                  <LockKeyhole
                    size={15}
                    className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-[#a99ca1] transition group-focus-within:text-[#c86038]"
                  />

                  <input
                    id="password"
                    name="password"
                    type={
                      showPassword
                        ? "text"
                        : "password"
                    }
                    autoComplete="current-password"
                    value={password}
                    onChange={(event) =>
                      setPassword(
                        event.target.value
                      )
                    }
                    placeholder="Şifrenizi girin"
                    className="h-11 w-full rounded-lg border border-[#ded4d0] bg-[#fbfaf9] pl-10 pr-11 text-[12px] text-[#3f3337] outline-none transition placeholder:text-[#b9afb2] focus:border-[#c86038]/60 focus:bg-white focus:ring-2 focus:ring-[#c86038]/[0.06] dark:border-white/[0.09] dark:bg-[#21171e] dark:text-[#eee4e7] dark:placeholder:text-[#65585e] dark:focus:border-[#e87950]/40 dark:focus:bg-[#21171e]"
                    required
                  />

                  <button
                    type="button"
                    onClick={() =>
                      setShowPassword(
                        (current) =>
                          !current
                      )
                    }
                    className="absolute right-3 top-1/2 flex -translate-y-1/2 items-center justify-center rounded-md p-1 text-[#9e9196] transition hover:text-[#5d4f54] dark:hover:text-[#d8cdd1]"
                    aria-label={
                      showPassword
                        ? "Şifreyi gizle"
                        : "Şifreyi göster"
                    }
                  >
                    {showPassword ? (
                      <EyeOff size={15} />
                    ) : (
                      <Eye size={15} />
                    )}
                  </button>
                </div>
              </div>


              <div className="mt-4 flex items-center justify-between gap-4">
                <label className="flex cursor-pointer items-center gap-2.5">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(event) =>
                      setRememberMe(
                        event.target.checked
                      )
                    }
                    className="peer sr-only"
                  />

                  <span className="flex h-4 w-4 items-center justify-center rounded-[4px] border border-[#d7ccc8] bg-[#fbfaf9] transition peer-checked:border-[#c86038] peer-checked:bg-[#c86038] dark:border-white/[0.12] dark:bg-[#21171e] dark:peer-checked:border-[#e87950] dark:peer-checked:bg-[#e87950]">
                    {rememberMe && (
                      <svg
                        viewBox="0 0 16 16"
                        className="h-3 w-3 text-white"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2.2"
                      >
                        <path
                          d="M3.5 8.2 6.5 11 12.5 4.8"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                      </svg>
                    )}
                  </span>

                  <span className="text-[11px] text-[#75676c] dark:text-[#91848a]">
                    Beni hatırla
                  </span>
                </label>

                <button
                  type="button"
                  onClick={() =>
                    navigate(
                      "/forgot-password"
                    )
                  }
                  className="text-[11px] font-medium text-[#a9573c] transition hover:text-[#c86038] hover:underline hover:underline-offset-4 dark:text-[#d77a58] dark:hover:text-[#f08a62]"
                >
                  Şifremi unuttum?
                </button>
              </div>


              {forgotMessage && (
                <div className="mt-4 flex items-start justify-between gap-3 rounded-lg border border-[#eaded9] bg-[#faf7f5] px-3.5 py-3 dark:border-white/[0.07] dark:bg-white/[0.025]">
                  <p className="text-[10px] leading-5 text-[#817278] dark:text-[#8f8187]">
                    {forgotMessage}
                  </p>

                  <button
                    type="button"
                    onClick={() =>
                      setForgotMessage(
                        null
                      )
                    }
                    className="shrink-0 text-[13px] leading-none text-[#9e9196] transition hover:text-[#57494e] dark:hover:text-[#d8cdd1]"
                    aria-label="Mesajı kapat"
                  >
                    ×
                  </button>
                </div>
              )}


              {error && (
                <div className="mt-5 rounded-lg border border-[#e9c9c3] bg-[#fff5f3] px-3.5 py-3 text-[11px] leading-5 text-[#a7483b] dark:border-red-400/10 dark:bg-red-400/[0.05] dark:text-red-300">
                  {error}
                </div>
              )}


              <button
                type="submit"
                disabled={submitting}
                className="mt-6 flex h-11 w-full items-center justify-center gap-2 rounded-lg bg-[#302529] px-4 text-[12px] font-medium text-white transition hover:bg-[#44363b] disabled:cursor-not-allowed disabled:opacity-60 dark:bg-[#e86f45] dark:text-[#1a1014] dark:hover:bg-[#f17b51]"
              >
                {submitting
                  ? "Giriş yapılıyor..."
                  : "Giriş yap"}

                {!submitting && (
                  <ArrowRight
                    size={15}
                  />
                )}
              </button>


              <div className="mt-5 flex items-center justify-center gap-1.5 text-[9px] uppercase tracking-[0.1em] text-[#aaa0a3] dark:text-[#665a60]">
                <ShieldCheck
                  size={12}
                />
                HttpOnly JWT ile güvenli oturum
              </div>
            </form>

            <div className="mt-5 text-center text-[10px] text-[#8e8085]">
              Hesabınız yok mu?{" "}

              <button
                type="button"
                onClick={() =>
                  navigate(
                    "/register"
                  )
                }
                className="font-medium text-[#a9573c] transition hover:underline hover:underline-offset-4"
              >
                Hesap oluştur
              </button>
            </div>



            <p className="mt-6 text-center text-[10px] text-[#aaa0a3] dark:text-[#62565b]">
              Yetkili kullanıcı erişimi · VERITAS
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}
