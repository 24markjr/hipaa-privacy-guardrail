import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-slate-100 text-center px-4">
      <h1 className="text-5xl font-bold text-slate-300">404</h1>
      <p className="text-slate-500 mt-2">Page not found.</p>
      <Link to="/analyze" className="text-teal-600 font-medium mt-4 hover:underline">
        Go to Analyze
      </Link>
    </div>
  );
}
