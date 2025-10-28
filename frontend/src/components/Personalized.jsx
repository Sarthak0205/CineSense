import React, { useEffect, useState, useCallback, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { authFetch } from "../utils/authFetch";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

const serverBaseURL =
  process.env.REACT_APP_BACKEND_URL || "http://127.0.0.1:5000";

const getFallbackPoster = (category) => "/posters/default.png";

export default function Personalized() {
  const [sections, setSections] = useState({
    movies: [],
    series: [],
    anime: [],
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const token = localStorage.getItem("token");
  const isLoggedIn = !!token;

  const visualizationRef = useRef(null);

  const fetchPosterFromBackend = useCallback(async (title, type) => {
    try {
      const res = await fetch(
        `${serverBaseURL}/api/poster/${encodeURIComponent(title)}?type=${type}`
      );
      const data = await res.json();
      return data.poster || null;
    } catch {
      return null;
    }
  }, []);

  // 🔹 Fetch all categories
  const fetchAllPersonalized = useCallback(async () => {
    if (!isLoggedIn) return navigate("/auth");
    setLoading(true);
    setError("");

    try {
      const endpoints = ["movies", "series", "anime"];
      const results = await Promise.all(
        endpoints.map((cat) =>
          authFetch(`${serverBaseURL}/api/personalized/${cat}`, { method: "GET" }, navigate)
        )
      );

      const jsonData = await Promise.all(results.map((r) => r.json()));
      const updatedSections = {};

      for (let i = 0; i < endpoints.length; i++) {
        const cat = endpoints[i];
        const data = jsonData[i];
        if (data.success && Array.isArray(data.results)) {
          const processed = data.results.map((r) => ({
            ...r,
            type: r.type || cat,
            match_percent:
              r.match_percent || Math.round((r.similarity || 0) * 100) || 70,
            poster: r.poster || r.poster_url || getFallbackPoster(cat),
          }));
          updatedSections[cat] = processed;
        } else {
          updatedSections[cat] = [];
        }
      }

      setSections(updatedSections);

      // ✅ Enrich posters
      for (const cat of endpoints) {
        const list = updatedSections[cat];
        const posters = await Promise.all(
          list.map(async (r, i) => {
            const p = await fetchPosterFromBackend(r.title, cat);
            return p ? { i, p } : null;
          })
        );
        setSections((prev) => {
          const next = { ...prev };
          const arr = [...next[cat]];
          posters.forEach((u) => u && (arr[u.i].poster = u.p));
          next[cat] = arr;
          return next;
        });
      }
    } catch {
      setError("Failed to load personalized recommendations.");
    } finally {
      setLoading(false);
    }
  }, [isLoggedIn, navigate, fetchPosterFromBackend]);

  useEffect(() => {
    fetchAllPersonalized();
  }, [fetchAllPersonalized]);

  const handleLogout = () => {
    localStorage.removeItem("token");
    navigate("/auth");
  };

  const handleScrollToVisualization = () => {
    visualizationRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const renderGrid = (title, list) => (
    <div className="mb-12">
      <h3 className="text-3xl font-bold mb-6 text-cyan-400">{title}</h3>
      {list.length === 0 ? (
        <p className="text-gray-400 mb-6 text-center">
          No recommendations yet for {title.toLowerCase()}.
        </p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
          {list.map((r, i) => (
            <motion.div
              key={i}
              whileHover={{ scale: 1.05 }}
              className="relative group rounded-2xl overflow-hidden shadow-lg border border-cyan-500/30 bg-gradient-to-b from-blue-700/20 to-cyan-500/10"
            >
              <img
                src={r.poster}
                alt={r.title}
                className="w-full h-80 object-cover rounded-t-2xl"
                onError={(e) => (e.target.src = getFallbackPoster(r.type))}
              />

              <div className="absolute inset-0 bg-gradient-to-t from-black via-black/80 to-transparent opacity-0 group-hover:opacity-100 flex flex-col justify-end p-4 transition-opacity duration-500">
                <h3 className="text-lg font-bold text-cyan-400 mb-2">
                  {r.title}
                </h3>
                <p className="text-xs text-gray-300 line-clamp-3 mb-3">
                  {r.overview || "No overview available."}
                </p>
                <div className="flex justify-between text-xs text-gray-300">
                  <span>🎬 {r.type}</span>
                  <span className="text-cyan-400 font-bold">
                    🎯 {r.match_percent}%
                  </span>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );

  // 🧠 Visualization Data
  const visualizationData = Object.keys(sections).map((key) => {
    const list = sections[key] || [];
    const avgMatch =
      list.length > 0
        ? list.reduce((sum, r) => sum + (r.match_percent || 0), 0) /
          list.length
        : 0;
    return {
      category: key.charAt(0).toUpperCase() + key.slice(1),
      avgMatch: Math.round(avgMatch),
      count: list.length,
    };
  });

  return (
    <div className="relative min-h-screen flex flex-col items-center text-white bg-gradient-to-b from-black via-[#0f172a] to-[#1e293b] py-10">
      {/* Background glow */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-cyan-500/20 blur-3xl rounded-full"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/20 blur-3xl rounded-full"></div>
      </div>

      {/* Top Buttons */}
      <div className="absolute top-6 right-6 flex gap-3 z-20">
        {isLoggedIn && (
          <>
            <motion.button
              onClick={handleScrollToVisualization}
              className="px-5 py-2 bg-cyan-600 hover:bg-cyan-700 rounded-lg font-semibold shadow-md"
              whileHover={{ scale: 1.05 }}
            >
              📊 Visualize
            </motion.button>
            <motion.button
              onClick={() => navigate("/favorites")}
              className="px-5 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg font-semibold shadow-md"
              whileHover={{ scale: 1.05 }}
            >
              ⭐ Favorites
            </motion.button>
            <motion.button
              onClick={handleLogout}
              className="px-5 py-2 bg-red-600 hover:bg-red-700 rounded-lg font-semibold shadow-md"
              whileHover={{ scale: 1.05 }}
            >
              Logout
            </motion.button>
          </>
        )}
      </div>

      {/* Title */}
      <motion.h2
        className="text-5xl font-bold mb-10 z-10"
        initial={{ opacity: 0, y: -40 }}
        animate={{ opacity: 1, y: 0 }}
      >
        🎯 Your Personalized Picks
      </motion.h2>

      {/* Visualization Panel */}
      <div ref={visualizationRef} className="w-full max-w-5xl mb-16 z-10">
        <motion.div
          className="bg-gray-800/60 rounded-2xl p-6 shadow-lg"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7 }}
        >
          <h3 className="text-2xl font-semibold text-cyan-400 mb-6 text-center">
            📈 Recommendation Overview
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart
              data={visualizationData}
              margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="category" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#1e293b",
                  border: "1px solid #334155",
                }}
              />
              <Legend />
              <Bar
                dataKey="avgMatch"
                name="Avg Match %"
                fill="#06b6d4"
                radius={[8, 8, 0, 0]}
                animationDuration={900}
              />
              <Bar
                dataKey="count"
                name="Total Titles"
                fill="#a855f7"
                radius={[8, 8, 0, 0]}
                animationDuration={900}
              />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>
      </div>

      {/* Recommendation Grids */}
      <div className="w-full max-w-7xl px-4 z-10 min-h-[500px]">
        {loading ? (
          <div className="text-gray-400 text-center text-lg">
            Loading personalized recommendations...
          </div>
        ) : error ? (
          <p className="text-red-400 text-center">{error}</p>
        ) : (
          <>
            {renderGrid("🎬 Movies", sections.movies)}
            {renderGrid("📺 Series", sections.series)}
            {renderGrid("🍜 Anime", sections.anime)}
          </>
        )}
      </div>

      {/* Back button */}
      <button
        onClick={() => navigate("/")}
        className="mt-10 px-6 py-2 bg-gray-700/70 hover:bg-gray-600 rounded-lg shadow-lg transition"
      >
        ⬅ Back to Home
      </button>
    </div>
  );
}
