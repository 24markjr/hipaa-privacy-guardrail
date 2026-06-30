// JWT storage (separate from api.js to avoid an import cycle).
const KEY = "pg_token";

export const getToken = () => localStorage.getItem(KEY);
export const setToken = (t) => localStorage.setItem(KEY, t);
export const clearToken = () => localStorage.removeItem(KEY);
