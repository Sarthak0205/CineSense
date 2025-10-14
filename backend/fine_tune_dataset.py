import pandas as pd
import numpy as np
import json

print("=" * 60)
print("🔧 CineSense Dataset Merger")
print("=" * 60)

# ============================================
# 1. LOAD TMDB MOVIES
# ============================================
print("\n📁 Loading TMDB Movies...")
try:
    # Try multiple possible paths
    movie_paths = [
        'tmdb_5000_movies.csv',
        'data/tmdb_5000_movies.csv',
        'tmdb_movies.csv',
        'data/tmdb_movies.csv'
    ]
    
    movies_df = None
    credits_df = None
    
    for path in movie_paths:
        try:
            movies_df = pd.read_csv(path)
            print(f"✅ Found movies at: {path}")
            break
        except FileNotFoundError:
            continue
    
    if movies_df is None:
        raise FileNotFoundError("Could not find TMDB movies file")
    
    # Try to load credits
    credit_paths = [
        'tmdb_5000_credits.csv',
        'data/tmdb_5000_credits.csv',
        'credits.csv',
        'data/credits.csv'
    ]
    
    for path in credit_paths:
        try:
            credits_df = pd.read_csv(path)
            print(f"✅ Found credits at: {path}")
            break
        except FileNotFoundError:
            continue
    print(f"✅ Loaded {len(movies_df)} movies")
    print(f"   Columns: {list(movies_df.columns)}")
    
    # Merge credits if available
    if credits_df is not None and 'movie_id' in credits_df.columns and 'id' in movies_df.columns:
        movies_df = movies_df.merge(credits_df, left_on='id', right_on='movie_id', how='left')
        print("✅ Merged with credits data")
    
    # Extract genre names from JSON format
    def parse_genres(genre_str):
        try:
            if pd.isna(genre_str) or genre_str == '':
                return ''
            genres = json.loads(genre_str.replace("'", '"'))
            return '|'.join([g['name'] for g in genres if 'name' in g])
        except:
            return ''
    
    if 'genres' in movies_df.columns:
        movies_df['genre_parsed'] = movies_df['genres'].apply(parse_genres)
    
    # Create clean movies dataframe
    movies_clean = pd.DataFrame({
        'title': movies_df['title'] if 'title' in movies_df.columns else movies_df['original_title'],
        'type': 'movie',
        'genre': movies_df['genre_parsed'] if 'genre_parsed' in movies_df.columns else '',
        'description': movies_df['overview'] if 'overview' in movies_df.columns else '',
        'rating': movies_df['vote_average'] if 'vote_average' in movies_df.columns else 0
    })
    
    print(f"✅ Processed {len(movies_clean)} movies")
    
except FileNotFoundError as e:
    print(f"⚠️ Movie files not found: {e}")
    movies_clean = pd.DataFrame(columns=['title', 'type', 'genre', 'description', 'rating'])
except Exception as e:
    print(f"❌ Error loading movies: {e}")
    movies_clean = pd.DataFrame(columns=['title', 'type', 'genre', 'description', 'rating'])

# ============================================
# 2. LOAD ANIME DATA
# ============================================
print("\n📁 Loading Anime...")
try:
    # Try multiple possible paths
    anime_paths = [
        'anime.csv',
        'data/anime.csv',
        'rating.csv',
        'data/rating.csv'
    ]
    
    anime_df = None
    for path in anime_paths:
        try:
            df = pd.read_csv(path)
            # Check if this looks like anime data (has 'name' or 'anime_id' column)
            if 'name' in df.columns or 'anime_id' in df.columns:
                anime_df = df
                print(f"✅ Found anime at: {path}")
                break
        except FileNotFoundError:
            continue
    
    if anime_df is None:
        raise FileNotFoundError("Could not find anime file")
    
    print(f"✅ Loaded {len(anime_df)} anime")
    print(f"   Columns: {list(anime_df.columns)}")
    
    # Determine column names (different datasets use different names)
    title_col = 'name' if 'name' in anime_df.columns else 'title'
    genre_col = 'genre' if 'genre' in anime_df.columns else 'genres'
    desc_col = 'synopsis' if 'synopsis' in anime_df.columns else 'description' if 'description' in anime_df.columns else 'overview'
    rating_col = 'rating' if 'rating' in anime_df.columns else 'score' if 'score' in anime_df.columns else 'vote_average'
    
    # Create clean anime dataframe
    anime_clean = pd.DataFrame({
        'title': anime_df[title_col] if title_col in anime_df.columns else '',
        'type': 'anime',
        'genre': anime_df[genre_col] if genre_col in anime_df.columns else '',
        'description': anime_df[desc_col] if desc_col in anime_df.columns else '',
        'rating': anime_df[rating_col] if rating_col in anime_df.columns else 0
    })
    
    print(f"✅ Processed {len(anime_clean)} anime")
    
except FileNotFoundError as e:
    print(f"⚠️ Anime file not found: {e}")
    anime_clean = pd.DataFrame(columns=['title', 'type', 'genre', 'description', 'rating'])
except Exception as e:
    print(f"❌ Error loading anime: {e}")
    anime_clean = pd.DataFrame(columns=['title', 'type', 'genre', 'description', 'rating'])

