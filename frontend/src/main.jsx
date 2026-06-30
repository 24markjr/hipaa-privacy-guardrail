import React from "react";
import ReactDOM from "react-dom/client";
import { Toaster } from "react-hot-toast";
import App from "./App";
import "./index.css";
import "@fontsource/inter";

ReactDOM.createRoot(
  document.getElementById("root")
).render(
  <React.StrictMode>

    <Toaster
      position="top-right"
      reverseOrder={false}
      toastOptions={{
        duration: 3000,

        style: {
          background: "#ffffff",
          color: "#0f172a",
          borderRadius: "12px",
          padding: "16px",
          fontSize: "14px",
          boxShadow:
            "0 10px 25px rgba(0,0,0,0.12)",
        },

        success: {
          iconTheme: {
            primary: "#22c55e",
            secondary: "#ffffff",
          },
        },

        error: {
          iconTheme: {
            primary: "#ef4444",
            secondary: "#ffffff",
          },
        },
      }}
    />

    <App />

  </React.StrictMode>
);