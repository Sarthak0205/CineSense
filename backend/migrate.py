import pymongo
from bson import ObjectId
import pprint

# ⚙️ Update if your DB settings differ
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "cinesense"  # change if needed

client = pymongo.MongoClient(MONGO_URI)
db = client[DB_NAME]
users = db.users

pp = pprint.PrettyPrinter(indent=2)


def normalize_type(t):
    """Ensure consistent lowercase category names."""
    t = (t or "").lower().strip()
    if "anime" in t:
        return "anime"
    elif t in ["tv", "series", "show"]:
        return "series"
    else:
        return "movies"


def normalize_user_favorites(user):
    """Normalize favorites structure for one user."""
    fav_data = user.get("favorites", [])
    grouped = {"movies": [], "series": [], "anime": []}

    # 🧹 Handle both list-based and dict-based favorites
    if isinstance(fav_data, list):
        for f in fav_data:
            ftype = normalize_type(f.get("type"))
            grouped[ftype].append(f)
    elif isinstance(fav_data, dict):
        for key in ["movies", "series", "anime"]:
            for f in fav_data.get(key, []):
                ftype = normalize_type(f.get("type"))
                grouped[ftype].append(f)

    # 🔁 Deduplicate by title
    for cat in grouped:
        seen = set()
        unique = []
        for f in grouped[cat]:
            title = f.get("title")
            if title and title not in seen:
                seen.add(title)
                f["_id"] = str(ObjectId())
                f["type"] = cat
                unique.append(f)
        grouped[cat] = unique

    return grouped


def run_normalization(preview=True):
    users_cursor = users.find({})
    updated_count = 0

    for user in users_cursor:
        user_id = str(user["_id"])
        print("\n" + "=" * 70)
        print(f"👤 Processing user: {user.get('username', '(no username)')} ({user_id})")
        print("-" * 70)
        print("Before:")
        pp.pprint(user.get("favorites", {}))

        normalized = normalize_user_favorites(user)

        print("\nAfter normalization:")
        pp.pprint(normalized)

        if preview:
            choice = input("\n✅ Apply changes for this user? (y/n/all/quit): ").strip().lower()
            if choice == "quit":
                print("\n🛑 Aborting normalization process.")
                break
            elif choice == "n":
                print("⏩ Skipping this user.")
                continue
            elif choice == "all":
                preview = False  # automatically apply for the rest
                print("🔄 Applying changes for all remaining users.")

        users.update_one({"_id": user["_id"]}, {"$set": {"favorites": normalized}})
        print("✅ Updated successfully.")
        updated_count += 1

    print(f"\n🎉 Normalization complete. Updated {updated_count} user(s).")


if __name__ == "__main__":
    run_normalization(preview=True)
