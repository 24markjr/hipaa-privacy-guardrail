import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Analyze from "./pages/Analyze";
import History from "./pages/History";
import Playground from "./pages/Playground";
import NotFound from "./pages/NotFound";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      {/* Authenticated area */}
      <Route element={<ProtectedRoute />}>
        <Route element={<Layout />}>
          <Route path="/analyze" element={<Analyze />} />
          <Route path="/history" element={<History />} />
          <Route path="/playground" element={<Playground />} />
        </Route>
      </Route>

      <Route path="/" element={<Navigate to="/analyze" replace />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
