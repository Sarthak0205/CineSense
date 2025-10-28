import React from "react";
import { Bar, Doughnut, Pie, Scatter } from "react-chartjs-2";
import {
  Chart as ChartJS,
  BarElement,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
  ArcElement,
} from "chart.js";
import { motion } from "framer-motion";
import { Film, Star, Layers } from "lucide-react";

ChartJS.register(
  BarElement,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
  ArcElement
);

function toNumber(val) {
  if (val == null) return 0;
  if (typeof val === "object") {
    const key = Object.keys(val)[0];
    const maybe = val[key];
    return Number(maybe) || 0;
  }
  return Number(val) || 0;
}

function normalizePercentArray(arr) {
  const nums = arr.map((v) => toNumber(v));
  const max = Math.max(...nums, 0);
  if (max <= 1) return nums.map((n) => n * 100);
  return nums;
}

export default function VisualizationPanel({ recommendations = [] }) {
  if (!recommendations.length)
    return (
      <p className="text-gray-400 text-center mt-10">
        No data to visualize yet. Try searching for a title.
      </p>
    );

  // --- Basic Data ---
  const topRaw = [...recommendations]
    .sort((a, b) => toNumber(b.match_percent) - toNumber(a.match_percent))
    .slice(0, 8);
  const labels = topRaw.map((r) => String(r.title || "Untitled"));
  const rawMatchValues = topRaw.map((r) => toNumber(r.match_percent));
  const matchData = normalizePercentArray(rawMatchValues);
  const avgMatch =
    matchData.length > 0
      ? matchData.reduce((a, b) => a + b, 0) / matchData.length
      : 0;

  // --- Ratings ---
  const ratings = recommendations.map((r) => toNumber(r.rating) || 0);
  const avgRating =
    ratings.length > 0
      ? ratings.reduce((a, b) => a + b, 0) / ratings.length
      : 0;

  // --- Genres ---
  const genreCounts = {};
  recommendations.forEach((r) => {
    let genres = [];
    if (Array.isArray(r.genres))
      genres = r.genres.map((g) =>
        typeof g === "object" && g?.name ? g.name : String(g)
      );
    else if (typeof r.genres === "string") genres = [r.genres];
    genres.forEach((g) => {
      if (g?.trim()) genreCounts[g.trim()] = (genreCounts[g.trim()] || 0) + 1;
    });
  });
  const sortedGenres = Object.entries(genreCounts).sort((a, b) => b[1] - a[1]);
  const topGenre = sortedGenres[0]?.[0] || "N/A";

  const genreLabels = sortedGenres.map(([g]) => g);
  const genreData = sortedGenres.map(([_, c]) => c);

  // --- Bar Chart (Match Value) ---
  const barData = {
    labels,
    datasets: [
      {
        label: "Match Value",
        data: matchData,
        backgroundColor: matchData.map(
          (v) => `rgba(34,197,94,${Math.min(0.95, 0.5 + v / 250)})`
        ),
        borderRadius: 10,
        borderSkipped: false,
      },
    ],
  };

  // --- Rating Distribution ---
  const ratingBuckets = Array(10).fill(0);
  recommendations.forEach((r) => {
    const rating = Math.floor(toNumber(r.rating)) || 0;
    if (rating >= 0 && rating <= 9) ratingBuckets[rating]++;
  });

  const ratingLabels = [
    "0-1",
    "1-2",
    "2-3",
    "3-4",
    "4-5",
    "5-6",
    "6-7",
    "7-8",
    "8-9",
    "9-10",
  ];
  const ratingData = {
    labels: ratingLabels,
    datasets: [
      {
        label: "Count of Recommendations",
        data: ratingBuckets,
        backgroundColor: "rgba(59,130,246,0.6)",
        borderRadius: 10,
      },
    ],
  };

  // --- Genre Pie ---
  const genreChartData = {
    labels: genreLabels,
    datasets: [
      {
        data: genreData,
        backgroundColor: genreLabels.map(
          (_, i) => `hsl(${(i * 50) % 360}, 70%, 55%)`
        ),
        borderWidth: 2,
        borderColor: "#0b1220",
      },
    ],
  };

  // --- Scatter (Match vs Rating) ---
  const scatterData = {
    datasets: [
      {
        label: "Match Consistency",
        data: recommendations.map((r) => ({
          x: toNumber(r.rating),
          y: toNumber(r.match_percent),
        })),
        backgroundColor: "rgba(139,92,246,0.8)",
      },
    ],
  };

  const scatterOptions = {
    scales: {
      x: { title: { display: true, text: "Rating", color: "#9fb4ff" } },
      y: { title: { display: true, text: "Match %", color: "#9fb4ff" } },
    },
    plugins: { legend: { labels: { color: "#e6eef8" } } },
  };

  // --- Horizontal Top Genres ---
  const topGenreBar = {
    labels: genreLabels.slice(0, 6),
    datasets: [
      {
        label: "Count",
        data: genreData.slice(0, 6),
        backgroundColor: "rgba(234,179,8,0.7)",
        borderRadius: 8,
      },
    ],
  };

  const barOptions = {
    indexAxis: "y",
    scales: {
      x: { ticks: { color: "#9fb4ff" } },
      y: { ticks: { color: "#9fb4ff" } },
    },
    plugins: { legend: { display: false } },
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 800 },
    plugins: {
      legend: { display: true, labels: { color: "#e6eef8" } },
      tooltip: {
        callbacks: { label: (ctx) => `${ctx.label}` },
      },
    },
    scales: {
      y: { beginAtZero: true, ticks: { color: "#9fb4ff" } },
      x: { ticks: { color: "#9fb4ff" } },
    },
  };

  // --- JSX ---
  return (
    <div className="mt-10 flex flex-col gap-8 items-center w-full max-w-7xl px-4">
      {/* Summary Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 w-full">
        {[{ icon: Film, label: "Total Titles", value: recommendations.length },
          { icon: Star, label: "Avg Rating", value: avgRating.toFixed(1) },
          { icon: Layers, label: "Top Genre", value: topGenre }].map((card, i) => (
          <motion.div
            key={i}
            whileHover={{ scale: 1.03 }}
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="bg-slate-900 p-5 rounded-2xl shadow-lg flex items-center justify-between"
          >
            <div>
              <p className="text-gray-400 text-sm">{card.label}</p>
              <p className="text-cyan-300 text-2xl font-semibold mt-1">{card.value}</p>
            </div>
            <card.icon className="text-cyan-400 w-8 h-8" />
          </motion.div>
        ))}
      </div>

      {/* Existing two rows (same as before) */}
      <div className="flex flex-col lg:flex-row gap-8 w-full">
        <div className="w-full lg:w-2/3 bg-slate-900 rounded-2xl p-6 shadow-lg h-[460px]">
          <h3 className="text-xl font-semibold text-cyan-300 mb-4">
            🔍 Match Value by Title
          </h3>
          <div className="h-[360px]">
            <Bar data={barData} options={options} />
          </div>
        </div>

        <div className="w-full lg:w-1/3 bg-slate-900 rounded-2xl p-6 shadow-lg h-[460px] flex flex-col items-center">
          <h3 className="text-xl font-semibold text-purple-300 mb-4">🎯 Average Match</h3>
          <div className="w-[22rem] h-[22rem]">
            <Doughnut data={{
              labels: ["Average", "Remaining"],
              datasets: [{ data: [avgMatch, 100 - avgMatch], backgroundColor: ["#06b6d4", "#0f172a"] }]
            }} />
          </div>
          <p className="mt-4 text-cyan-200 font-semibold text-lg">{avgMatch.toFixed(1)}%</p>
        </div>
      </div>

      {/* Row 2 */}
      <div className="flex flex-col lg:flex-row gap-8 w-full">
        <div className="w-full lg:w-1/2 bg-slate-900 rounded-2xl p-6 shadow-lg h-[540px] flex justify-center items-center">
          <Pie data={genreChartData} options={{ plugins: { legend: { labels: { color: "#e6eef8" } } } }} />
        </div>
        <div className="w-full lg:w-1/2 bg-slate-900 rounded-2xl p-6 shadow-lg h-[480px]">
          <Bar data={ratingData} options={options} />
        </div>
      </div>

      {/* New Visuals */}
      <div className="flex flex-col lg:flex-row gap-8 w-full">
        <div className="w-full lg:w-1/2 bg-slate-900 rounded-2xl p-6 shadow-lg h-[460px]">
          <h3 className="text-xl font-semibold text-violet-300 mb-4">📈 Match Consistency</h3>
          <div className="h-[360px]">
            <Scatter data={scatterData} options={scatterOptions} />
          </div>
        </div>

        <div className="w-full lg:w-1/2 bg-slate-900 rounded-2xl p-6 shadow-lg h-[460px]">
          <h3 className="text-xl font-semibold text-amber-300 mb-4">🔥 Top Genres</h3>
          <div className="h-[360px]">
            <Bar data={topGenreBar} options={barOptions} />
          </div>
        </div>
      </div>
    </div>
  );
}
