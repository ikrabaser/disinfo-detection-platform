import { Route, Routes } from "react-router-dom";

import Sidebar from "./components/layout/Sidebar";
import TopBar from "./components/layout/TopBar";
import AnalysisDetail from "./pages/AnalysisDetail";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";

export default function App() {
  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />

      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar />

        <main className="flex-1 overflow-y-auto px-5 py-6 lg:px-7 xl:px-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route
              path="/analyses/:analysisId"
              element={<AnalysisDetail />}
            />
            <Route path="/login" element={<Login />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}
