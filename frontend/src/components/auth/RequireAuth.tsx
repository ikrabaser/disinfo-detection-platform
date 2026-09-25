import {
  useEffect,
  useState,
  type ReactNode,
} from "react";

import {
  Navigate,
  useLocation,
} from "react-router-dom";

import {
  getMe,
} from "../../api/client";


interface RequireAuthProps {
  children: ReactNode;
}


export default function RequireAuth({
  children,
}: RequireAuthProps) {
  const location =
    useLocation();

  const [
    status,
    setStatus,
  ] = useState<
    | "checking"
    | "authenticated"
    | "unauthenticated"
  >("checking");


  useEffect(() => {
    let cancelled = false;

    getMe()
      .then(() => {
        if (!cancelled) {
          setStatus(
            "authenticated"
          );
        }
      })
      .catch(() => {
        if (!cancelled) {
          setStatus(
            "unauthenticated"
          );
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);


  if (status === "checking") {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <p className="text-sm text-[#8d7f84] dark:text-[#a99ca1]">
          Oturum kontrol ediliyor...
        </p>
      </div>
    );
  }


  if (
    status ===
    "unauthenticated"
  ) {
    return (
      <Navigate
        to="/login"
        replace
        state={{
          from:
            location.pathname +
            location.search,
        }}
      />
    );
  }


  return <>{children}</>;
}
