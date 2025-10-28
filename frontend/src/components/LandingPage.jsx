import { useState, useEffect, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useNavigate } from "react-router-dom";

const categories = ["movies", "series", "anime"];

export default function LandingPage() {
  const navigate = useNavigate();
  const [activeCategory, setActiveCategory] = useState("movies");
  const [fadeOverlay, setFadeOverlay] = useState(false);

  // ✅ NEW: Track login state
  const [loggedIn, setLoggedIn] = useState(false);
  const [username, setUsername] = useState("");

  useEffect(() => {
    const token = localStorage.getItem("token");
    const name = localStorage.getItem("username");
    if (token && name) {
      setLoggedIn(true);
      setUsername(name);
    }
  }, []);

  // ✅ NEW: Logout function
  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    localStorage.removeItem("email");
    setLoggedIn(false);
    navigate("/");
  };

  const posters = useMemo(
    () => ({
      movies: [
        "inception.jpg",
        "interstellar.jpg",
        "Oppenheimer.jpg",
        "batman.jpg",
        "superman.jpg",
        "avengers.jpg",
        "deadpool.jpg",
      ],
      series: [
        "GOT.jpg",
        "Breaking-Bad.jpg",
        "Stranger-Things.jpg",
        "money-heist.jpg",
        "loki.jpg",
        "the-boys.jpg",
        "vikings.jpg",
      ],
      anime: [
        "AOT.jpg",
        "Solo-Leveling.jpg",
        "One-Piece.jpg",
        "deathnote.jpg",
        "vinland.jpg",
        "your-name.jpg",
        "demon-slayer.jpg",
      ],
    }),
    []
  );

  const handleCategorySelect = (key) => {
    setFadeOverlay(true);
    setTimeout(() => {
      navigate(`/recommend?type=${key}`);
    }, 800);
  };

  useEffect(() => {
    const interval = setInterval(() => {
      setFadeOverlay(true);
      setTimeout(() => {
        setActiveCategory((prev) => {
          const currentIndex = categories.indexOf(prev);
          const nextIndex = (currentIndex + 1) % categories.length;
          return categories[nextIndex];
        });
        setFadeOverlay(false);
      }, 1200);
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="relative min-h-screen flex flex-col justify-center items-center text-white overflow-hidden bg-gradient-to-b from-black via-[#0f172a] to-[#1e293b]">

      {/* ✅ NEW - Welcome Message */}
      {loggedIn && (
        <motion.div
          className="absolute top-6 right-6 z-30 bg-gray-900/50 px-4 py-2 rounded-xl border border-cyan-400/40 shadow-lg"
          initial={{ opacity: 0, x: 30 }}
          animate={{ opacity: 1, x: 0 }}
        >
          👋 Welcome, <span className="text-cyan-400 font-semibold">{username}</span>
        </motion.div>
      )}

      {/* Background Posters */}
      <div className="absolute inset-0 overflow-hidden opacity-60">
        <AnimatePresence mode="sync">
          {posters[activeCategory]?.map((img, i) => (
            <motion.img
              key={`${activeCategory}-${img}`}
              src={require(`../assets/posters/${img}`)}
              alt=""
              className="absolute w-[28%] md:w-[22%] rounded-2xl shadow-2xl object-cover"
              style={{
                top: `${10 + i * 15}%`,
                left: `${8 + i * 18}%`,
                transform: `rotate(${i % 2 === 0 ? 5 : -5}deg)`,
                filter: "blur(3px) brightness(0.7)",
              }}
              initial={{ opacity: 0, scale: 1.05 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 2.5 + i * 0.3, ease: "easeInOut" }}
            />
          ))}
        </AnimatePresence>
      </div>

      {/* Fade Overlay */}
      <motion.div
        className="absolute inset-0 bg-black z-10"
        initial={{ opacity: 0 }}
        animate={{ opacity: fadeOverlay ? 0.8 : 0 }}
        transition={{ duration: 1 }}
      />

      {/* Gradient Overlay */}
      <div className="absolute inset-0 bg-gradient-to-b from-black/80 via-[#0f172a]/70 to-black/90 z-0" />

      {/* Title */}
      <motion.h1
        className="text-6xl font-extrabold mb-6 tracking-wide drop-shadow-[0_0_25px_rgba(0,255,255,0.5)] z-20"
        initial={{ opacity: 0, y: -40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1 }}
      >
        CineSense
      </motion.h1>

      {/* Tagline */}
      <motion.p
        className="text-lg text-gray-300 mb-12 z-20 text-center max-w-lg"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5, duration: 1 }}
      >
        Your next favorite show, revealed with precision ✨
      </motion.p>

      {/* Category Buttons */}
      <div className="flex flex-wrap justify-center gap-8 z-20">
        {categories.map((key, i) => (
          <motion.button
            key={key}
            onClick={() => handleCategorySelect(key)}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className={`px-10 py-4 text-xl font-semibold rounded-full ${
              activeCategory === key
                ? "bg-gradient-to-r from-blue-600 to-cyan-500 shadow-lg shadow-cyan-500/30"
                : "bg-gradient-to-r from-gray-700 to-gray-900"
            }`}
            transition={{ delay: 0.2 + i * 0.2 }}
          >
            {key.charAt(0).toUpperCase() + key.slice(1)}
          </motion.button>
        ))}
      </div>

      {/* ✅ AUTH Buttons Updated */}
      <div className="flex flex-col sm:flex-row gap-5 mt-14 z-20">
        {!loggedIn ? (
          <motion.button
            onClick={() => navigate("/auth")}
            className="px-8 py-3 bg-purple-600 hover:bg-purple-700 rounded-full text-lg font-semibold shadow-lg shadow-purple-500/30"
            whileHover={{ scale: 1.05 }}
          >
            Login / Register
          </motion.button>
        ) : (
          <motion.button
            onClick={handleLogout}
            className="px-8 py-3 bg-red-600 hover:bg-red-700 rounded-full text-lg font-semibold shadow-lg shadow-red-500/30"
            whileHover={{ scale: 1.05 }}
          >
            Logout
          </motion.button>
        )}
      </div>

      {/* Footer */}
      <p className="mt-14 text-gray-400 text-sm tracking-wide z-20">
        Pick your path — the adventure starts now 🍿
      </p>
    </div>
  );
}
