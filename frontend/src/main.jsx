import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import App from "./App";
import { AuthProvider } from "./context/AuthContext";
import "./index.css";
import "@fontsource/inter";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 3000,
            style: {
              background: "#ffffff",
              color: "#0f172a",
              borderRadius: "12px",
              padding: "14px",
              fontSize: "14px",
              boxShadow: "0 10px 25px rgba(0,0,0,0.12)",
            },
            success: { iconTheme: { primary: "#0d9488", secondary: "#ffffff" } },
            error: { iconTheme: { primary: "#e11d48", secondary: "#ffffff" } },
          }}
        />
        <App />
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
);
