import pandas as pd
import json
import os

#RAW_PATH = "../data/raw/RecipeNLG/split/recipes_part_0.csv"
RAW_PATH = "../data/raw/RecipeNLG/full_dataset.csv"
OUT_PATH = "../data/processed/recipes.json"

os.makedirs("../data/processed", exist_ok=True)

# Load CSV
df = pd.read_csv(RAW_PATH)

# Normalize column names (adjust if your CSV differs)
df = df.rename(columns={
    "title": "title",
    "ingredients": "ingredients",
    "directions": "instructions",  # sometimes it's "directions" in RecipeNLG
    "link": "link"
})

recipes = []
for idx, row in df.iterrows():
    title = str(row["title"]).strip()
    ingredients = row["ingredients"]
    instructions = row.get("instructions", "")
    link = row.get("link", "")

    # Parse ingredients (may be stored as a string list)
    if isinstance(ingredients, str):
        try:
            ingredients = json.loads(ingredients.replace("'", "\""))
        except:
            ingredients = [ingredients]

    # Build rich text field
    text = (
        f"Recipe Title: {title}. "
        f"Ingredients: {', '.join(ingredients) if isinstance(ingredients, list) else ingredients}. "
        f"Instructions: {instructions}"
        f"Link: {link}"
    )

    recipe = {
        "title": title,
        "ingredients": ingredients if isinstance(ingredients, list) else [str(ingredients)],
        "instructions": instructions,
        "text": text,  # <-- unified text field for embeddings
        "link": link
    }
    recipes.append(recipe)

# Save to JSON
with open(OUT_PATH, "w") as f:
    json.dump(recipes, f, indent=2)

print(f"✅ Saved {len(recipes)} recipes with rich text to {OUT_PATH}")
