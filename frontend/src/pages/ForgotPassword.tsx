import {
  ArrowLeft,
  ArrowRight,
  Check,
  Eye,
  EyeOff,
  KeyRound,
  Mail,
  RotateCcw,
  ShieldCheck,
} from "lucide-react";

import {
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
} from "react";

import {
  Link,
} from "react-router-dom";

import {
  confirmPasswordReset,
  requestPasswordReset,
  verifyPasswordResetCode,
} from "../api/client";


type ResetStep =
  | "email"
  | "code"
  | "password"
  | "success";


function getErrorMessage(
  error: unknown,
  fallback: string
): string {
  if (
    typeof error === "object" &&
    error !== null &&
    "response" in error
  ) {
    const response = (
      error as {
        response?: {
          data?: {
            detail?: string;
            new_password?: string[];
          };
        };
      }
    ).response;

    if (
      response?.data
        ?.new_password
        ?.length
    ) {
      return response.data
        .new_password
        .join(" ");
    }

    if (
      typeof response?.data?.detail
      === "string"
    ) {
      return response.data.detail;
    }
  }

  return fallback;
}


function maskEmail(
  email: string
): string {
  const [
    local,
    domain,
  ] = email.split("@");

  if (!domain) {
    return email;
  }

  const visible =
    local.slice(
      0,
      Math.min(
        local.length,
        2
      )
    );

  const hidden =
    "*".repeat(
      Math.max(
        3,
        local.length -
          visible.length
      )
    );

  return (
    `${visible}${hidden}@${domain}`
  );
}


