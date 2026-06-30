// Small clinical UI primitives (clean, light theme).

export function Logo({ className = "" }) {
  return (
    <span className={`inline-flex items-center gap-2 font-bold text-slate-800 ${className}`}>
      <span className="text-teal-600 text-xl">🛡️</span>
      Privacy Guardrail
    </span>
  );
}

export function Card({ title, action, children, className = "" }) {
  return (
    <section className={`bg-white border border-slate-200 rounded-2xl shadow-sm ${className}`}>
      {(title || action) && (
        <header className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
          {title && <h2 className="font-semibold text-slate-800">{title}</h2>}
          {action}
        </header>
      )}
      <div className="p-6">{children}</div>
    </section>
  );
}

export function Button({ children, variant = "primary", className = "", ...props }) {
  const variants = {
    primary: "bg-teal-600 hover:bg-teal-700 text-white",
    ghost: "bg-transparent hover:bg-slate-100 text-slate-700",
    danger: "bg-rose-600 hover:bg-rose-700 text-white",
  };
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-lg px-5 py-2.5 font-semibold transition
        disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-teal-500/50
        ${variants[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}

export function Field({ label, ...props }) {
  return (
    <label className="block">
      <span className="block text-sm font-medium text-slate-600 mb-1">{label}</span>
      <input
        className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-slate-800
          focus:outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500"
        {...props}
      />
    </label>
  );
}

export function Spinner({ className = "" }) {
  return (
    <span
      className={`inline-block w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin ${className}`}
    />
  );
}

export function Badge({ children, tone = "slate" }) {
  const tones = {
    slate: "bg-slate-100 text-slate-700",
    teal: "bg-teal-50 text-teal-700 border border-teal-200",
    green: "bg-green-50 text-green-700",
    rose: "bg-rose-50 text-rose-700",
    amber: "bg-amber-50 text-amber-700",
  };
  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold ${tones[tone]}`}>
      {children}
    </span>
  );
}

export function ProtectedBadge() {
  return (
    <Badge tone="green">
      <span>🔒</span> PHI protected
    </Badge>
  );
}
