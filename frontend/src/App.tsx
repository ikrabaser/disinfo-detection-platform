import {
  Route,
  Routes,
  useLocation,
} from "react-router-dom";

import RequireAuth from "./components/auth/RequireAuth";
import Sidebar from "./components/layout/Sidebar";
import TopBar from "./components/layout/TopBar";

import AnalysisDetail from "./pages/AnalysisDetail";
import Assistant from "./pages/Assistant";
import Dashboard from "./pages/Dashboard";
import ForgotPassword from "./pages/ForgotPassword";
import Login from "./pages/Login";
import ResetPassword from "./pages/ResetPassword";


export default function App() {
  const location = useLocation();

  const isAuthPage = [
    "/login",
    "/forgot-password",
    "/reset-password",
  ].includes(
    location.pathname
  );

  if (isAuthPage) {
    return (
      <Routes>
        <Route
          path="/login"
          element={<Login />}
        />

        <Route
          path="/forgot-password"
          element={
            <ForgotPassword />
          }
        />

        <Route
          path="/reset-password"
          element={
            <ResetPassword />
          }
        />
      </Routes>
    );
  }

  return (
    <div className="flex min-h-screen bg-[#f6f4f2] text-[#241c1f] dark:bg-[#120c12] dark:text-[#fff8f5]">
      <Sidebar />

      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar />

        <main className="relative flex-1 overflow-y-auto">
          <div className="pointer-events-none absolute inset-x-0 top-0 hidden h-[320px] overflow-hidden dark:block">
            <div className="absolute -right-24 -top-56 h-[430px] w-[620px] rotate-[20deg] rounded-full bg-[#e85f32]/[0.055] blur-3xl" />
            <div className="absolute left-[18%] top-[-220px] h-[390px] w-[500px] rounded-full bg-[#8b315b]/[0.04] blur-3xl" />
          </div>

          <div className="relative px-5 py-7 lg:px-8 xl:px-10">
            <Routes>
              <Route
                path="/"
                element={
                  <RequireAuth>
                    <Dashboard />
                  </RequireAuth>
                }
              />

              <Route
                path="/analyses/:analysisId"
                element={
                  <RequireAuth>
                    <AnalysisDetail />
                  </RequireAuth>
                }
              />

              <Route
                path="/assistant"
                element={
                  <RequireAuth>
                    <Assistant />
                  </RequireAuth>
                }
              />
            </Routes>
          </div>
        </main>
      </div>
    </div>
  );
}
