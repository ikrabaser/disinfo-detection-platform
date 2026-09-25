import {
  ArrowLeft,
  ArrowRight,
  Check,
  Eye,
  EyeOff,
  LockKeyhole,
  Mail,
  RotateCcw,
  ShieldCheck,
  UserRound,
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
  registerUser,
  resendRegistrationCode,
  verifyRegistrationCode,
} from "../api/client";


type RegisterStep =
  | "details"
  | "code"
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
          data?: Record<
            string,
            string | string[] | number
          >;
        };
      }
    ).response;

    const data = response?.data;

    if (data) {
      const priority = [
        "username",
        "email",
        "password",
        "confirm_password",
        "code",
        "detail",
      ];

      for (const key of priority) {
        const value = data[key];

        if (
          Array.isArray(value) &&
          value.length
        ) {
          return value.join(" ");
        }

        if (
          typeof value === "string"
        ) {
          return value;
        }
      }
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
        2,
        local.length
      )
    );

  return (
    `${visible}${"*".repeat(
      Math.max(
        3,
        local.length -
          visible.length
      )
    )}@${domain}`
  );
}


export default function Register() {
  const [
    step,
    setStep,
  ] = useState<RegisterStep>(
    "details"
  );

  const [
    username,
    setUsername,
  ] = useState("");

  const [
    email,
    setEmail,
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
    code,
    setCode,
  ] = useState<string[]>(
    ["", "", "", "", "", ""]
  );

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


  async function submitDetails(
    event: FormEvent
  ) {
    event.preventDefault();

    setError(null);

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

    try {
      const result =
        await registerUser({
          username:
            username.trim(),
          email:
            email.trim(),
          password,
          confirm_password:
            confirmPassword,
        });

      setEmail(
        result.email
      );

      setCooldown(
        result.cooldown_seconds
        ?? 60
      );

      setCode(
        ["", "", "", "", "", ""]
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
          "Kayıt başlatılamadı. Lütfen bilgilerinizi kontrol edin."
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


  function handleCodeKeyDown(
    index: number,
    event: KeyboardEvent<HTMLInputElement>
  ) {
    if (
      event.key === "Backspace" &&
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

    if (value.length !== 6) {
      setError(
        "6 haneli doğrulama kodunu eksiksiz girin."
      );

      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      await verifyRegistrationCode(
        email,
        value
      );

      setPassword("");
      setConfirmPassword("");

      setStep(
        "success"
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
      submitting ||
      cooldown > 0
    ) {
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const result =
        await resendRegistrationCode(
          email
        );

      setCode(
        ["", "", "", "", "", ""]
      );

      setCooldown(
        result.cooldown_seconds
        ?? 60
      );

      codeRefs.current[0]
        ?.focus();
    } catch (requestError) {
      setError(
        getErrorMessage(
          requestError,
          "Yeni kod gönderilemedi."
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
              VERITAS çalışma alanınıza katılın.
            </h1>

            <p className="mt-5 max-w-md text-[13px] leading-6 text-[#95878d]">
              E-posta adresinizi doğrulayın,
              güvenli hesabınızı oluşturun ve
              kanıta dayalı analiz çalışma
              alanınıza erişin.
            </p>

            <div className="mt-10 space-y-3 text-[11px] text-[#a99ca1]">
              <div className="flex items-center gap-3 border-t border-white/[0.06] py-3">
                <Mail
                  size={15}
                  className="text-[#d26c48]"
                />

                6 haneli e-posta doğrulaması
              </div>

              <div className="flex items-center gap-3 border-t border-white/[0.06] py-3">
                <ShieldCheck
                  size={15}
                  className="text-[#d26c48]"
                />

                Güvenli viewer hesabı
              </div>
            </div>
          </div>

          <div className="border-t border-white/[0.06] px-10 py-5 text-[9px] uppercase tracking-[0.14em] text-[#665960] xl:px-14">
            VERITAS · Secure Registration
          </div>
        </section>


        <section className="flex min-h-screen items-center justify-center px-5 py-10 sm:px-8">
          <div className="w-full max-w-[430px]">

            {step !== "success" && (
              <Link
                to="/login"
                className="mb-7 inline-flex items-center gap-2 text-[11px] text-[#85777c] transition hover:text-[#b15e42]"
              >
                <ArrowLeft
                  size={14}
                />

                Giriş ekranına dön
              </Link>
            )}


            {step === "details" && (
              <>
                <div className="mb-7">
                  <div className="mb-3 flex items-center gap-2 text-[10px] font-medium uppercase tracking-[0.14em] text-[#a75a40]">
                    <ShieldCheck
                      size={13}
                    />

                    Güvenli kayıt
                  </div>

                  <h1 className="text-[27px] font-semibold tracking-[-0.035em]">
                    Hesabınızı oluşturun
                  </h1>

                  <p className="mt-2 text-[12px] leading-5 text-[#988b90]">
                    Bilgilerinizi girin.
                    Hesabınız e-posta
                    doğrulamasından sonra
                    oluşturulacaktır.
                  </p>
                </div>

                <form
                  onSubmit={
                    submitDetails
                  }
                  className="rounded-2xl border border-[#e2d9d5] bg-white p-7 shadow-[0_18px_55px_rgba(65,42,49,0.06)] dark:border-white/[0.08] dark:bg-[#1a1218]"
                >
                  <label
                    htmlFor="username"
                    className="mb-2 block text-[11px] font-medium text-[#66585d]"
                  >
                    Kullanıcı adı
                  </label>

                  <div className="relative">
                    <UserRound
                      size={15}
                      className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#a99ca1]"
                    />

                    <input
                      id="username"
                      type="text"
                      autoComplete="username"
                      value={username}
                      onChange={(event) =>
                        setUsername(
                          event.target.value
                        )
                      }
                      className="h-11 w-full rounded-lg border border-[#ded4d0] bg-[#fbfaf9] pl-10 pr-3 text-[12px] outline-none focus:border-[#c86038]/60 dark:border-white/[0.09] dark:bg-[#21171e]"
                      required
                    />
                  </div>


                  <label
                    htmlFor="email"
                    className="mb-2 mt-4 block text-[11px] font-medium text-[#66585d]"
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
                          event.target.value
                        )
                      }
                      className="h-11 w-full rounded-lg border border-[#ded4d0] bg-[#fbfaf9] pl-10 pr-3 text-[12px] outline-none focus:border-[#c86038]/60 dark:border-white/[0.09] dark:bg-[#21171e]"
                      required
                    />
                  </div>


                  <label
                    htmlFor="password"
                    className="mb-2 mt-4 block text-[11px] font-medium text-[#66585d]"
                  >
                    Şifre
                  </label>

                  <div className="relative">
                    <LockKeyhole
                      size={15}
                      className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#a99ca1]"
                    />

                    <input
                      id="password"
                      type={
                        showPassword
                          ? "text"
                          : "password"
                      }
                      autoComplete="new-password"
                      value={password}
                      onChange={(event) =>
                        setPassword(
                          event.target.value
                        )
                      }
                      minLength={8}
                      className="h-11 w-full rounded-lg border border-[#ded4d0] bg-[#fbfaf9] pl-10 pr-11 text-[12px] outline-none focus:border-[#c86038]/60 dark:border-white/[0.09] dark:bg-[#21171e]"
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
                      className="absolute right-3.5 top-1/2 -translate-y-1/2 text-[#9e9196]"
                    >
                      {showPassword ? (
                        <EyeOff size={15} />
                      ) : (
                        <Eye size={15} />
                      )}
                    </button>
                  </div>


                  <label
                    htmlFor="confirm-password"
                    className="mb-2 mt-4 block text-[11px] font-medium text-[#66585d]"
                  >
                    Şifre tekrar
                  </label>

                  <div className="relative">
                    <LockKeyhole
                      size={15}
                      className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#a99ca1]"
                    />

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
                      onChange={(event) =>
                        setConfirmPassword(
                          event.target.value
                        )
                      }
                      minLength={8}
                      className="h-11 w-full rounded-lg border border-[#ded4d0] bg-[#fbfaf9] pl-10 pr-3 text-[12px] outline-none focus:border-[#c86038]/60 dark:border-white/[0.09] dark:bg-[#21171e]"
                      required
                    />
                  </div>

                  <p className="mt-3 text-[9px] leading-4 text-[#9c8f94]">
                    Hesabınız viewer yetkisiyle
                    oluşturulur. Ek yetkiler
                    sistem yöneticisi tarafından
                    verilir.
                  </p>

                  {error && (
                    <div className="mt-5 rounded-lg border border-[#e9c9c3] bg-[#fff5f3] px-3.5 py-3 text-[11px] leading-5 text-[#a7483b]">
                      {error}
                    </div>
                  )}

                  <button
                    type="submit"
                    disabled={submitting}
                    className="mt-6 flex h-11 w-full items-center justify-center gap-2 rounded-lg bg-[#302529] text-[12px] font-medium text-white disabled:opacity-60 dark:bg-[#e86f45] dark:text-[#1a1014]"
                  >
                    {submitting
                      ? "Kod gönderiliyor..."
                      : "E-postayı doğrula"}

                    {!submitting && (
                      <ArrowRight size={15} />
                    )}
                  </button>

                  <div className="mt-5 border-t border-[#eee6e2] pt-5 text-center text-[10px] text-[#8e8085] dark:border-white/[0.06]">
                    Zaten hesabınız var mı?{" "}

                    <Link
                      to="/login"
                      className="font-medium text-[#a9573c] hover:underline"
                    >
                      Giriş yap
                    </Link>
                  </div>
                </form>
              </>
            )}


            {step === "code" && (
              <>
                <div className="mb-7">
                  <div className="mb-3 flex items-center gap-2 text-[10px] font-medium uppercase tracking-[0.14em] text-[#a75a40]">
                    <Mail size={13} />
                    E-posta doğrulama
                  </div>

                  <h1 className="text-[27px] font-semibold tracking-[-0.035em]">
                    Kodunuzu girin
                  </h1>

                  <p className="mt-2 text-[12px] leading-5 text-[#988b90]">
                    <span className="font-medium text-[#66585d]">
                      {maskEmail(email)}
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
                          key={index}
                          ref={(element) => {
                            codeRefs.current[
                              index
                            ] = element;
                          }}
                          value={digit}
                          onChange={(event) =>
                            changeCode(
                              index,
                              event.target.value
                            )
                          }
                          onKeyDown={(event) =>
                            handleCodeKeyDown(
                              index,
                              event
                            )
                          }
                          onPaste={(event) => {
                            event.preventDefault();

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
                          maxLength={1}
                          className="h-12 min-w-0 rounded-lg border border-[#ded4d0] bg-[#fbfaf9] text-center text-[17px] font-semibold outline-none focus:border-[#c86038]/70 dark:border-white/[0.09] dark:bg-[#21171e]"
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
                      code.join("")
                        .length !== 6
                    }
                    className="mt-6 flex h-11 w-full items-center justify-center gap-2 rounded-lg bg-[#302529] text-[12px] font-medium text-white disabled:opacity-45 dark:bg-[#e86f45] dark:text-[#1a1014]"
                  >
                    {submitting
                      ? "Doğrulanıyor..."
                      : "Kodu doğrula"}

                    {!submitting && (
                      <ArrowRight size={15} />
                    )}
                  </button>

                  <div className="mt-5 flex items-center justify-between border-t border-[#eee6e2] pt-5 dark:border-white/[0.06]">
                    <button
                      type="button"
                      onClick={() => {
                        setStep(
                          "details"
                        );

                        setError(
                          null
                        );
                      }}
                      className="text-[10px] text-[#8b7d82] hover:text-[#a9573c]"
                    >
                      Bilgileri değiştir
                    </button>

                    <button
                      type="button"
                      disabled={
                        cooldown > 0 ||
                        submitting
                      }
                      onClick={
                        resendCode
                      }
                      className="flex items-center gap-1.5 text-[10px] font-medium text-[#a9573c] disabled:text-[#aaa0a3]"
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


            {step === "success" && (
              <div className="rounded-2xl border border-[#e2d9d5] bg-white p-8 shadow-[0_18px_55px_rgba(65,42,49,0.06)] dark:border-white/[0.08] dark:bg-[#1a1218]">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl border border-[#d9e4dc] bg-[#f4faf6] text-[#52735c]">
                  <Check
                    size={20}
                  />
                </div>

                <h1 className="mt-6 text-[24px] font-semibold tracking-[-0.03em]">
                  E-posta doğrulandı
                </h1>

                <p className="mt-2 text-[12px] leading-5 text-[#8c7f84]">
                  VERITAS hesabınız başarıyla
                  oluşturuldu. Artık giriş
                  yapabilirsiniz.
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
