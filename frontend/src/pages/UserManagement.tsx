import {
  AlertCircle,
  CheckCircle2,
  ShieldCheck,
  Users,
} from "lucide-react";

import {
  useEffect,
  useState,
} from "react";

import {
  getMe,
  getUsers,
  updateUserRole,
  type User,
} from "../api/client";


type Role =
  User["role"];


const ROLE_LABELS: Record<
  Role,
  string
> = {
  admin: "Admin",
  analyst: "Analyst",
  viewer: "Viewer",
};


const ROLE_DESCRIPTIONS: Record<
  Role,
  string
> = {
  admin:
    "Tam platform ve kullanıcı yönetimi erişimi",
  analyst:
    "Analiz oluşturma ve çalıştırma yetkisi",
  viewer:
    "Salt okunur görüntüleme erişimi",
};


function formatDate(
  value: string
): string {
  if (!value) {
    return "—";
  }

  return new Intl.DateTimeFormat(
    "tr-TR",
    {
      day: "2-digit",
      month: "short",
      year: "numeric",
    }
  ).format(
    new Date(value)
  );
}


export default function UserManagement() {
  const [
    currentUser,
    setCurrentUser,
  ] = useState<User | null>(
    null
  );

  const [
    users,
    setUsers,
  ] = useState<User[]>([]);

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    forbidden,
    setForbidden,
  ] = useState(false);

  const [
    savingId,
    setSavingId,
  ] = useState<number | null>(
    null
  );

  const [
    error,
    setError,
  ] = useState<string | null>(
    null
  );

  const [
    success,
    setSuccess,
  ] = useState<string | null>(
    null
  );


  useEffect(() => {
    let mounted = true;

    async function load() {
      try {
        const me =
          await getMe();

        if (!mounted) {
          return;
        }

        setCurrentUser(me);

        if (
          me.role !== "admin"
        ) {
          setForbidden(true);
          return;
        }

        const userList =
          await getUsers();

        if (mounted) {
          setUsers(
            userList
          );
        }
      } catch {
        if (mounted) {
          setError(
            "Kullanıcı yönetimi verileri yüklenemedi."
          );
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    void load();

    return () => {
      mounted = false;
    };
  }, []);


  async function handleRoleChange(
    user: User,
    nextRole: Role
  ) {
    if (
      currentUser?.id ===
      user.id
    ) {
      return;
    }

    if (
      user.role === nextRole
    ) {
      return;
    }

    setSavingId(
      user.id
    );

    setError(null);
    setSuccess(null);

    try {
      const updated =
        await updateUserRole(
          user.id,
          nextRole
        );

      setUsers(
        (current) =>
          current.map(
            (item) =>
              item.id ===
              updated.id
                ? updated
                : item
          )
      );

      setSuccess(
        `${updated.username} kullanıcısının rolü ${ROLE_LABELS[updated.role]} olarak güncellendi.`
      );
    } catch {
      setError(
        "Kullanıcı rolü güncellenemedi."
      );
    } finally {
      setSavingId(
        null
      );
    }
  }


  if (loading) {
    return (
      <div className="flex min-h-[480px] items-center justify-center">
        <div className="text-center">
          <div className="mx-auto h-7 w-7 animate-spin rounded-full border-2 border-[#e5d9d4] border-t-[#c86038]" />

          <p className="mt-4 text-xs text-[#918489]">
            Kullanıcılar yükleniyor...
          </p>
        </div>
      </div>
    );
  }


  if (forbidden) {
    return (
      <div className="mx-auto mt-12 max-w-xl rounded-2xl border border-[#e7dedb] bg-white p-8 shadow-[0_16px_45px_rgba(50,35,41,0.04)] dark:border-white/[0.07] dark:bg-[#191116]">
        <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-[#fff1ea] text-[#b85434] dark:bg-[#ff895d]/[0.09] dark:text-[#ff956e]">
          <AlertCircle
            size={20}
          />
        </div>

        <h1 className="mt-5 text-xl font-semibold tracking-[-0.02em]">
          Yetkisiz erişim
        </h1>

        <p className="mt-2 text-sm leading-6 text-[#918489]">
          Kullanıcı yönetimi yalnızca
          admin rolündeki VERITAS
          hesapları tarafından kullanılabilir.
        </p>
      </div>
    );
  }


  return (
    <div className="mx-auto max-w-6xl">

      <div className="mb-8 flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
        <div>
          <div className="mb-3 flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-[#b25b3d]">
            <ShieldCheck
              size={13}
            />

            Yönetim
          </div>

          <h1 className="text-[30px] font-semibold tracking-[-0.035em] text-[#2d2327] dark:text-[#fff7f4]">
            Kullanıcı Yönetimi
          </h1>

          <p className="mt-2 max-w-2xl text-[13px] leading-6 text-[#918489] dark:text-[#8d7f85]">
            Platform kullanıcılarını
            görüntüleyin ve VERITAS
            erişim rollerini yönetin.
          </p>
        </div>

        <div className="flex items-center gap-2 rounded-xl border border-[#e7dedb] bg-white px-4 py-2.5 text-xs text-[#776a6f] shadow-sm dark:border-white/[0.07] dark:bg-white/[0.025] dark:text-[#aa9ca1]">
          <Users
            size={15}
          />

          <span>
            {users.length} kullanıcı
          </span>
        </div>
      </div>


      {error && (
        <div className="mb-5 flex items-center gap-2 rounded-xl border border-[#eccbc4] bg-[#fff5f2] px-4 py-3 text-xs text-[#a84d3d]">
          <AlertCircle
            size={14}
          />

          {error}
        </div>
      )}


      {success && (
        <div className="mb-5 flex items-center gap-2 rounded-xl border border-[#dce8df] bg-[#f5faf6] px-4 py-3 text-xs text-[#52705b]">
          <CheckCircle2
            size={14}
          />

          {success}
        </div>
      )}


      <div className="overflow-hidden rounded-2xl border border-[#e5ddda] bg-white shadow-[0_18px_55px_rgba(55,39,46,0.045)] dark:border-white/[0.07] dark:bg-[#191116]">

        <div className="hidden grid-cols-[1.25fr_1.7fr_1fr_0.75fr_0.9fr] gap-5 border-b border-[#eee7e4] bg-[#faf8f7] px-6 py-3.5 text-[9px] font-semibold uppercase tracking-[0.15em] text-[#a09398] md:grid dark:border-white/[0.06] dark:bg-white/[0.018]">
          <span>Kullanıcı</span>
          <span>E-posta</span>
          <span>Rol</span>
          <span>Durum</span>
          <span>Kayıt</span>
        </div>


        {users.map(
          (user) => {
            const isSelf =
              currentUser?.id ===
              user.id;

            return (
              <div
                key={user.id}
                className="grid gap-4 border-b border-[#f0e9e6] px-5 py-5 last:border-b-0 md:grid-cols-[1.25fr_1.7fr_1fr_0.75fr_0.9fr] md:items-center md:gap-5 md:px-6 dark:border-white/[0.05]"
              >

                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="truncate text-[13px] font-semibold text-[#382c31] dark:text-[#f4eaed]">
                      {user.username}
                    </span>

                    {isSelf && (
                      <span className="rounded-md bg-[#fff0e7] px-1.5 py-0.5 text-[8px] font-semibold uppercase tracking-[0.08em] text-[#ad4d2f] dark:bg-[#ff895d]/[0.10] dark:text-[#ff9872]">
                        Siz
                      </span>
                    )}
                  </div>

                  <p className="mt-1 text-[9px] text-[#aaa0a3]">
                    ID #{user.id}
                  </p>
                </div>


                <div className="min-w-0">
                  <p className="truncate text-[11px] text-[#74676c] dark:text-[#a99ba0]">
                    {user.email || "—"}
                  </p>
                </div>


                <div>
                  <select
                    value={user.role}
                    disabled={
                      isSelf ||
                      savingId ===
                        user.id
                    }
                    title={
                      isSelf
                        ? "Kendi rolünüzü değiştiremezsiniz."
                        : ROLE_DESCRIPTIONS[user.role]
                    }
                    onChange={(event) =>
                      void handleRoleChange(
                        user,
                        event.target
                          .value as Role
                      )
                    }
                    className="h-9 w-full max-w-[135px] rounded-lg border border-[#ded5d1] bg-[#fbfaf9] px-3 text-[11px] font-medium text-[#55484d] outline-none transition focus:border-[#c86038]/60 focus:ring-2 focus:ring-[#c86038]/[0.06] disabled:cursor-not-allowed disabled:opacity-50 dark:border-white/[0.08] dark:bg-[#21171e] dark:text-[#d9cdd1]"
                  >
                    <option value="viewer">
                      Viewer
                    </option>

                    <option value="analyst">
                      Analyst
                    </option>

                    <option value="admin">
                      Admin
                    </option>
                  </select>
                </div>


                <div>
                  <span
                    className={[
                      "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[9px] font-semibold",
                      user.is_active
                        ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-400/[0.08] dark:text-emerald-300"
                        : "bg-neutral-100 text-neutral-500 dark:bg-white/[0.05] dark:text-[#8d8085]",
                    ].join(" ")}
                  >
                    <span
                      className={[
                        "h-1.5 w-1.5 rounded-full",
                        user.is_active
                          ? "bg-emerald-500"
                          : "bg-neutral-400",
                      ].join(" ")}
                    />

                    {user.is_active
                      ? "Aktif"
                      : "Pasif"}
                  </span>
                </div>


                <div className="text-[10px] text-[#95888d] dark:text-[#7e7076]">
                  {formatDate(
                    user.date_joined
                  )}
                </div>

              </div>
            );
          }
        )}

      </div>


      <div className="mt-5 rounded-xl border border-[#ebe3df] bg-[#faf8f7] px-4 py-3 text-[10px] leading-5 text-[#94878c] dark:border-white/[0.055] dark:bg-white/[0.018]">
        Güvenlik nedeniyle oturum açmış
        admin kendi rolünü bu ekrandan
        değiştiremez. Rol değişiklikleri
        backend tarafından ayrıca
        doğrulanır.
      </div>

    </div>
  );
}
