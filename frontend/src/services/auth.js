import api from "./api";
import { clearToken, setToken } from "./token";

export async function register({ email, password, name }) {
  const { data } = await api.post("/v1/auth/register", { email, password, name });
  setToken(data.access_token);
  return data.user;
}

export async function login({ email, password }) {
  const { data } = await api.post("/v1/auth/login", { email, password });
  setToken(data.access_token);
  return data.user;
}

export async function fetchMe() {
  const { data } = await api.get("/v1/auth/me");
  return data;
}

export function logout() {
  clearToken();
}
