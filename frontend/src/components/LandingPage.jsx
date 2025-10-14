import { useState, useEffect, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useNavigate } from "react-router-dom"; // ✅ for navigation

const categories = ["movies", "series", "anime"];

export default function LandingPage() {
  const navigate = useNavigate(); // hook to navigate
  const [activeCategory, setActiveCategory] = useState("movies");
  const [fadeOverlay, setFadeOverlay] = useState(false);

  // ✅ Memoized posters (prevents re-creation warnings)
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

  const buttons = [
    { label: "Movies", key: "movies" },
    { label: "Series", key: "series" },
    { label: "Anime", key: "anime" },
  ];

  // 🎬 Smooth auto transitions
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

  // 🎯 Handle button click — fade and navigate
  const handleCategorySelect = (key) => {
    setFadeOverlay(true);
    setTimeout(() => {
      navigate(`/recommend?type=${key}`);
    }, 800);
  };

  return (
    <div className="relative min-h-screen flex flex-col justify-center items-center text-white overflow-hidden bg-gradient-to-b from-black via-[#0f172a] to-[#1e293b]">

      {/* 🎞 Background Posters */}
      <div className="absolute inset-0 overflow-hidden opacity-60">
        <AnimatePresence mode="wait">
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

      {/* 🎥 Fade Overlay */}
      <motion.div
        className="absolute inset-0 bg-black z-10"
        initial={{ opacity: 0 }}
        animate={{ opacity: fadeOverlay ? 0.8 : 0 }}
        transition={{ duration: 1 }}
      />

      {/* Gradient Overlay */}
      <div className="absolute inset-0 bg-gradient-to-b from-black/80 via-[#0f172a]/70 to-black/90 z-0" />

      {/* Floating Orbs */}
      <motion.div
        className="absolute -top-20 -right-20 w-96 h-96 bg-cyan-500/20 rounded-full blur-3xl"
        animate={{ y: [0, 30, 0], opacity: [0.4, 0.7, 0.4] }}
        transition={{ duration: 7, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="absolute -bottom-20 -left-20 w-96 h-96 bg-blue-600/20 rounded-full blur-3xl"
        animate={{ y: [0, -30, 0], opacity: [0.4, 0.7, 0.4] }}
        transition={{ duration: 7, repeat: Infinity, ease: "easeInOut" }}
      />

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
        className="text-lg text-gray-300 mb-12 z-20"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5, duration: 1 }}
      >
        Your next favorite show, revealed with precision ✨
      </motion.p>

      {/* Buttons */}
      <div className="flex flex-wrap justify-center gap-8 z-20">
        {buttons.map((btn, i) => (
          <motion.div
            key={btn.key}
            className="relative"
            onClick={() => handleCategorySelect(btn.key)}
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 + i * 0.3, type: "spring", stiffness: 60 }}
          >
            {/* Pulse ring */}
            <motion.div
              className={`absolute -inset-2 rounded-full blur-xl opacity-40 ${
                activeCategory === btn.key
                  ? "bg-gradient-to-r from-cyan-500 to-blue-600"
                  : "bg-gradient-to-r from-gray-600 to-gray-800"
              }`}
              animate={{ scale: [1, 1.15, 1] }}
              transition={{
                repeat: Infinity,
                duration: 4 + i,
                ease: "easeInOut",
              }}
            />
            {/* Button */}
            <motion.button
              whileTap={{ scale: 0.95 }}
              animate={{ y: [0, -6, 0] }}
              transition={{
                repeat: Infinity,
                duration: 4 + i * 0.5,
                ease: "easeInOut",
              }}
              className={`px-10 py-4 text-xl font-semibold rounded-full relative overflow-hidden ${
                activeCategory === btn.key
                  ? "bg-gradient-to-r from-blue-600 to-cyan-500"
                  : "bg-gradient-to-r from-gray-700 to-gray-900"
              } text-white`}
            >
              <span className="relative z-10">{btn.label}</span>
            </motion.button>
          </motion.div>
        ))}
      </div>

      {/* Footer */}
      <p className="mt-14 text-gray-400 text-sm tracking-wide z-20">
        Pick your path — the adventure starts now 🍿
      </p>
    </div>
  );
}