# ============================================
# 3. LOAD TV SERIES (if you have it)
# ============================================
print("\n📁 Looking for TV Series data...")
try:
    # Try common TV series filenames
    series_filenames = [
        'titles.csv', 
        'data/titles.csv',
        'netflix_titles.csv',
        'data/netflix_titles.csv',
        'tv_shows.csv',
        'data/tv_shows.csv'
    ]
    series_df = None
    
    for filename in series_filenames:
        try:
            series_df = pd.read_csv(filename)
            print(f"✅ Found {filename} with {len(series_df)} entries")
            break
        except FileNotFoundError:
            continue
    
    if series_df is not None:
        print(f"   Columns: {list(series_df.columns)}")
        
        # Filter for TV shows only if type column exists
        if 'type' in series_df.columns:
            original_count = len(series_df)
            # Convert to uppercase for comparison to handle case variations
            series_df = series_df[series_df['type'].str.upper().isin(['SHOW', 'TV SHOW', 'TV SERIES', 'SERIES'])]
            print(f"   Filtered to {len(series_df)} TV shows from {original_count} total")
        
        # Determine column names
        title_col = 'title' if 'title' in series_df.columns else 'name'
        
        # For genres, handle multiple possible column names
        if 'genres' in series_df.columns:
            genre_col = 'genres'
        elif 'listed_in' in series_df.columns:
            genre_col = 'listed_in'
        elif 'genre' in series_df.columns:
            genre_col = 'genre'
        else:
            genre_col = None
        
        desc_col = 'description' if 'description' in series_df.columns else 'overview' if 'overview' in series_df.columns else 'synopsis'
        
        # Handle rating - try multiple column names
        if 'imdb_score' in series_df.columns:
            rating_col = 'imdb_score'
        elif 'tmdb_score' in series_df.columns:
            rating_col = 'tmdb_score'
        elif 'rating' in series_df.columns:
            rating_col = 'rating'
        else:
            rating_col = None
        
        series_clean = pd.DataFrame({
            'title': series_df[title_col] if title_col in series_df.columns else '',
            'type': 'series',
            'genre': series_df[genre_col] if genre_col and genre_col in series_df.columns else '',
            'description': series_df[desc_col] if desc_col in series_df.columns else '',
            'rating': series_df[rating_col] if rating_col and rating_col in series_df.columns else 0
        })
        
        # Remove empty rows
        series_clean = series_clean[series_clean['title'].notna()]
        series_clean = series_clean[series_clean['title'].str.strip() != '']
        
        print(f"✅ Processed {len(series_clean)} series")
    else:
        print("⚠️ No TV series data found - skipping")
        series_clean = pd.DataFrame(columns=['title', 'type', 'genre', 'description', 'rating'])
        
except Exception as e:
    print(f"⚠️ Could not load series data: {e}")
    series_clean = pd.DataFrame(columns=['title', 'type', 'genre', 'description', 'rating'])

# ============================================
# 4. COMBINE ALL DATASETS
# ============================================
print("\n🔄 Combining datasets...")
combined = pd.concat([movies_clean, anime_clean, series_clean], ignore_index=True)

print(f"✅ Combined total: {len(combined)} items")

# ============================================
# 5. CLEAN AND VALIDATE DATA
# ============================================
print("\n🧹 Cleaning data...")

# Remove rows with no title
combined = combined[combined['title'].notna()]
combined = combined[combined['title'].str.strip() != '']
print(f"   - After removing empty titles: {len(combined)} items")

# Remove duplicates
before = len(combined)
combined = combined.drop_duplicates(subset=['title'], keep='first')
print(f"   - Removed {before - len(combined)} duplicates")

# Fill missing values
combined['description'] = combined['description'].fillna('')
combined['genre'] = combined['genre'].fillna('Unknown')
combined['rating'] = pd.to_numeric(combined['rating'], errors='coerce').fillna(0)

# Clean genre field (remove extra spaces, commas)
combined['genre'] = combined['genre'].str.replace(', ', '|')
combined['genre'] = combined['genre'].str.replace(',', '|')

# Convert rating to 0-10 scale if needed
if combined['rating'].max() > 10:
    print("   - Converting ratings to 0-10 scale")
    combined['rating'] = combined['rating'] / combined['rating'].max() * 10

# ============================================
# 6. SHOW STATISTICS
# ============================================
print("\n" + "=" * 60)
print("📊 DATASET STATISTICS")
print("=" * 60)
print(f"\nTotal items: {len(combined)}")
print(f"\nBreakdown by type:")
type_counts = combined['type'].value_counts()
for content_type, count in type_counts.items():
    print(f"   - {content_type}: {count}")

print(f"\nRating statistics:")
print(f"   - Average: {combined['rating'].mean():.2f}")
print(f"   - Min: {combined['rating'].min():.2f}")
print(f"   - Max: {combined['rating'].max():.2f}")

print(f"\nTop genres:")
all_genres = combined['genre'].str.split('|').explode()
top_genres = all_genres.value_counts().head(10)
for genre, count in top_genres.items():
    print(f"   - {genre}: {count}")

print(f"\nSample titles:")
for content_type in combined['type'].unique():
    sample = combined[combined['type'] == content_type].head(3)
    print(f"\n   {content_type.upper()}:")
    for _, row in sample.iterrows():
        print(f"      • {row['title']} ({row['rating']:.1f}/10)")

# ============================================
# 7. SAVE COMBINED DATASET
# ============================================
print("\n" + "=" * 60)
output_file = 'unified_content.csv'
combined.to_csv(output_file, index=False, encoding='utf-8')
print(f"✅ Saved to: {output_file}")
print("=" * 60)

print("\n🎉 Done! You can now use this with your recommender:")
print(f"   model = CineSenseModel('{output_file}', n_clusters=20)")
print("\n" + "=" * 60)