import React, { useState, useCallback, useRef } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { authFetch } from "../utils/authFetch";
import VisualizationPanel from "../components/VisualizationPanel";

const serverBaseURL =
  process.env.REACT_APP_BACKEND_URL || "http://127.0.0.1:5000";

const getFallbackPoster = (genres, category) => "/posters/default.png";

export default function RecommendPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const params = new URLSearchParams(location.search);
  const category = params.get("type") || "movies";

  const [title, setTitle] = useState("");
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [hasSearched, setHasSearched] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");
  const [showViz, setShowViz] = useState(false);

  const visualizationRef = useRef(null);
  const token = localStorage.getItem("token");
  const isLoggedIn = !!token;

  const handleBeginner = () => {
    const presets = {
      movies: [
        { title: "Inception", poster: "/posters/inception.jpg" },
        { title: "Interstellar", poster: "/posters/interstellar.jpg" },
        { title: "Avengers", poster: "/posters/avengers.jpg" },
      ],
      series: [
        { title: "Breaking Bad", poster: "/posters/Breaking-Bad.jpg" },
        { title: "Stranger Things", poster: "/posters/Stranger-Things.jpg" },
        { title: "Loki", poster: "/posters/loki.jpg" },
      ],
      anime: [
        { title: "Attack on Titan", poster: "/posters/AOT.jpg" },
        { title: "Demon Slayer", poster: "/posters/demon-slayer.jpg" },
        { title: "Naruto", poster: "/posters/vinland.jpg" },
      ],
    };
    const list = presets[category] || [];
    setRecommendations(
      list.map((i) => ({
        title: i.title,
        poster: i.poster,
        overview: "A must-watch beginner-friendly title.",
        rating: 8.5,
        release_date: "N/A",
        match_percent: 100,
        added: false,
      }))
    );
    setHasSearched(true);
  };

  const fetchPosterFromBackend = useCallback(async (title, type) => {
    try {
      const res = await fetch(
        `${serverBaseURL}/api/poster/${encodeURIComponent(title)}?type=${type}`
      );
      if (!res.ok) return null;
      const data = await res.json();
      return data.poster;
    } catch {
      return null;
    }
  }, []);

  const handleSearch = async () => {
    if (!title.trim()) return setError("Please enter a title");
    setLoading(true);
    setError("");
    setSuccessMsg("");
    setRecommendations([]);
    setHasSearched(true);

    try {
      const res = await fetch(`${serverBaseURL}/api/recommend`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: title.trim(),
          type: category === "movies" ? "movie" : category,
          top_k: 10,
        }),
      });

      if (!res.ok) throw new Error("Server error");
      const data = await res.json();
      if (!data.success)
        throw new Error(data.message || "No recommendations found.");

      const results = data.results.map((r) => ({
        ...r,
        poster: getFallbackPoster(r.genres, category),
        added: false,
      }));
      setRecommendations(results);

      const updates = await Promise.all(
        results.map(async (r, i) => {
          const p = await fetchPosterFromBackend(r.title, r.type || category);
          return p ? { i, p } : null;
        })
      );
      setRecommendations((prev) => {
        const next = [...prev];
        updates.forEach((u) => u && (next[u.i].poster = u.p));
        return next;
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAddToFavorites = async (item, index) => {
    if (!isLoggedIn) return setError("Please login to save favorites.");
    try {
      const res = await authFetch(
        `${serverBaseURL}/api/favorites/add`,
        {
          method: "POST",
          body: JSON.stringify({
            title: item.title,
            type: category,
            poster: item.poster,
          }),
        },
        navigate
      );

      const data = await res.json();
      if (data.success) {
        setRecommendations((prev) =>
          prev.map((r, i) => (i === index ? { ...r, added: true } : r))
        );
        setSuccessMsg(`✅ Added "${item.title}" to favorites!`);
        setTimeout(() => setSuccessMsg(""), 2000);
      } else {
        setError(data.message || "Failed to add favorite");
      }
    } catch {
      setError("Server error while adding favorite.");
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    navigate("/auth");
  };

  const scrollToVisualization = () => {
    setShowViz(true);
    setTimeout(() => {
      visualizationRef.current?.scrollIntoView({ behavior: "smooth" });
    }, 100);
  };

  return (
    <div className="relative min-h-screen flex flex-col items-center text-white bg-gradient-to-b from-black via-[#0f172a] to-[#1e293b] py-10">
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-cyan-500/20 blur-3xl rounded-full"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-500/20 blur-3xl rounded-full"></div>
      </div>

      <div className="absolute top-6 right-6 flex gap-3 z-20">
        {isLoggedIn && (
          <>
            <motion.button
              onClick={() => navigate("/favorites")}
              className="px-5 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg font-semibold shadow-md"
              whileHover={{ scale: 1.05 }}
            >
              ⭐ View Favorites
            </motion.button>
            <motion.button
              onClick={() => navigate("/personalized")}
              className="px-5 py-2 bg-cyan-600 hover:bg-cyan-700 rounded-lg font-semibold shadow-md"
              whileHover={{ scale: 1.05 }}
            >
              🎯 Personalized
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

      <motion.h2
        className="text-5xl font-bold mb-8 z-10"
        initial={{ opacity: 0, y: -40 }}
        animate={{ opacity: 1, y: 0 }}
      >
        CineSense Recommendations
      </motion.h2>

      <div className="z-10 flex flex-col sm:flex-row gap-3 mb-6">
        <input
          type="text"
          placeholder={`Enter a ${category} title...`}
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          className="px-4 py-2 rounded-lg text-black focus:ring-2 focus:ring-cyan-500"
        />
        <motion.button
          onClick={handleSearch}
          disabled={loading}
          className="px-6 py-2 bg-cyan-600 rounded-lg font-semibold"
          whileHover={{ scale: loading ? 1 : 1.05 }}
        >
          {loading ? "Loading..." : "Get Recommendations"}
        </motion.button>
        <motion.button
          onClick={handleBeginner}
          className="px-6 py-2 bg-gradient-to-r from-green-500 to-green-700 rounded-lg font-semibold"
          whileHover={{ scale: 1.05 }}
        >
          🌱 I'm a Beginner
        </motion.button>
      </div>

      {recommendations.length > 0 && (
        <div className="z-10 flex justify-center mb-6">
          <button
            className="px-6 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg font-semibold shadow-md"
            onClick={scrollToVisualization}
          >
            📊 Show Visualizations
          </button>
        </div>
      )}

      {error && <p className="text-red-400 mb-4 z-10">{error}</p>}
      {successMsg && <p className="text-green-400 mb-4 z-10">{successMsg}</p>}

      <div className="w-full max-w-7xl px-4 z-10 min-h-[500px]">
        {loading ? (
          <div className="text-gray-400 text-lg flex flex-col items-center gap-4">
            <div className="w-12 h-12 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin"></div>
            <p>Fetching recommendations...</p>
          </div>
        ) : !hasSearched ? (
          <p className="text-gray-400 text-center text-xl">
            Search for a title or click “I'm a Beginner” to get started!
          </p>
        ) : recommendations.length > 0 ? (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
              {recommendations.map((r, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  whileHover={{ scale: 1.05 }}
                  className="relative group bg-gradient-to-b from-blue-700/20 to-cyan-500/10 rounded-2xl overflow-hidden shadow-lg border border-cyan-500/30"
                >
                  <img
                    src={r.poster}
                    alt={r.title}
                    className="w-full h-80 object-cover rounded-t-2xl"
                    onError={(e) =>
                      (e.target.src = getFallbackPoster(r.genres, category))
                    }
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black via-black/80 to-transparent opacity-0 group-hover:opacity-100 flex flex-col justify-end p-4 transition-opacity duration-500">
                    <h3 className="text-lg font-bold text-cyan-400 mb-2">
                      {r.title}
                    </h3>
                    <p className="text-xs text-gray-300 line-clamp-3 mb-3">
                      {r.overview}
                    </p>
                    <div className="flex justify-between text-xs text-gray-300">
                      <span>⭐ {r.rating?.toFixed(1) || "N/A"}</span>
                      <span>📅 {r.release_date || "N/A"}</span>
                      <span>🎯 {r.match_percent}%</span>
                    </div>
                    {isLoggedIn && (
                      <motion.button
                        onClick={() => handleAddToFavorites(r, i)}
                        className={`mt-3 px-4 py-1 text-sm rounded-lg transition ${
                          r.added
                            ? "bg-green-600 cursor-default"
                            : "bg-purple-600 hover:bg-purple-700"
                        }`}
                        disabled={r.added}
                      >
                        {r.added ? "✅ Added" : "❤️ Add to Favorites"}
                      </motion.button>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>

            {showViz && (
              <div ref={visualizationRef}>
                <VisualizationPanel recommendations={recommendations} />
              </div>
            )}
          </>
        ) : (
          <p className="text-gray-400 text-lg text-center">
            No recommendations found.
          </p>
        )}
      </div>

      <button
        onClick={() => navigate("/")}
        className="mt-10 px-6 py-2 bg-gray-700/70 hover:bg-gray-600 text-white rounded-lg shadow-lg transition"
      >
        ⬅ Back to Home
      </button>
    </div>
  );
}
