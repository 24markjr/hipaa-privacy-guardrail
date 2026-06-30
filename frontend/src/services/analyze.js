import api from "./api";

// Returns { ok: true, data } on success, or { ok: false, blocked, reason, violations }
// when the gateway blocks the note (HTTP 422) so the UI can render it gracefully.
export async function analyzeNote(note) {
  try {
    const { data } = await api.post("/v1/analyze", { note });
    return { ok: true, data };
  } catch (err) {
    const res = err.response;
    if (res?.status === 422 && res.data?.blocked) {
      return {
        ok: false,
        blocked: true,
        reason: res.data.reason,
        violations: res.data.violations || [],
        injectionFlag: res.data.injectionFlag,
      };
    }
    throw err;
  }
}

export async function fetchHistory(limit = 50) {
  const { data } = await api.get("/v1/history", { params: { limit } });
  return data.records || [];
}