export default function ForgotPassword() {
  const [
    step,
    setStep,
  ] = useState<ResetStep>(
    "email"
  );

  const [
    email,
    setEmail,
  ] = useState("");

  const [
    code,
    setCode,
  ] = useState<string[]>(
    ["", "", "", "", "", ""]
  );

  const [
    resetToken,
    setResetToken,
  ] = useState("");

  const [
    password,
    setPassword,
  ] = useState("");

  const [
    confirmPassword,
    setConfirmPassword,
  ] = useState("");

  const [
    showPassword,
    setShowPassword,
  ] = useState(false);

  const [
    cooldown,
    setCooldown,
  ] = useState(0);

  const [
    submitting,
    setSubmitting,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState<string | null>(
    null
  );

  const codeRefs =
    useRef<
      Array<
        HTMLInputElement | null
      >
    >([]);


  useEffect(() => {
    if (cooldown <= 0) {
      return;
    }

    const timer =
      window.setInterval(
        () => {
          setCooldown(
            (current) =>
              Math.max(
                current - 1,
                0
              )
          );
        },
        1000
      );

    return () => {
      window.clearInterval(
        timer
      );
    };
  }, [cooldown]);


  async function sendCode(
    event?: FormEvent
  ) {
    event?.preventDefault();

    setSubmitting(true);
    setError(null);

    try {
      const result =
        await requestPasswordReset(
          email
        );

      setCode(
        ["", "", "", "", "", ""]
      );

      setCooldown(
        result.cooldown_seconds ??
          60
      );

      setStep("code");

      window.setTimeout(
        () => {
          codeRefs.current[0]
            ?.focus();
        },
        0
      );
    } catch (requestError) {
      setError(
        getErrorMessage(
          requestError,
          "Doğrulama kodu gönderilemedi. Lütfen tekrar deneyin."
        )
      );
    } finally {
      setSubmitting(false);
    }
  }


  function changeCode(
    index: number,
    value: string
  ) {
    const digit =
      value
        .replace(/\D/g, "")
        .slice(-1);

    const next = [
      ...code
    ];

    next[index] = digit;

    setCode(next);
    setError(null);

    if (
      digit &&
      index < 5
    ) {
      codeRefs.current[
        index + 1
      ]?.focus();
    }
  }


  function codeKeyDown(
    index: number,
    event: KeyboardEvent<HTMLInputElement>
  ) {
    if (
      event.key ===
        "Backspace" &&
      !code[index] &&
      index > 0
    ) {
      codeRefs.current[
        index - 1
      ]?.focus();
    }
  }


  function pasteCode(
    value: string
  ) {
    const digits =
      value
        .replace(/\D/g, "")
        .slice(0, 6)
        .split("");

    if (!digits.length) {
      return;
    }

    setCode(
      Array.from(
        {
          length: 6,
        },
        (_, index) =>
          digits[index] ?? ""
      )
    );

    codeRefs.current[
      Math.min(
        digits.length,
        6
      ) - 1
    ]?.focus();
  }


  async function verifyCode(
    event: FormEvent
  ) {
    event.preventDefault();

    const value =
      code.join("");

    if (
      value.length !== 6
    ) {
      setError(
        "6 haneli doğrulama kodunu eksiksiz girin."
      );

      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const result =
        await verifyPasswordResetCode(
          email,
          value
        );

      setResetToken(
        result.reset_token
      );

      setStep(
        "password"
      );
    } catch (requestError) {
      setError(
        getErrorMessage(
          requestError,
          "Doğrulama kodu geçersiz veya süresi dolmuş."
        )
      );
    } finally {
      setSubmitting(false);
    }
  }


  async function resendCode() {
    if (
      cooldown > 0 ||
      submitting
    ) {
      return;
    }

    await sendCode();
  }


  async function updatePassword(
    event: FormEvent
  ) {
    event.preventDefault();

    if (
      password !==
      confirmPassword
    ) {
      setError(
        "Şifreler eşleşmiyor."
      );

      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      await confirmPasswordReset(
        {
          reset_token:
            resetToken,
          new_password:
            password,
          confirm_password:
            confirmPassword,
        }
      );

      setResetToken("");
      setPassword("");
      setConfirmPassword("");

      setStep(
        "success"
      );
    } catch (requestError) {
      setError(
        getErrorMessage(
          requestError,
          "Şifre güncellenemedi. Doğrulama oturumunuzun süresi dolmuş olabilir."
        )
      );
    } finally {
      setSubmitting(false);
    }
  }


  return (
    <div className="min-h-screen bg-[#f6f4f2] text-[#302529] dark:bg-[#120c12] dark:text-[#f8efec]">
      <div className="grid min-h-screen lg:grid-cols-[0.95fr_1.05fr]">

        <section className="relative hidden overflow-hidden border-r border-[#e5dcd8] bg-[#1b1218] lg:flex lg:flex-col lg:justify-between dark:border-white/[0.06]">
          <div className="absolute inset-x-0 top-0 h-px bg-[#e85f32]/60" />

          <div className="p-10 xl:p-14">
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

                <div className="mt-0.5 text-[9px] uppercase tracking-[0.2em] text-[#807178]">
                  Intelligence Platform
                </div>
              </div>
            </div>
          </div>

          <div className="max-w-xl px-10 pb-16 xl:px-14">
            <div className="mb-6 h-px w-10 bg-[#e85f32]" />

            <h1 className="text-[32px] font-semibold tracking-[-0.03em] text-[#f8efec]">
              Hesabınıza yeniden erişin.
            </h1>

            <p className="mt-5 max-w-md text-[13px] leading-6 text-[#95878d]">
              Kimliğinizi e-posta doğrulamasıyla
              güvenli şekilde doğrulayın ve hesabınız
              için yeni bir şifre oluşturun.
            </p>

            <div className="mt-10 space-y-3 text-[11px] text-[#a99ca1]">
              <div className="flex items-center gap-3 border-t border-white/[0.06] py-3">
                <ShieldCheck
                  size={15}
                  className="text-[#d26c48]"
                />

                6 haneli tek kullanımlık doğrulama kodu
              </div>

              <div className="flex items-center gap-3 border-t border-white/[0.06] py-3">
                <KeyRound
                  size={15}
                  className="text-[#d26c48]"
                />

                Kısa süreli güvenli şifre yenileme oturumu
              </div>
            </div>
          </div>

          <div className="border-t border-white/[0.06] px-10 py-5 text-[9px] uppercase tracking-[0.14em] text-[#665960] xl:px-14">
            VERITAS · Secure account recovery
          </div>
        </section>


        <section className="flex min-h-screen items-center justify-center px-5 py-10 sm:px-8">
          <div className="w-full max-w-[420px]">

            {step !==
              "success" && (
              <Link
                to="/login"
                className="mb-8 inline-flex items-center gap-2 text-[11px] text-[#85777c] transition hover:text-[#b15e42]"
              >
                <ArrowLeft
                  size={14}
                />

                Giriş ekranına dön
              </Link>
            )}


            {step === "email" && (
              <>
                <div className="mb-8">
                  <div className="mb-3 flex items-center gap-2 text-[10px] font-medium uppercase tracking-[0.14em] text-[#a75a40]">
                    <ShieldCheck
                      size={13}
                    />

                    Hesap kurtarma
                  </div>

                  <h1 className="text-[27px] font-semibold tracking-[-0.035em]">
                    Şifrenizi sıfırlayın
                  </h1>

                  <p className="mt-2 text-[12px] leading-5 text-[#988b90]">
                    VERITAS hesabınızda kullandığınız
                    e-posta adresini girin.
                  </p>
                </div>

                <form
                  onSubmit={
                    sendCode
                  }
                  className="rounded-2xl border border-[#e2d9d5] bg-white p-7 shadow-[0_18px_55px_rgba(65,42,49,0.06)] dark:border-white/[0.08] dark:bg-[#1a1218]"
                >
                  <label
                    htmlFor="email"
                    className="mb-2 block text-[11px] font-medium text-[#66585d]"
                  >
                    E-posta adresi
                  </label>

                  <div className="relative">
                    <Mail
                      size={15}
                      className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#a99ca1]"
                    />

                    <input
                      id="email"
                      type="email"
                      autoComplete="email"
                      value={email}
                      onChange={(event) =>
                        setEmail(
                          event
                            .target
                            .value
                        )
                      }
                      placeholder="ornek@veritas.com"
                      className="h-11 w-full rounded-lg border border-[#ded4d0] bg-[#fbfaf9] pl-10 pr-3 text-[12px] outline-none transition focus:border-[#c86038]/60 focus:ring-2 focus:ring-[#c86038]/[0.06] dark:border-white/[0.09] dark:bg-[#21171e]"
                      required
                    />
                  </div>

                  {error && (
                    <div className="mt-5 rounded-lg border border-[#e9c9c3] bg-[#fff5f3] px-3.5 py-3 text-[11px] leading-5 text-[#a7483b]">
                      {error}
                    </div>
                  )}

                  <button
                    type="submit"
                    disabled={
                      submitting
                    }
                    className="mt-6 flex h-11 w-full items-center justify-center gap-2 rounded-lg bg-[#302529] text-[12px] font-medium text-white transition hover:bg-[#44363b] disabled:opacity-60 dark:bg-[#e86f45] dark:text-[#1a1014]"
                  >
                    {submitting
                      ? "Gönderiliyor..."
                      : "Doğrulama kodu gönder"}

                    {!submitting && (
                      <ArrowRight
                        size={15}
                      />
                    )}
                  </button>
                </form>
              </>
            )}


            {step === "code" && (
              <>
                <div className="mb-8">
                  <div className="mb-3 flex items-center gap-2 text-[10px] font-medium uppercase tracking-[0.14em] text-[#a75a40]">
                    <Mail
                      size={13}
                    />

                    E-posta doğrulama
                  </div>

                  <h1 className="text-[27px] font-semibold tracking-[-0.035em]">
                    Kodunuzu girin
                  </h1>

                  <p className="mt-2 text-[12px] leading-5 text-[#988b90]">
                    <span className="font-medium text-[#66585d]">
                      {maskEmail(
                        email
                      )}
                    </span>
                    {" "}
                    adresine gönderilen
                    6 haneli kodu girin.
                  </p>
                </div>

                <form
                  onSubmit={
                    verifyCode
                  }
                  className="rounded-2xl border border-[#e2d9d5] bg-white p-7 shadow-[0_18px_55px_rgba(65,42,49,0.06)] dark:border-white/[0.08] dark:bg-[#1a1218]"
                >
                  <div className="grid grid-cols-6 gap-2">
                    {code.map(
                      (
                        digit,
                        index
                      ) => (
                        <input
                          key={
                            index
                          }
                          ref={(
                            element
                          ) => {
                            codeRefs
                              .current[
                                index
                              ] =
                                element;
                          }}
                          value={
                            digit
                          }
                          onChange={(
                            event
                          ) =>
                            changeCode(
                              index,
                              event
                                .target
                                .value
                            )
                          }
                          onKeyDown={(
                            event
                          ) =>
                            codeKeyDown(
                              index,
                              event
                            )
                          }
                          onPaste={(
                            event
                          ) => {
                            event
                              .preventDefault();

                            pasteCode(
                              event
                                .clipboardData
                                .getData(
                                  "text"
                                )
                            );
                          }}
                          inputMode="numeric"
                          autoComplete={
                            index === 0
                              ? "one-time-code"
                              : "off"
                          }
                          maxLength={
                            1
                          }
                          className="h-12 min-w-0 rounded-lg border border-[#ded4d0] bg-[#fbfaf9] text-center text-[17px] font-semibold outline-none transition focus:border-[#c86038]/70 focus:ring-2 focus:ring-[#c86038]/[0.08] dark:border-white/[0.09] dark:bg-[#21171e]"
                        />
                      )
                    )}
                  </div>

                  {error && (
                    <div className="mt-5 rounded-lg border border-[#e9c9c3] bg-[#fff5f3] px-3.5 py-3 text-[11px] leading-5 text-[#a7483b]">
                      {error}
                    </div>
                  )}

                  <button
                    type="submit"
                    disabled={
                      submitting ||
                      code
                        .join("")
                        .length !==
                        6
                    }
                    className="mt-6 flex h-11 w-full items-center justify-center gap-2 rounded-lg bg-[#302529] text-[12px] font-medium text-white transition hover:bg-[#44363b] disabled:cursor-not-allowed disabled:opacity-45 dark:bg-[#e86f45] dark:text-[#1a1014]"
                  >
                    {submitting
                      ? "Doğrulanıyor..."
                      : "Kodu doğrula"}

                    {!submitting && (
                      <ArrowRight
                        size={15}
                      />
                    )}
                  </button>

                  <div className="mt-5 flex items-center justify-between border-t border-[#eee6e2] pt-5 dark:border-white/[0.06]">
                    <button
                      type="button"
                      onClick={() => {
                        setStep(
                          "email"
                        );
                        setError(
                          null
                        );
                      }}
                      className="text-[10px] text-[#8b7d82] transition hover:text-[#a9573c]"
                    >
                      E-postayı değiştir
                    </button>

                    <button
                      type="button"
                      disabled={
                        cooldown >
                          0 ||
                        submitting
                      }
                      onClick={
                        resendCode
                      }
                      className="flex items-center gap-1.5 text-[10px] font-medium text-[#a9573c] disabled:cursor-not-allowed disabled:text-[#aaa0a3]"
                    >
                      <RotateCcw
                        size={12}
                      />

                      {cooldown > 0
                        ? `Tekrar gönder 00:${String(
                            cooldown
                          ).padStart(
                            2,
                            "0"
                          )}`
                        : "Kodu tekrar gönder"}
                    </button>
                  </div>
                </form>
              </>
            )}


            {step ===
              "password" && (
              <>
                <div className="mb-8">
                  <div className="mb-3 flex items-center gap-2 text-[10px] font-medium uppercase tracking-[0.14em] text-[#a75a40]">
                    <KeyRound
                      size={13}
                    />

                    Yeni şifre
                  </div>

                  <h1 className="text-[27px] font-semibold tracking-[-0.035em]">
                    Yeni şifrenizi belirleyin
                  </h1>

                  <p className="mt-2 text-[12px] leading-5 text-[#988b90]">
                    E-posta doğrulaması tamamlandı.
                    Hesabınız için güçlü bir yeni
                    şifre oluşturun.
                  </p>
                </div>

                <form
                  onSubmit={
                    updatePassword
                  }
                  className="rounded-2xl border border-[#e2d9d5] bg-white p-7 shadow-[0_18px_55px_rgba(65,42,49,0.06)] dark:border-white/[0.08] dark:bg-[#1a1218]"
                >
                  <label
                    htmlFor="new-password"
                    className="mb-2 block text-[11px] font-medium text-[#66585d]"
                  >
                    Yeni şifre
                  </label>

                  <div className="relative">
                    <KeyRound
                      size={15}
                      className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#a99ca1]"
                    />

                    <input
                      id="new-password"
                      type={
                        showPassword
                          ? "text"
                          : "password"
                      }
                      autoComplete="new-password"
                      value={
                        password
                      }
                      onChange={(
                        event
                      ) =>
                        setPassword(
                          event
                            .target
                            .value
                        )
                      }
                      className="h-11 w-full rounded-lg border border-[#ded4d0] bg-[#fbfaf9] pl-10 pr-11 text-[12px] outline-none focus:border-[#c86038]/60 dark:border-white/[0.09] dark:bg-[#21171e]"
                      minLength={8}
                      required
                    />

                    <button
                      type="button"
                      onClick={() =>
                        setShowPassword(
                          (
                            current
                          ) =>
                            !current
                        )
                      }
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-[#9e9196]"
                    >
                      {showPassword ? (
                        <EyeOff
                          size={15}
                        />
                      ) : (
                        <Eye
                          size={15}
                        />
                      )}
                    </button>
                  </div>

                  <label
                    htmlFor="confirm-password"
                    className="mb-2 mt-5 block text-[11px] font-medium text-[#66585d]"
                  >
                    Yeni şifre tekrar
                  </label>

                  <input
                    id="confirm-password"
                    type={
                      showPassword
                        ? "text"
                        : "password"
                    }
                    autoComplete="new-password"
                    value={
                      confirmPassword
                    }
                    onChange={(
                      event
                    ) =>
                      setConfirmPassword(
                        event
                          .target
                          .value
                      )
                    }
                    className="h-11 w-full rounded-lg border border-[#ded4d0] bg-[#fbfaf9] px-3 text-[12px] outline-none focus:border-[#c86038]/60 dark:border-white/[0.09] dark:bg-[#21171e]"
                    minLength={8}
                    required
                  />

                  {error && (
                    <div className="mt-5 rounded-lg border border-[#e9c9c3] bg-[#fff5f3] px-3.5 py-3 text-[11px] leading-5 text-[#a7483b]">
                      {error}
                    </div>
                  )}

                  <button
                    type="submit"
                    disabled={
                      submitting
                    }
                    className="mt-6 flex h-11 w-full items-center justify-center gap-2 rounded-lg bg-[#302529] text-[12px] font-medium text-white transition hover:bg-[#44363b] disabled:opacity-60 dark:bg-[#e86f45] dark:text-[#1a1014]"
                  >
                    {submitting
                      ? "Güncelleniyor..."
                      : "Şifreyi güncelle"}

                    {!submitting && (
                      <ArrowRight
                        size={15}
                      />
                    )}
                  </button>
                </form>
              </>
            )}


            {step ===
              "success" && (
              <div className="rounded-2xl border border-[#e2d9d5] bg-white p-8 shadow-[0_18px_55px_rgba(65,42,49,0.06)] dark:border-white/[0.08] dark:bg-[#1a1218]">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl border border-[#d9e4dc] bg-[#f4faf6] text-[#52735c]">
                  <Check
                    size={20}
                  />
                </div>

                <h1 className="mt-6 text-[24px] font-semibold tracking-[-0.03em]">
                  Şifreniz güncellendi
                </h1>

                <p className="mt-2 text-[12px] leading-5 text-[#8c7f84]">
                  Yeni şifrenizle VERITAS çalışma
                  alanınıza giriş yapabilirsiniz.
                </p>

                <Link
                  to="/login"
                  className="mt-7 flex h-11 w-full items-center justify-center gap-2 rounded-lg bg-[#302529] text-[12px] font-medium text-white dark:bg-[#e86f45] dark:text-[#1a1014]"
                >
                  Giriş yap

                  <ArrowRight
                    size={15}
                  />
                </Link>
              </div>
            )}

          </div>
        </section>
      </div>
    </div>
  );
}
