import { NavLink, Outlet, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { useAuth } from "../context/AuthContext";
import { Logo } from "./ui";

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    toast.success("Signed out");
    navigate("/login");
  };

  const linkClass = ({ isActive }) =>
    `px-3 py-2 rounded-lg text-sm font-medium transition ${
      isActive ? "bg-teal-50 text-teal-700" : "text-slate-600 hover:bg-slate-100"
    }`;

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-6 h-16 flex items-center gap-6">
          <Logo />
          <nav className="flex items-center gap-1">
            <NavLink to="/analyze" className={linkClass}>
              Analyze
            </NavLink>
            <NavLink to="/history" className={linkClass}>
              History
            </NavLink>
          </nav>
          <div className="ml-auto flex items-center gap-3">
            <span className="text-sm text-slate-500 hidden sm:inline">
              {user?.name || user?.email}
            </span>
            <button
              onClick={handleLogout}
              className="text-sm font-medium text-slate-600 hover:text-rose-600 transition"
            >
              Sign out
            </button>
          </div>
        </div>
      </header>

      <main className="flex-1 w-full max-w-5xl mx-auto px-6 py-8">
        <Outlet />
      </main>

      <footer className="text-center text-xs text-slate-400 py-6">
        Clinical notes are de-identified before any AI processing · PHI never leaves your boundary
      </footer>
    </div>
  );
}
