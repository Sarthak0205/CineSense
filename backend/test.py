# verify_recommendations.py
import pandas as pd
from hybrid_recommender import HybridRecommender

# Initialize model
model = HybridRecommender(dataset_path="data/final_dataset.csv")

# Titles to test (one from each category)
test_titles = [
    ("avengers", "movies"),
    ("money heist", "series"),
    ("naruto", "anime"),
    ("bleach", "anime"),
    ("the dark knight", "movies"),
]

results = []

for title, ctype in test_titles:
    print(f"\n🔹 Testing: {title} ({ctype})")
    recs = model.recommend(title, content_type=ctype, top_n=5)
    if isinstance(recs, pd.DataFrame) and not recs.empty:
        print(recs[["title", "genre", "similarity"]])
        avg_sim = recs["similarity"].mean()
        results.append({"title": title, "type": ctype, "avg_similarity": avg_sim})
    else:
        print("⚠️ No recommendations found.")

# Summary
print("\n📊 Summary of Average Similarity:")
print(pd.DataFrame(results))
