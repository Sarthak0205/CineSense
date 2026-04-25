# =========================================================
# 🎨 CineSense: Model Performance Visualization
# Visual Comparison of TF-IDF + Cosine vs BERT + Cosine
# =========================================================

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# ---------------------------------------------------------
# 1️⃣ Load Results
# ---------------------------------------------------------
df = pd.read_csv("data/model_comparison_results.csv", index_col=0)
print("✅ Loaded Results:\n", df, "\n")

# ---------------------------------------------------------
# 2️⃣ Plot Style Configuration
# ---------------------------------------------------------
plt.style.use('dark_background')
plt.figure(figsize=(10, 6))
colors = ["#00bcd4", "#9c27b0"]  # Cyan & Purple (poster theme)

# ---------------------------------------------------------
# 3️⃣ Plot Bars
# ---------------------------------------------------------
metrics = df.columns
x = np.arange(len(metrics))
width = 0.35

plt.bar(x - width/2, df.loc["TF-IDF + Cosine"], width, label="TF-IDF + Cosine", color=colors[0])
plt.bar(x + width/2, df.loc["BERT + Cosine"], width, label="BERT + Cosine", color=colors[1])

# ---------------------------------------------------------
# 4️⃣ Styling & Labels
# ---------------------------------------------------------
plt.title("📊 Model Performance Comparison", fontsize=16, color="#00e5ff", pad=15)
plt.ylabel("Score", fontsize=12, color="white")
plt.xticks(x, metrics, rotation=0, fontsize=10, color="white")
plt.yticks(color="white")

# Annotate values on bars
for i in range(len(metrics)):
    plt.text(x[i] - width/2, df.loc["TF-IDF + Cosine", metrics[i]] + 0.01,
             f'{df.loc["TF-IDF + Cosine", metrics[i]]:.2f}', ha='center', color='white', fontsize=9)
    plt.text(x[i] + width/2, df.loc["BERT + Cosine", metrics[i]] + 0.01,
             f'{df.loc["BERT + Cosine", metrics[i]]:.2f}', ha='center', color='white', fontsize=9)

plt.legend(frameon=False, loc="upper right", fontsize=10)
plt.grid(axis='y', linestyle='--', alpha=0.3)
plt.tight_layout()

# ---------------------------------------------------------
# 5️⃣ Save & Show
# ---------------------------------------------------------
plt.savefig("data/performance_comparison_chart.png", dpi=300, bbox_inches="tight")
plt.show()

print("✅ Chart saved as: data/Picture2.png")
