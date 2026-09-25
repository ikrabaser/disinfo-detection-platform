import {
  ArrowLeft,
  ArrowRight,
  Mail,
  ShieldCheck,
} from "lucide-react";

import {
  useState,
  type FormEvent,
} from "react";

import {
  Link,
} from "react-router-dom";

import {
  requestPasswordReset,
} from "../api/client";


export default function ForgotPassword() {
  const [
    email,
    setEmail,
  ] = useState("");

  const [
    submitting,
    setSubmitting,
  ] = useState(false);

  const [
    message,
    setMessage,
  ] = useState<string | null>(
    null
  );

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

    setSubmitting(true);
    setError(null);
    setMessage(null);

    try {
      const result =
        await requestPasswordReset(
          email
        );

      setMessage(
        result.detail
      );
    } catch {
      setError(
        "İstek tamamlanamadı. Lütfen tekrar deneyin."
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
              Kayıtlı e-posta adresinizi girin.
              Hesabınız varsa güvenli bir şifre
              sıfırlama bağlantısı göndereceğiz.
            </p>
          </div>

          <div className="border-t border-white/[0.06] px-10 py-5 text-[9px] uppercase tracking-[0.14em] text-[#665960] xl:px-14">
            VERITAS · Secure account recovery
          </div>
        </section>


        <section className="flex min-h-screen items-center justify-center px-5 py-10 sm:px-8">
          <div className="w-full max-w-[420px]">
            <Link
              to="/login"
              className="mb-8 inline-flex items-center gap-2 text-[11px] text-[#85777c] transition hover:text-[#b15e42]"
            >
              <ArrowLeft size={14} />
              Giriş ekranına dön
            </Link>

            <div className="mb-8">
              <div className="mb-3 flex items-center gap-2 text-[10px] font-medium uppercase tracking-[0.14em] text-[#a75a40]">
                <ShieldCheck size={13} />
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
              onSubmit={handleSubmit}
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
                      event.target.value
                    )
                  }
                  placeholder="ornek@veritas.com"
                  className="h-11 w-full rounded-lg border border-[#ded4d0] bg-[#fbfaf9] pl-10 pr-3 text-[12px] outline-none transition focus:border-[#c86038]/60 focus:ring-2 focus:ring-[#c86038]/[0.06] dark:border-white/[0.09] dark:bg-[#21171e]"
                  required
                />
              </div>

              {message && (
                <div className="mt-5 rounded-lg border border-[#d9e4dc] bg-[#f4faf6] px-3.5 py-3 text-[11px] leading-5 text-[#4d7057]">
                  {message}
                </div>
              )}

              {error && (
                <div className="mt-5 rounded-lg border border-[#e9c9c3] bg-[#fff5f3] px-3.5 py-3 text-[11px] text-[#a7483b]">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={submitting}
                className="mt-6 flex h-11 w-full items-center justify-center gap-2 rounded-lg bg-[#302529] px-4 text-[12px] font-medium text-white transition hover:bg-[#44363b] disabled:opacity-60 dark:bg-[#e86f45] dark:text-[#1a1014]"
              >
                {submitting
                  ? "Gönderiliyor..."
                  : "Sıfırlama bağlantısı gönder"}

                {!submitting && (
                  <ArrowRight
                    size={15}
                  />
                )}
              </button>
            </form>
          </div>
        </section>
      </div>
    </div>
  );
}
