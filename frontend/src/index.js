import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import "./index.css";
import LandingPage from "./components/LandingPage";
import RecommendPage from "./components/RecommendPage"; // you’ll create this file next

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <Router>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/recommend" element={<RecommendPage />} />
      </Routes>
    </Router>
  </React.StrictMode>
);
