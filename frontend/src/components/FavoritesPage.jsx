import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { authFetch } from "../utils/authFetch";

const serverBaseURL =
  process.env.REACT_APP_BACKEND_URL || "http://127.0.0.1:5000";

export default function FavoritesPage() {
  const navigate = useNavigate();
  const [favorites, setFavorites] = useState({ movies: [], series: [], anime: [] });
  const [expanded, setExpanded] = useState({ movies: true, series: true, anime: true });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // ✅ Fetch favorites
  useEffect(() => {
    const fetchFavorites = async () => {
      try {
        const res = await authFetch(`${serverBaseURL}/api/favorites/`, {}, navigate);
        const data = await res.json();

        if (data.success) {
          setFavorites({
            movies: data.favorites.movies || [],
            series: data.favorites.series || [],
            anime: data.favorites.anime || [],
          });
        } else {
          setError(data.message || "Failed to load favorites");
        }
      } catch (err) {
        console.error("Favorites fetch error:", err);
        setError("Server error while fetching favorites.");
      } finally {
        setLoading(false);
      }
    };
    fetchFavorites();
  }, [navigate]);

  // ❌ Remove favorite
  const handleRemove = async (id, type) => {
    try {
      const res = await authFetch(
        `${serverBaseURL}/api/favorites/remove/${id}`,
        { method: "DELETE" },
        navigate
      );
      const data = await res.json();

      if (data.success) {
        setFavorites((prev) => ({
          ...prev,
          [type]: prev[type].filter((f) => f._id !== id),
        }));
      } else {
        setError(data.message || "Failed to remove favorite.");
      }
    } catch (err) {
      console.error("Remove favorite error:", err);
      setError("Server error while removing favorite.");
    }
  };

  const toggleExpand = (type) =>
    setExpanded((prev) => ({ ...prev, [type]: !prev[type] }));

  // 🎬 Render category block
  const renderCategory = (title, items, type, emoji) => (
    <div key={type} className="mb-10">
      <div
        onClick={() => toggleExpand(type)}
        className="flex justify-between items-center cursor-pointer mb-4"
      >
        <h3 className="text-3xl font-bold text-cyan-400 tracking-wide">
          {emoji} {title}
        </h3>
        <motion.span
          animate={{ rotate: expanded[type] ? 180 : 0 }}
          transition={{ duration: 0.3 }}
          className="text-cyan-300 text-xl"
        >
          ▼
        </motion.span>
      </div>

      <AnimatePresence initial={false}>
        {expanded[type] && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.4 }}
            className="overflow-hidden"
          >
            {items.length === 0 ? (
              <p className="text-gray-500 italic mb-6">No favorites yet.</p>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
                {items.map((f, i) => (
                  <motion.div
                    key={f._id || i}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    whileHover={{ scale: 1.05 }}
                    transition={{ delay: i * 0.05 }}
                    className="relative group bg-gradient-to-b from-blue-700/20 to-cyan-500/10 rounded-2xl overflow-hidden shadow-lg border border-cyan-500/30"
                  >
                    <img
                      src={f.poster || "/posters/default.jpg"}
                      alt={f.title}
                      onError={(e) => (e.target.src = "/posters/default.jpg")}
                      className="w-full h-80 object-cover rounded-t-2xl"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black via-black/80 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 flex flex-col justify-end p-4">
                      <h3 className="text-lg font-bold text-cyan-400 mb-2 line-clamp-2">
                        {f.title}
                      </h3>
                      <motion.button
                        onClick={() => handleRemove(f._id, type)}
                        className="mt-2 px-4 py-1 bg-red-600 hover:bg-red-700 text-sm rounded-lg"
                        whileHover={{ scale: 1.05 }}
                      >
                        ❌ Remove
                      </motion.button>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );

  return (
    <div className="relative min-h-screen flex flex-col items-center text-white bg-gradient-to-b from-black via-[#0f172a] to-[#1e293b] py-10">
      {/* Floating orbs */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-cyan-500/20 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl animate-pulse delay-1000"></div>
      </div>

      {/* Header */}
      <motion.h2
        className="text-5xl font-bold mb-10 tracking-wide drop-shadow-[0_0_25px_rgba(0,255,255,0.5)] z-10"
        initial={{ opacity: 0, y: -40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1 }}
      >
        ❤️ Your Favorites
      </motion.h2>

      {/* States */}
      {loading ? (
        <div className="text-gray-400 text-lg flex flex-col items-center gap-4 z-10">
          <div className="w-12 h-12 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin"></div>
          <p>Loading your favorites...</p>
        </div>
      ) : error ? (
        <p className="text-red-400 z-10">{error}</p>
      ) : (
        <div className="z-10 w-full max-w-7xl px-4">
          {renderCategory("Movies", favorites.movies, "movies", "🎬")}
          {renderCategory("Series", favorites.series, "series", "📺")}
          {renderCategory("Anime", favorites.anime, "anime", "🍜")}
        </div>
      )}

      {/* Back button */}
      <button
        onClick={() => navigate("/recommend?type=movies")}
        className="mt-10 px-6 py-2 bg-gray-700/70 hover:bg-gray-600 text-white rounded-lg shadow-lg transition z-10"
      >
        ⬅ Back to Recommendations
      </button>
    </div>
  );
}
