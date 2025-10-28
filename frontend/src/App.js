import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import LandingPage from "./components/LandingPage";
import RecommendPage from "./components/RecommendPage";
import AuthPage from "./components/AuthPage"; // ✅ new auth page
import FavoritesPage from "./components/FavoritesPage"; // 
import Personalized from "./components/Personalized";
function App() {
  return (
    <Router>
      <Routes>
        {/* 🏠 Landing Page */}
        <Route path="/" element={<LandingPage />} />

        {/* 🔐 Login / Register */}
        <Route path="/auth" element={<AuthPage />} />

        {/* 🎬 Recommendation Page */}
        <Route path="/recommend" element={<RecommendPage />} />

        {/* ✨ Fallback route */}
        <Route path="*" element={<h1 style={{ color: "white", textAlign: "center", marginTop: "20%" }}>404 — Page Not Found</h1>} />
         <Route path="/favorites" element={<FavoritesPage />} />
         <Route path="/personalized" element={<Personalized />} />
      </Routes>
    </Router>
  );
}

export default App;
