import React, { createContext, useContext, useState, useEffect } from "react";
import { getToken, getUser, saveAuth, clearAuth } from "../utils/auth";

const UserContext = createContext();

export function UserProvider({ children }) {
  const [user, setUser] = useState(() => getUser());
  const [token, setToken] = useState(() => getToken());
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // If needed, you can validate token here by calling backend /me
  }, []);

  const login = (tokenValue, userObj) => {
    saveAuth(tokenValue, userObj);
    setToken(tokenValue);
    setUser(userObj);
  };

  const logout = () => {
    clearAuth();
    setToken(null);
    setUser(null);
  };

  return (
    <UserContext.Provider value={{ user, token, login, logout, loading, setLoading }}>
      {children}
    </UserContext.Provider>
  );
}

export function useAuth() {
  return useContext(UserContext);
}
