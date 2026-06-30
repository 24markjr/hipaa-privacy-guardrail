import { Link, useLocation, Outlet } from "react-router-dom";import {
  LayoutDashboard,
  Search,
  FileText,
  Workflow,
} from "lucide-react";

function Layout() {
  const location = useLocation();

  const linkClass = (path) =>
    `block px-3 py-2 rounded-lg transition ${
      location.pathname === path
        ? "bg-slate-800 text-sky-400 font-semibold"
        : "text-slate-300 hover:bg-slate-800"
    }`;

  return (
    <div className="min-h-screen flex">
      <aside className="w-72 bg-slate-850 bg-slate-900 text-white p-6">

        <div className="mb-10">
  <h1 className="text-2xl font-bold">
    HIPAA Privacy Guardrail
  </h1>

  <p className="text-slate-400 text-sm mt-1">
    Secure Clinical AI Gateway
  </p>
</div>

        <nav className="space-y-2">
         <Link
    className={linkClass("/")}
    to="/"
  >
    <div className="flex items-center gap-2">
      <LayoutDashboard size={18} />
      Dashboard
    </div>
  </Link>

  <Link
    className={linkClass("/analyze")}
    to="/analyze"
  >
    <div className="flex items-center gap-2">
      <Search size={18} />
      Analyze
    </div>
  </Link>

  <Link
    className={linkClass("/logs")}
    to="/logs"
  >
    <div className="flex items-center gap-2">
      <FileText size={18} />
      Audit Logs
    </div>
  </Link>

  <Link
    className={linkClass("/architecture")}
    to="/architecture"
  >
    <div className="flex items-center gap-2">
      <Workflow size={18} />
      Architecture
    </div>
  </Link> 
        </nav>
      </aside>

      <main className="flex-1 p-10">
        <Outlet />
      </main>
    </div>
  );
}

export default Layout;