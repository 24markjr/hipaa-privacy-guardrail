import { useEffect, useRef, useState } from "react";
import toast from "react-hot-toast";
import { analyzeFile, analyzeNote, fetchMeta } from "../services/analyze";
import {
  Badge,
  Button,
  Card,
  LatencyTimeline,
  ProtectedBadge,
  Select,
  Spinner,
} from "../components/ui";

const SAMPLE =
  "Patient John Doe, DOB 12/05/1985, MRN12345, phone 415-555-0100, " +
  "email john@example.com. Complains of persistent cough and fever for 5 days.";

export default function Analyze() {
  const [note, setNote] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [blocked, setBlocked] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [showDetails, setShowDetails] = useState(false);
  const [meta, setMeta] = useState({ providers: [], policies: [] });
  const [provider, setProvider] = useState("");
  const [policy, setPolicy] = useState("");
  const fileInput = useRef(null);

  useEffect(() => {
    fetchMeta()
      .then((m) => {
        setMeta(m);
        setProvider(m.default_provider || m.providers?.[0] || "");
        setPolicy(m.default_policy || m.policies?.[0] || "");
      })
      .catch(() => {}); // selectors just won't show if meta unavailable
  }, []);

  const opts = () => ({ provider: provider || undefined, policy: policy || undefined });

  const applyResult = (res) => {
    if (res.ok) {
      setResult(res.data);
      setShowDetails(false);
      if (res.data.source?.startsWith("file:")) setNote(res.data.originalText || "");
    } else {
      setBlocked(res);
      toast.error("Blocked by compliance policy");
    }
  };

  const run = async () => {
    if (!note.trim()) return toast.error("Please enter a clinical note");
    setLoading(true);
    setResult(null);
    setBlocked(null);
    try {
      applyResult(await analyzeNote(note, opts()));
    } catch (err) {
      toast.error(err.response?.data?.detail || "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  const runFile = async (file) => {
    if (!file) return;
    setLoading(true);
    setResult(null);
    setBlocked(null);
    try {
      applyResult(await analyzeFile(file, opts()));
    } catch (err) {
      toast.error(err.response?.data?.detail || "Could not read or analyze file");
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
        {/* Provider + policy selectors */}
        {(meta.providers?.length > 1 || meta.policies?.length > 0) && (
          <div className="flex flex-wrap gap-4 mb-4">
            {/* Only show the provider selector when more than one is available. */}
            {meta.providers?.length > 1 && (
              <Select label="LLM provider" options={meta.providers} value={provider} onChange={setProvider} />
            )}
            {meta.policies?.length > 0 && (
              <Select label="Compliance profile" options={meta.policies} value={policy} onChange={setPolicy} />
            )}
          </div>
        )}

        <textarea
          rows={8}
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="Paste the clinical note here…"
          className="w-full rounded-lg border border-slate-300 p-4 text-slate-800 resize-y
            focus:outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500"
        />

        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragOver(false);
            runFile(e.dataTransfer.files?.[0]);
          }}
          onClick={() => fileInput.current?.click()}
          className={`mt-3 rounded-lg border-2 border-dashed p-4 text-center text-sm cursor-pointer transition
            ${dragOver ? "border-teal-500 bg-teal-50" : "border-slate-300 hover:border-teal-400 text-slate-500"}`}
        >
          📎 Drag &amp; drop a <strong>PDF, Word (.docx)</strong> or text file, or click to browse
          <input
            ref={fileInput}
            type="file"
            accept=".pdf,.docx,.txt,.md"
            className="hidden"
            onChange={(e) => {
              runFile(e.target.files?.[0]);
              e.target.value = "";
            }}
          />
        </div>

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
          <button onClick={() => setNote(SAMPLE)} className="text-sm text-slate-500 hover:text-teal-600">
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
          {/* Summary first */}
          <Card
            title="Clinical summary"
            action={<span className="text-xs text-slate-400">your data restored</span>}
          >
            <div className="whitespace-pre-wrap leading-7 text-slate-800">{result.finalSummary}</div>
          </Card>

          {result.suggestions && (
            <Card title="Suggestions for review">
              <div className="whitespace-pre-wrap leading-7 text-slate-800">{result.suggestions}</div>
              <p className="mt-4 pt-3 border-t border-slate-100 text-xs text-amber-700 bg-amber-50 rounded p-2">
                ⚠️ {result.disclaimer}
              </p>
            </Card>
          )}

          {/* The "backend working" — collapsed by default */}
          <Card>
            <button
              onClick={() => setShowDetails((s) => !s)}
              className="flex items-center gap-2 text-sm font-medium text-teal-700"
            >
              {showDetails ? "▾ Hide" : "▸ Show"} how it worked (masking &amp; pipeline)
              <Badge tone="teal">{result.piiCount} masked</Badge>
              <Badge tone="slate">{result.provider}</Badge>
              <Badge tone="slate">{result.policy || "default"}</Badge>
            </button>

            {showDetails && (
              <div className="mt-5 space-y-6">
                <div>
                  <h3 className="text-xs font-semibold uppercase text-slate-500 mb-2">What was protected</h3>
                  <div className="flex flex-wrap gap-2">
                    {result.entityTypes?.length ? (
                      result.entityTypes.map((t) => (
                        <Badge key={t} tone="teal">
                          {t}
                        </Badge>
                      ))
                    ) : (
                      <span className="text-slate-500 text-sm">No sensitive entities detected.</span>
                    )}
                    {result.injectionFlag && <Badge tone="amber">⚠️ injection flagged</Badge>}
                  </div>
                </div>

                <div>
                  <h3 className="text-xs font-semibold uppercase text-slate-500 mb-2">Latency breakdown</h3>
                  <LatencyTimeline timings={result.timings} />
                </div>

                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <h3 className="text-xs font-semibold uppercase text-slate-500 mb-2">Original</h3>
                    <pre className="whitespace-pre-wrap text-sm text-slate-700 leading-6 bg-slate-50 rounded p-3">
                      {result.originalText}
                    </pre>
                  </div>
                  <div>
                    <h3 className="text-xs font-semibold uppercase text-slate-500 mb-2">De-identified (sent to AI)</h3>
                    <pre className="whitespace-pre-wrap text-sm text-slate-700 leading-6 bg-slate-50 rounded p-3">
                      {result.maskedText}
                    </pre>
                  </div>
                </div>
              </div>
            )}
          </Card>
        </>
      )}
    </div>
  );
}
