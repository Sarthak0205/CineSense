from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

recommendations_data = {
    "movies": [
        {"title": "Inception", "rating": 8.8, "genre": "Sci-Fi", "poster": "inception.jpg"},
        {"title": "Interstellar", "rating": 8.6, "genre": "Adventure", "poster": "interstellar.jpg"},
        {"title": "Oppenheimer", "rating": 8.5, "genre": "Drama", "poster": "Oppenheimer.jpg"},
    ],
    "series": [
        {"title": "Breaking Bad", "rating": 9.5, "genre": "Crime", "poster": "Breaking-Bad.jpg"},
        {"title": "Game of Thrones", "rating": 9.0, "genre": "Fantasy", "poster": "GOT.jpg"},
    ],
    "anime": [
        {"title": "Attack on Titan", "rating": 9.1, "genre": "Action", "poster": "AOT.jpg"},
        {"title": "Demon Slayer", "rating": 8.8, "genre": "Adventure", "poster": "demon-slayer.jpg"},
    ],
}

@app.get("/recommend")
def get_recommendations(type: str):
    type = type.lower()
    if type in recommendations_data:
        return recommendations_data[type]
    return {"error": "Invalid category"}
