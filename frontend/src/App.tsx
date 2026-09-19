import { Link, Route, Routes } from "react-router-dom";

import AnalysisDetail from "./pages/AnalysisDetail";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";

function NavBar() {
  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <Link to="/" className="text-lg font-semibold text-brand-700">
          Dezenformasyon Tespit Platformu
        </Link>
        <nav className="flex gap-4 text-sm text-slate-600">
          <Link to="/" className="hover:text-brand-600">
            Panel
          </Link>
          <Link to="/login" className="hover:text-brand-600">
            Giris Yap
          </Link>
        </nav>
      </div>
    </header>
  );
}

export default function App() {
  return (
    <div className="min-h-screen">
      <NavBar />
      <main className="mx-auto max-w-6xl px-4 py-6">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/analyses/:analysisId" element={<AnalysisDetail />} />
          <Route path="/login" element={<Login />} />
        </Routes>
      </main>
    </div>
  );
}
