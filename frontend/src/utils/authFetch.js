// ✅ Centralized authenticated fetch utility
export const authFetch = async (url, options = {}, navigate) => {
  const token = localStorage.getItem("token");

  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  const response = await fetch(url, { ...options, headers });

  // If the token is invalid or expired, auto-logout
  if (response.status === 401) {
    console.warn("🔒 Token expired or invalid. Logging out...");
    localStorage.removeItem("token");
    if (navigate) navigate("/auth");
    return { success: false, message: "Session expired. Please log in again." };
  }

  return response;
};
