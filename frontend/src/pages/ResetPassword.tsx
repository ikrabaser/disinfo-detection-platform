import {
  ArrowLeft,
  ArrowRight,
  KeyRound,
  ShieldCheck,
} from "lucide-react";

import {
  useState,
  type FormEvent,
} from "react";

import {
  Link,
  useSearchParams,
} from "react-router-dom";

import {
  confirmPasswordReset,
} from "../api/client";


export default function ResetPassword() {
  const [searchParams] =
    useSearchParams();

  const uid =
    searchParams.get("uid") ?? "";

  const token =
    searchParams.get("token") ?? "";

  const [
    password,
    setPassword,
  ] = useState("");

  const [
    confirmPassword,
    setConfirmPassword,
  ] = useState("");

  const [
    submitting,
    setSubmitting,
  ] = useState(false);

  const [
    success,
    setSuccess,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState<string | null>(
    null
  );


  async function handleSubmit(
    event: FormEvent
  ) {
    event.preventDefault();

    setError(null);

    if (!uid || !token) {
      setError(
        "Şifre sıfırlama bağlantısı geçersiz."
      );
      return;
    }

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
      await confirmPasswordReset({
        uid,
        token,
        new_password:
          password,
        confirm_password:
          confirmPassword,
      });

      setSuccess(true);
    } catch (requestError) {
      const fallback =
        "Şifre güncellenemedi. Bağlantının süresi dolmuş olabilir.";

      if (
        typeof requestError
        === "object" &&
        requestError !== null &&
        "response" in requestError
      ) {
        const response = (
          requestError as {
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
          setError(
            response.data
              .new_password
              .join(" ")
          );
        } else {
          setError(
            response?.data
              ?.detail ??
              fallback
          );
        }
      } else {
        setError(fallback);
      }
    } finally {
      setSubmitting(false);
    }
  }


  return (
    <div className="min-h-screen bg-[#f6f4f2] text-[#302529] dark:bg-[#120c12] dark:text-[#f8efec]">
      <div className="flex min-h-screen items-center justify-center px-5 py-10">
        <div className="w-full max-w-[420px]">
          <Link
            to="/login"
            className="mb-8 inline-flex items-center gap-2 text-[11px] text-[#85777c]"
          >
            <ArrowLeft size={14} />
            Giriş ekranına dön
          </Link>

          <div className="mb-8">
            <div className="mb-3 flex items-center gap-2 text-[10px] font-medium uppercase tracking-[0.14em] text-[#a75a40]">
              <ShieldCheck size={13} />
              Güvenli şifre yenileme
            </div>

            <h1 className="text-[27px] font-semibold tracking-[-0.035em]">
              Yeni şifrenizi belirleyin
            </h1>

            <p className="mt-2 text-[12px] leading-5 text-[#988b90]">
              Hesabınız için güçlü ve daha önce
              kullanmadığınız bir şifre seçin.
            </p>
          </div>

          <div className="rounded-2xl border border-[#e2d9d5] bg-white p-7 shadow-[0_18px_55px_rgba(65,42,49,0.06)] dark:border-white/[0.08] dark:bg-[#1a1218]">
            {success ? (
              <div>
                <div className="flex h-11 w-11 items-center justify-center rounded-xl border border-[#d9e4dc] bg-[#f4faf6] text-[#52735c]">
                  <ShieldCheck
                    size={19}
                  />
                </div>

                <h2 className="mt-5 text-lg font-semibold">
                  Şifreniz güncellendi
                </h2>

                <p className="mt-2 text-[12px] leading-5 text-[#8c7f84]">
                  Yeni şifrenizle VERITAS'a
                  giriş yapabilirsiniz.
                </p>

                <Link
                  to="/login"
                  className="mt-6 flex h-11 w-full items-center justify-center gap-2 rounded-lg bg-[#302529] text-[12px] font-medium text-white"
                >
                  Giriş yap
                  <ArrowRight
                    size={15}
                  />
                </Link>
              </div>
            ) : (
              <form
                onSubmit={
                  handleSubmit
                }
              >
                <label
                  htmlFor="password"
                  className="mb-2 block text-[11px] font-medium"
                >
                  Yeni şifre
                </label>

                <div className="relative">
                  <KeyRound
                    size={15}
                    className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#a99ca1]"
                  />

                  <input
                    id="password"
                    type="password"
                    autoComplete="new-password"
                    value={password}
                    onChange={(event) =>
                      setPassword(
                        event.target.value
                      )
                    }
                    className="h-11 w-full rounded-lg border border-[#ded4d0] bg-[#fbfaf9] pl-10 pr-3 text-[12px] outline-none focus:border-[#c86038]/60 dark:border-white/[0.09] dark:bg-[#21171e]"
                    required
                    minLength={8}
                  />
                </div>

                <label
                  htmlFor="confirm-password"
                  className="mb-2 mt-5 block text-[11px] font-medium"
                >
                  Yeni şifre tekrar
                </label>

                <input
                  id="confirm-password"
                  type="password"
                  autoComplete="new-password"
                  value={
                    confirmPassword
                  }
                  onChange={(event) =>
                    setConfirmPassword(
                      event.target.value
                    )
                  }
                  className="h-11 w-full rounded-lg border border-[#ded4d0] bg-[#fbfaf9] px-3 text-[12px] outline-none focus:border-[#c86038]/60 dark:border-white/[0.09] dark:bg-[#21171e]"
                  required
                  minLength={8}
                />

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
                    ? "Güncelleniyor..."
                    : "Şifreyi güncelle"}

                  {!submitting && (
                    <ArrowRight
                      size={15}
                    />
                  )}
                </button>
              </form>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
