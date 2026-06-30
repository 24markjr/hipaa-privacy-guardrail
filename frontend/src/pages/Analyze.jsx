import { useState } from "react";
import toast from "react-hot-toast";
import { analyzeNote } from "../services/analyze";
import { Badge, Button, Card, ProtectedBadge, Spinner } from "../components/ui";

const SAMPLE =
  "Patient John Doe, DOB 12/05/1985, MRN12345, phone 415-555-0100, " +
  "email john@example.com. Complains of persistent cough and fever for 5 days.";

export default function Analyze() {
  const [note, setNote] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [blocked, setBlocked] = useState(null);

  const run = async () => {
    if (!note.trim()) {
      toast.error("Please enter a clinical note");
      return;
    }
    setLoading(true);
    setResult(null);
    setBlocked(null);
    try {
      const res = await analyzeNote(note);
      if (res.ok) {
        setResult(res.data);
      } else {
        setBlocked(res);
        toast.error("Note blocked by compliance policy");
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Analyze clinical note</h1>
        <p className="text-slate-500 mt-1">
          PII/PHI is detected and masked before anything is sent to the AI, then restored in your summary.
        </p>
      </div>

      <Card title="Patient note" action={<ProtectedBadge />}>
        <textarea
          rows={8}
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="Paste the clinical note here…"
          className="w-full rounded-lg border border-slate-300 p-4 text-slate-800 resize-y
            focus:outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500"
        />
        <div className="flex items-center gap-3 mt-4">
          <Button onClick={run} disabled={loading}>
            {loading ? (
              <>
                <Spinner /> Analyzing…
              </>
            ) : (
              "Analyze note"
            )}
          </Button>
          <button
            onClick={() => setNote(SAMPLE)}
            className="text-sm text-slate-500 hover:text-teal-600"
          >
            Use sample note
          </button>
        </div>
      </Card>

      {blocked && (
        <Card className="border-rose-200">
          <div className="flex items-start gap-3">
            <span className="text-2xl">⛔</span>
            <div>
              <h2 className="font-semibold text-rose-700">Blocked before reaching the AI</h2>
              <p className="text-slate-600 mt-1">{blocked.reason}</p>
              {blocked.violations?.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-3">
                  {blocked.violations.map((v) => (
                    <Badge key={v} tone="rose">
                      {v}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          </div>
        </Card>
      )}

      {result && (
        <>
          <Card
            title="What was protected"
            action={<Badge tone="teal">{result.piiCount} item(s) masked</Badge>}
          >
            {result.entityTypes?.length ? (
              <div className="flex flex-wrap gap-2">
                {result.entityTypes.map((t) => (
                  <Badge key={t} tone="teal">
                    {t}
                  </Badge>
                ))}
              </div>
            ) : (
              <p className="text-slate-500">No sensitive entities detected.</p>
            )}
            {result.injectionFlag && (
              <div className="mt-3">
                <Badge tone="amber">⚠️ prompt-injection patterns flagged</Badge>
              </div>
            )}
          </Card>

          <div className="grid md:grid-cols-2 gap-6">
            <Card title="Original note">
              <pre className="whitespace-pre-wrap text-sm text-slate-700 leading-6">
                {result.originalText}
              </pre>
            </Card>
            <Card title="De-identified (sent to AI)">
              <pre className="whitespace-pre-wrap text-sm text-slate-700 leading-6">
                {result.maskedText}
              </pre>
            </Card>
          </div>

          <Card
            title="Clinical summary"
            action={<span className="text-xs text-slate-400">your data restored</span>}
          >
            <div className="whitespace-pre-wrap leading-7 text-slate-800">
              {result.finalSummary}
            </div>
            <div className="mt-4 pt-4 border-t border-slate-100 text-sm text-slate-500">
              Provider: <span className="font-medium text-slate-700">{result.provider}</span>
            </div>
          </Card>
        </>
      )}
    </div>
  );
}
