import { Fragment, useEffect, useState } from "react";
import toast from "react-hot-toast";
import { fetchHistory } from "../services/analyze";
import { Badge, Card, Spinner } from "../components/ui";

function formatTime(iso) {
  if (!iso) return "—";
  return iso.replace("T", " ").slice(0, 16);
}

export default function History() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(null);

  useEffect(() => {
    let active = true;
    fetchHistory()
      .then((r) => active && setRows(r))
      .catch(() => toast.error("Could not load history"))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center py-20 text-teal-600">
        <Spinner className="w-8 h-8" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Analysis history</h1>
        <p className="text-slate-500 mt-1">
          De-identified records only — original notes are never stored.
        </p>
      </div>

      {rows.length === 0 ? (
        <Card>
          <div className="text-center py-12 text-slate-500">
            <div className="text-4xl mb-3">🗂️</div>
            No analyses yet. Run one from the Analyze tab.
          </div>
        </Card>
      ) : (
        <Card className="overflow-hidden" >
          <div className="overflow-x-auto -m-6">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-slate-500">
                <tr>
                  <th className="text-left font-medium px-6 py-3">Time</th>
                  <th className="text-left font-medium px-6 py-3">PII</th>
                  <th className="text-left font-medium px-6 py-3">Entities</th>
                  <th className="text-left font-medium px-6 py-3">Status</th>
                  <th className="text-right font-medium px-6 py-3">ms</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r, i) => (
                  <Fragment key={r.request_id || i}>
                    <tr
                      onClick={() => setOpen(open === i ? null : i)}
                      className="border-t border-slate-100 hover:bg-slate-50 cursor-pointer"
                    >
                      <td className="px-6 py-3 text-slate-600">{formatTime(r.created_at)}</td>
                      <td className="px-6 py-3">{r.pii_count}</td>
                      <td className="px-6 py-3 text-slate-600">
                        {(r.entity_types || []).join(", ") || "—"}
                      </td>
                      <td className="px-6 py-3">
                        {r.blocked ? (
                          <Badge tone="rose">blocked</Badge>
                        ) : (
                          <Badge tone="green">ok</Badge>
                        )}
                      </td>
                      <td className="px-6 py-3 text-right text-slate-600">
                        {Math.round(r.processing_ms)}
                      </td>
                    </tr>
                    {open === i && (
                      <tr className="bg-slate-50">
                        <td colSpan={5} className="px-6 py-4">
                          <div className="text-xs font-semibold text-slate-500 mb-1">
                            De-identified summary
                          </div>
                          <pre className="whitespace-pre-wrap text-sm text-slate-700">
                            {r.masked_summary || "(none)"}
                          </pre>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}
