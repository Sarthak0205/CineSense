import React, { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";

const TMDB_API_KEY = process.env.REACT_APP_TMDB_KEY;

export default function RecommendPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const params = new URLSearchParams(location.search);
  const category = params.get("type") || "movies";

  const [title, setTitle] = useState("");
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);

  const beginnerLists = {
    movies: ["Inception", "Interstellar", "The Dark Knight", "Avengers", "Titanic"],
    series: ["Breaking Bad", "Stranger Things", "Money Heist", "Loki", "Game of Thrones"],
    anime: ["Attack on Titan", "Demon Slayer", "Death Note", "One Piece", "Naruto"],
  };

  const fetchTMDBDetails = async (title, category) => {
    try {
      let endpoint;
      if (category === "anime") {
        endpoint = `https://api.themoviedb.org/3/search/tv?api_key=${TMDB_API_KEY}&query=${encodeURIComponent(
          title
        )}&language=en-US&page=1`;
      } else if (category === "series") {
        endpoint = `https://api.themoviedb.org/3/search/tv?api_key=${TMDB_API_KEY}&query=${encodeURIComponent(
          title
        )}&language=en-US&page=1`;
      } else {
        endpoint = `https://api.themoviedb.org/3/search/movie?api_key=${TMDB_API_KEY}&query=${encodeURIComponent(
          title
        )}&language=en-US&page=1`;
      }
      const res = await fetch(endpoint);
      const data = await res.json();
      if (!data.results || data.results.length === 0) return null;
      let best;
      if (category === "anime") {
        const japanese = data.results.find((i) => i.original_language === "ja");
        best = japanese || data.results[0];
      } else {
        best = data.results[0];
      }
      const fallbackPosters = {
        Naruto: "https://upload.wikimedia.org/wikipedia/en/9/94/NarutoCoverTankobon1.jpg",
        "One Piece": "https://upload.wikimedia.org/wikipedia/en/6/6c/One_Piece_Volume_1.jpg",
      };
      return {
        id: best.id,
        title: best.title || best.name || title,
        overview: best.overview || "No overview available.",
        rating: best.vote_average || 0,
        release_date: best.release_date || best.first_air_date || "N/A",
        poster:
          best.poster_path
            ? `https://image.tmdb.org/t/p/w500${best.poster_path}`
            : fallbackPosters[title] || "https://via.placeholder.com/500x750?text=No+Image",
      };
    } catch (err) {
      console.error("TMDB Fetch Error:", err);
      return null;
    }
  };

  const handleBeginner = async () => {
    setLoading(true);
    const titles = beginnerLists[category] || [];
    const results = [];
    for (const t of titles) {
      const meta = await fetchTMDBDetails(t, category);
      if (meta) results.push(meta);
    }
    setRecommendations(results);
    setLoading(false);
  };

  const handleSearch = async () => {
    if (!title.trim()) return;
    try {
      setLoading(true);
      const response = await fetch("http://127.0.0.1:5000/api/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, type: category }),
      });
      if (!response.ok) throw new Error("Failed to fetch recommendations");
      const data = await response.json();
      setRecommendations(data);
    } catch (err) {
      console.error("Recommendation Error:", err);
      setRecommendations([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen flex flex-col justify-center items-center text-white overflow-hidden bg-gradient-to-b from-black via-[#0f172a] to-[#1e293b]">
      <motion.div
        className="absolute -top-20 -right-20 w-96 h-96 bg-cyan-500/20 rounded-full blur-3xl"
        animate={{ y: [0, 40, 0], opacity: [0.4, 0.8, 0.4] }}
        transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="absolute -bottom-20 -left-20 w-96 h-96 bg-blue-600/20 rounded-full blur-3xl"
        animate={{ y: [0, -40, 0], opacity: [0.4, 0.8, 0.4] }}
        transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
      />

      <motion.h2
        className="text-5xl font-bold mb-8 tracking-wide drop-shadow-[0_0_25px_rgba(0,255,255,0.5)] z-10"
        initial={{ opacity: 0, y: -40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1 }}
      >
        CineSense Recommendations
      </motion.h2>

      <div className="z-10 flex flex-col sm:flex-row gap-3 mb-10">
        <input
          type="text"
          placeholder="Enter a title..."
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="px-4 py-2 rounded-lg text-black focus:outline-none"
        />
        <motion.button
          onClick={handleSearch}
          className="px-6 py-2 bg-cyan-600 rounded-lg font-semibold hover:bg-cyan-700 transition"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          Get Recommendations
        </motion.button>
        <motion.button
          onClick={handleBeginner}
          className="px-6 py-2 bg-gradient-to-r from-green-500 to-green-700 rounded-lg font-semibold hover:scale-105 transition"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          🌱 I'm a Beginner
        </motion.button>
      </div>

      <AnimatePresence mode="wait">
        {loading ? (
          <motion.div
            key="loading"
            className="text-gray-400 text-lg z-10"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            Fetching beginner recommendations...
          </motion.div>
        ) : (
          <motion.div
            key="content"
            className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-10 px-10 z-10"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 1 }}
          >
            {recommendations.map((item, idx) => {
              // Safe fallback for missing fields from backend
              const poster = item.poster || "https://via.placeholder.com/500x750?text=No+Image";
              const title = item.title || `Untitled ${idx + 1}`;
              const overview = item.overview || "No overview available.";
              const rating = typeof item.rating === "number" ? item.rating : 0;
              const release_date = item.release_date || "N/A";
              return (
                <motion.div
                  key={item.id || title || idx}
                  whileHover={{ scale: 1.08 }}
                  className="relative group bg-gradient-to-b from-blue-700/20 to-cyan-500/10 rounded-2xl overflow-hidden shadow-lg backdrop-blur-xl border border-cyan-500/30"
                >
                  <img
                    src={poster}
                    alt={title}
                    className="w-full h-80 object-cover opacity-90 group-hover:opacity-100 transition duration-500"
                    onError={(e) => {
                      e.target.src = "https://via.placeholder.com/500x750?text=No+Image";
                    }}
                  />
                  <div className="absolute inset-0 bg-black/70 opacity-0 group-hover:opacity-100 transition duration-500 flex flex-col justify-center items-center text-center p-4">
                    <h3 className="text-xl font-bold text-cyan-400 mb-2">{title}</h3>
                    <p className="text-sm text-gray-300 line-clamp-4">{overview}</p>
                    <p className="text-yellow-400 mt-3">⭐ {rating.toFixed(1)}</p>
                    <p className="text-gray-400 text-sm">{release_date}</p>
                  </div>
                </motion.div>
              );
            })}
          </motion.div>
        )}
      </AnimatePresence>

      <motion.button
        onClick={() => navigate("/")}
        className="mt-14 px-8 py-3 text-lg rounded-full bg-gradient-to-r from-cyan-600 to-blue-700 text-white font-semibold shadow-[0_0_25px_rgba(0,255,255,0.4)] hover:scale-105 transition-transform z-10"
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.95 }}
      >
        ⬅ Back to Home
      </motion.button>
    </div>
  );
}
