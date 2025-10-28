// src/utils/api.js
import { getToken } from "./auth";

export async function apiFetch(path, options = {}) {
  const BACKEND = process.env.REACT_APP_BACKEND_URL || "http://127.0.0.1:5000";
  const token = getToken();
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(BACKEND + path, { ...options, headers });
  const text = await res.text();
  // try parse json
  let data;
  try { data = text ? JSON.parse(text) : {}; } catch (e) { data = { raw: text }; }
  if (!res.ok) {
    const err = new Error(data.message || res.statusText || "API error");
    err.response = res;
    err.data = data;
    throw err;
  }
  return data;
}
