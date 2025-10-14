import { useState } from "react";
import LandingPage from "./components/LandingPage";
import RecommendPage from "./components/RecommendPage";

export default function App() {
  const [page, setPage] = useState("landing");
  const [category, setCategory] = useState("movies");

  return (
    <>
      {page === "landing" ? (
        <LandingPage
          onSelectCategory={(selected) => {
            setCategory(selected);
            setPage("recommend");
          }}
        />
      ) : (
        <RecommendPage category={category} onBack={() => setPage("landing")} />
      )}
    </>
  );
}
