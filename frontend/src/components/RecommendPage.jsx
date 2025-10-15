import React, { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";

const TMDB_API_KEY = process.env.REACT_APP_TMDB_KEY;
const serverBaseURL = process.env.REACT_APP_BACKEND_URL || "http://127.0.0.1:5000";

export default function RecommendPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const params = new URLSearchParams(location.search);
  const category = params.get("type") || "movies";

  const [title, setTitle] = useState("");
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

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
    setError("");
    const titles = beginnerLists[category] || [];
    const results = [];
    
    console.log("🌱 Fetching beginner recommendations for:", category);
    
    for (const t of titles) {
      const meta = await fetchTMDBDetails(t, category);
      if (meta) results.push(meta);
    }
    
    console.log("✅ Beginner recommendations loaded:", results.length);
    setRecommendations(results);
    setLoading(false);
  };

  const handleSearch = async () => {
    if (!title.trim()) {
      setError("Please enter a title");
      return;
    }
    
    try {
      setLoading(true);
      setError("");
      
      console.log("🔍 Searching for:", title, "| Category:", category);
      console.log("📡 Backend URL:", serverBaseURL);
      
      const response = await fetch(`${serverBaseURL}/api/recommend`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          title: title.trim(), 
          type: category === "movies" ? "movie" : category === "series" ? "series" : "anime",
          top_n: 10
        }),
      });
      
      console.log("📡 Response status:", response.status);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error("❌ Response error:", errorText);
        throw new Error(`Failed to fetch recommendations: ${response.status}`);
      }
      
      const data = await response.json();
      console.log("✅ Received data:", data);
      console.log("📊 Results count:", data.results?.length || 0);
      
      // Check if results exist
      if (data.error) {
        console.warn("⚠️ Backend error:", data.error);
        setError(data.error);
        setRecommendations([]);
        return;
      }
      
      if (!data.results || data.results.length === 0) {
        console.warn("⚠️ No recommendations returned");
        setError("No recommendations found. Try a different title!");
        setRecommendations([]);
        return;
      }
      
      setRecommendations(data.results);
      console.log("✅ Set recommendations:", data.results.length);
      
    } catch (err) {
      console.error("❌ Recommendation Error:", err);
      setError(`Error: ${err.message}`);
      setRecommendations([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen flex flex-col justify-center items-center text-white overflow-hidden bg-gradient-to-b from-black via-[#0f172a] to-[#1e293b]">
      {/* Background Effects */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-cyan-500/20 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl animate-pulse delay-1000"></div>
      </div>

      <motion.h2
        className="text-5xl font-bold mb-8 tracking-wide drop-shadow-[0_0_25px_rgba(0,255,255,0.5)] z-10"
        initial={{ opacity: 0, y: -40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1 }}
      >
        CineSense Recommendations
      </motion.h2>

      <div className="z-10 flex flex-col sm:flex-row gap-3 mb-6">
        <input
          type="text"
          placeholder={`Enter a ${category === 'movies' ? 'movie' : category === 'series' ? 'series' : 'anime'} title...`}
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          className="px-4 py-2 rounded-lg text-black focus:outline-none focus:ring-2 focus:ring-cyan-500"
        />
        <motion.button
          onClick={handleSearch}
          disabled={loading}
          className="px-6 py-2 bg-cyan-600 rounded-lg font-semibold hover:bg-cyan-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
          whileHover={{ scale: loading ? 1 : 1.05 }}
          whileTap={{ scale: loading ? 1 : 0.95 }}
        >
          {loading ? "Loading..." : "Get Recommendations"}
        </motion.button>
        <motion.button
          onClick={handleBeginner}
          disabled={loading}
          className="px-6 py-2 bg-gradient-to-r from-green-500 to-green-700 rounded-lg font-semibold hover:scale-105 transition disabled:opacity-50 disabled:cursor-not-allowed"
          whileHover={{ scale: loading ? 1 : 1.05 }}
          whileTap={{ scale: loading ? 1 : 0.95 }}
        >
          🌱 I'm a Beginner
        </motion.button>
      </div>

      {/* Error Message */}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="z-10 mb-4 px-6 py-3 bg-red-500/20 border border-red-500 rounded-lg text-red-200"
        >
          {error}
        </motion.div>
      )}

      <AnimatePresence mode="wait">
        {loading ? (
          <motion.div
            key="loading"
            className="text-gray-400 text-lg z-10 flex flex-col items-center gap-4"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <div className="w-12 h-12 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin"></div>
            <p>Fetching recommendations...</p>
          </motion.div>
        ) : (
          <motion.div
            key="content"
            className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-10 px-10 z-10 max-w-7xl"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5 }}
          >
            {recommendations.map((item, idx) => {
              // Handle poster URL
              let posterUrl = item.poster || "https://via.placeholder.com/500x750?text=No+Image";
              if (posterUrl.startsWith("/poster/")) {
                posterUrl = serverBaseURL + posterUrl;
              }
              
              const itemTitle = item.title || `Untitled ${idx + 1}`;
              const overview = item.overview || "No overview available.";
              const rating = typeof item.rating === "number" ? item.rating : 0;
              const releaseDate = item.release_date || "N/A";
              
              return (
                <motion.div
                  key={item.id || itemTitle || idx}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: idx * 0.05 }}
                  whileHover={{ scale: 1.08 }}
                  className="relative group bg-gradient-to-b from-blue-700/20 to-cyan-500/10 rounded-2xl overflow-hidden shadow-lg backdrop-blur-xl border border-cyan-500/30"
                >
                  <img
                    src={posterUrl}
                    alt={itemTitle}
                    className="w-full h-80 object-cover opacity-90 group-hover:opacity-100 transition duration-500"
                    onError={(e) => {
                      console.error("Image load error for:", itemTitle);
                      e.target.src = "https://via.placeholder.com/500x750?text=No+Image";
                    }}
                  />
                  <div className="absolute inset-0 bg-black/70 opacity-0 group-hover:opacity-100 transition duration-500 flex flex-col justify-center items-center text-center p-4">
                    <h3 className="text-xl font-bold text-cyan-400 mb-2">{itemTitle}</h3>
                    <p className="text-sm text-gray-300 line-clamp-4 mb-3">{overview}</p>
                    <div className="flex items-center gap-4 text-sm">
                      <p className="text-yellow-400">⭐ {rating.toFixed(1)}</p>
                      <p className="text-gray-400">{releaseDate}</p>
                    </div>
                    {item.similarity && (
                      <p className="text-cyan-300 text-xs mt-2">
                        Match: {(item.similarity * 100).toFixed(1)}%
                      </p>
                    )}
                  </div>
                </motion.div>
              );
            })}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Show message when no results */}
      {!loading && recommendations.length === 0 && !error && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="z-10 text-gray-400 text-center mt-10"
        >
          <p className="text-xl mb-2">No recommendations yet</p>
          <p className="text-sm">Enter a title or try the beginner option</p>
        </motion.div>
      )}

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