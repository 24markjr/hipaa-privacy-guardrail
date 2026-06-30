import { Navigate } from "react-router-dom";
import { useEffect, useState } from "react";
import supabase from "../config/supabase";

export default function ProtectedRoute({ children }) {
  const [loading, setLoading] = useState(true);
  const [session, setSession] = useState(null);

  useEffect(() => {
    async function checkSession() {
      try {
        const {
          data: { session },
        } = await supabase.auth.getSession();

        setSession(session);
      } catch (error) {
        console.error("Session Error:", error);
      } finally {
        setLoading(false);
      }
    }

    checkSession();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50">

        <div className="w-16 h-16 border-4 border-sky-500 border-t-transparent rounded-full animate-spin"></div>

        <h2 className="mt-6 text-2xl font-bold text-slate-800">
          HIPAA Privacy Guardrail
        </h2>

        <p className="mt-2 text-slate-500">
          Checking authentication...
        </p>

      </div>
    );
  }

  if (!session) {
    return <Navigate to="/login" replace />;
  }

  return children;
}