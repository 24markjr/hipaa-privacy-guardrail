import { useState } from "react";
import api from "../services/api";
import Card from "../components/Card";
import ReactDiffViewer from "react-diff-viewer-continued";
import supabase from "../config/supabase";

function Analyze() {
  const [note, setNote] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  async function handleAnalyze() {
    if (!note.trim()) {
      alert("Please enter a clinical note.");
      return;
    }

    try {
      setLoading(true);

      const {
  data: { user },
} = await supabase.auth.getUser();

console.log("Logged in user:", user);
console.log("Sending userId:", user.id);

const response = await api.post("/analyze", {
  note,
  userId: user.id,
});

      setResult(response.data);
    } catch (error) {
      console.error(error);

      alert(
        error.response?.data?.message ||
          "Analysis failed."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="w-full">

      {/* Header */}

      <div className="mb-8">
        <h1 className="text-4xl font-bold">
          Analyze Clinical Note
        </h1>

        <p className="text-slate-500 mt-2">
          Paste a clinical note below to
          automatically remove PII and
          generate a privacy-safe AI summary.
        </p>
      </div>

      {/* Input */}

      <Card title="Patient Note">

        <textarea
          rows="12"
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="Paste patient note here..."
          className="w-full border rounded-lg p-4 focus:outline-none focus:ring-2 focus:ring-sky-500 resize-none"
        />

        <button
          onClick={handleAnalyze}
          disabled={loading}
          className="mt-5 bg-sky-500 hover:bg-sky-600 disabled:bg-sky-300 text-white px-6 py-3 rounded-lg font-semibold transition flex items-center gap-2"
        >
          {loading ? (
            <>
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>

              Analyzing...
            </>
          ) : (
            "Analyze Note"
          )}
        </button>

      </Card>

      {/* Empty State */}

      {!result && (

        <Card title="Ready to Analyze">

          <div className="text-center py-16">

            <div className="text-6xl mb-4">
              📄
            </div>

            <h2 className="text-2xl font-bold">
              No Analysis Yet
            </h2>

            <p className="text-slate-500 mt-3">
              Paste a clinical note above and
              click <strong>Analyze Note</strong>
              {" "}to generate a privacy-safe
              summary.
            </p>

          </div>

        </Card>

      )}

      {/* Results */}

      {result && (
        <>

          <div className="mt-8">

            <Card title="PII Redaction Comparison">

              <ReactDiffViewer
                oldValue={result.originalText}
                newValue={result.maskedText}
                splitView
              />

            </Card>

          </div>

          <div className="mt-8">

            <Card title="Clinical Summary">

              <div className="whitespace-pre-wrap leading-7 text-slate-700">
                {result.finalSummary}
              </div>

            </Card>

          </div>

          <div className="mt-8">

            <Card title="Analysis Metrics">

              <div className="grid md:grid-cols-2 gap-6">

                <div className="bg-sky-50 rounded-xl p-6 border">

                  <p className="text-slate-500">
                    PII Elements Removed
                  </p>

                  <h2 className="text-4xl font-bold text-sky-600 mt-2">
                    {result.piiCount}
                  </h2>

                </div>

                <div className="bg-green-50 rounded-xl p-6 border">

                  <p className="text-slate-500">
                    Processing Status
                  </p>

                  <h2 className="text-4xl font-bold text-green-600 mt-2">
                    Success
                  </h2>

                </div>

              </div>

            </Card>

          </div>

        </>
      )}

    </div>
  );
}

export default Analyze;