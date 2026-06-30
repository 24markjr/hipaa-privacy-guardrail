import api from "./api";

function _normalize(err) {
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

export async function analyzeNote(note, opts = {}) {
  try {
    const { data } = await api.post("/v1/analyze", { note, ...opts });
    return { ok: true, data };
  } catch (err) {
    return _normalize(err);
  }
}

export async function analyzeFile(file, opts = {}) {
  const form = new FormData();
  form.append("file", file);
  if (opts.provider) form.append("provider", opts.provider);
  if (opts.policy) form.append("policy", opts.policy);
  try {
    const { data } = await api.post("/v1/analyze/file", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return { ok: true, data };
  } catch (err) {
    return _normalize(err);
  }
}

export async function scan(text, policy) {
  const { data } = await api.post("/v1/scan", { text, policy });
  return data;
}

export async function fetchMeta() {
  const { data } = await api.get("/v1/meta");
  return data;
}

export async function fetchHistory(limit = 50) {
  const { data } = await api.get("/v1/history", { params: { limit } });
  return data.records || [];
}
