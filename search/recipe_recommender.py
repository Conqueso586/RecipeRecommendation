import json
import torch
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# ---- GPU Setup ----
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}\n")

# ---- Load the fine-tuned model ----
print("📦 Loading fine-tuned model...")
try:
    # Try loading best model first
    encoder = SentenceTransformer('../models/best_model/')
    print("✅ Loaded best model\n")
except:
    try:
        # Fallback to fine-tuned model
        encoder = SentenceTransformer('../models/fine_tuned/')
        print("✅ Loaded fine-tuned model\n")
    except:
        print("❌ Could not find fine-tuned model. Using base model instead.")
        encoder = SentenceTransformer('all-MiniLM-L6-v2')
        print("✅ Loaded base model\n")

encoder = encoder.to(device)
encoder.eval()

# ---- Load all recipes ----
print("📚 Loading recipe database...")
with open("../data/processed/recipes.json", "r") as f:
    recipes = json.load(f)
print(f"Loaded {len(recipes)} recipes\n")


# ---- Helper function to format recipe ----
def format_recipe(recipe):
    """Create a structured text representation of the recipe"""
    ingredients = ', '.join(recipe['ingredients'])
    instructions = ' '.join(json.loads(recipe['instructions']))
    return f"Title: {recipe['title']}. Ingredients: {ingredients}. Instructions: {instructions}"


# ---- Precompute embeddings for all recipes (optional but recommended for speed) ----
print("🔄 Computing embeddings for all recipes...")
recipe_texts = [format_recipe(recipe) for recipe in recipes]
recipe_embeddings = encoder.encode(recipe_texts, convert_to_tensor=True, device=device, show_progress_bar=True)
print("✅ Embeddings computed\n")


# ---- Main recommendation function ----
def find_similar_recipes(query_recipe, top_k=5, use_title_only=False, exclude_self=True,
                         exclude_domains=None, exclude_keywords=None):
    """
    Find similar recipes based on a query recipe.

    Args:
        query_recipe (dict): Recipe JSON object with 'title', 'ingredients', 'instructions', etc.
        top_k (int): Number of similar recipes to return
        use_title_only (bool): If True, only use the title for similarity (faster)
        exclude_self (bool): If True, exclude exact matches from results
        exclude_domains (list): List of domains/websites to exclude (e.g., ['example.com', 'site.org'])
        exclude_keywords (list): List of keywords to exclude from titles (e.g., ['vegan', 'gluten-free'])

    Returns:
        list: List of tuples (recipe, similarity_score)
    """
    # Format the query recipe
    if use_title_only:
        query_text = query_recipe['title']
    else:
        query_text = format_recipe(query_recipe)

    print(f"🔍 Searching for recipes similar to: '{query_recipe['title']}'")

    # Get embedding for query
    query_embedding = encoder.encode([query_text], convert_to_tensor=True, device=device)

    # Compute cosine similarities
    query_embedding_np = query_embedding.cpu().numpy()
    recipe_embeddings_np = recipe_embeddings.cpu().numpy()

    similarities = cosine_similarity(query_embedding_np, recipe_embeddings_np)[0]

    # Get top-k indices
    exclude_indices = []

    if exclude_self:
        # Find and exclude exact title matches
        query_title = query_recipe['title'].lower().strip()
        exclude_indices.extend([i for i, r in enumerate(recipes) if r['title'].lower().strip() == query_title])

    if exclude_domains:
        # Exclude recipes from specific domains
        exclude_domains_lower = [domain.lower() for domain in exclude_domains]
        for i, recipe in enumerate(recipes):
            if 'link' in recipe and recipe['link']:
                link_lower = recipe['link'].lower()
                if any(domain in link_lower for domain in exclude_domains_lower):
                    exclude_indices.append(i)

    if exclude_keywords:
        # Exclude recipes with specific keywords in title
        exclude_keywords_lower = [kw.lower() for kw in exclude_keywords]
        for i, recipe in enumerate(recipes):
            title_lower = recipe['title'].lower()
            if any(keyword in title_lower for keyword in exclude_keywords_lower):
                exclude_indices.append(i)

    # Remove duplicates from exclude list
    exclude_indices = list(set(exclude_indices))

    # Set similarity to -1 for excluded recipes
    for idx in exclude_indices:
        similarities[idx] = -1

    top_indices = np.argsort(similarities)[::-1][:top_k]

    # Return results with similarity scores
    results = []
    for idx in top_indices:
        if similarities[idx] > -1:  # Skip excluded recipes
            results.append({
                'recipe': recipes[idx],
                'similarity': float(similarities[idx])
            })

    return results


# ---- Display function ----
def display_recommendations(results, show_full_recipe=False):
    """Display the recommended recipes in a nice format"""
    print("\n" + "=" * 80)
    print(f"🍳 Top {len(results)} Similar Recipes:")
    print("=" * 80 + "\n")

    for i, result in enumerate(results, 1):
        recipe = result['recipe']
        similarity = result['similarity']

        print(f"{i}. {recipe['title']}")
        print(f"   Similarity Score: {similarity:.4f} ({similarity * 100:.1f}%)")

        # Always show the link if available
        if 'link' in recipe and recipe['link']:
            print(f"   🔗 Link: {recipe['link']}")

        if show_full_recipe:
            print(f"\n   Ingredients:")
            for ing in recipe['ingredients']:
                print(f"     • {ing}")

            print(f"\n   Instructions:")
            instructions = json.loads(recipe['instructions'])
            for j, step in enumerate(instructions, 1):
                print(f"     {j}. {step}")

        print("\n" + "-" * 80 + "\n")


# ---- Example Usage ----
if __name__ == "__main__":
    # Example 1: Find similar recipes using a recipe from the database
    print("=" * 80)
    print("EXAMPLE 1: Find similar recipes to an existing recipe")
    print("=" * 80)

    # Use the first recipe as an example
    example_recipe = recipes[0]
    print(f"\nQuery Recipe: {example_recipe['title']}\n")

    results = find_similar_recipes(example_recipe, top_k=5, exclude_self=True)
    display_recommendations(results, show_full_recipe=False)

    # Example 2: Find similar recipes using a custom recipe JSON
    print("\n\n" + "=" * 80)
    print("EXAMPLE 2: Find similar recipes to a custom recipe")
    print("=" * 80 + "\n")

    custom_recipe = {
        "title": "Chocolate Chip Cookies",
        "ingredients": [
            "2 cups all-purpose flour",
            "1 cup butter, softened",
            "3/4 cup sugar",
            "3/4 cup brown sugar",
            "2 eggs",
            "1 tsp vanilla extract",
            "1 tsp baking soda",
            "2 cups chocolate chips"
        ],
        "instructions": json.dumps([
            "Preheat oven to 375°F.",
            "Cream together butter and sugars until fluffy.",
            "Beat in eggs and vanilla.",
            "Mix in flour and baking soda.",
            "Stir in chocolate chips.",
            "Drop spoonfuls onto baking sheet.",
            "Bake for 10-12 minutes."
        ])
    }

    print(f"Query Recipe: {custom_recipe['title']}\n")

    results = find_similar_recipes(custom_recipe, top_k=5, exclude_self=False)
    display_recommendations(results, show_full_recipe=False)

    # Example 3: Search by title only (faster)
    print("\n\n" + "=" * 80)
    print("EXAMPLE 3: Quick search using title only")
    print("=" * 80 + "\n")

    quick_search_recipe = {
        "title": "Chocolate Cake",
        "ingredients": [],
        "instructions": "[]"
    }

    print(f"Query: {quick_search_recipe['title']}\n")

    results = find_similar_recipes(quick_search_recipe, top_k=5, use_title_only=True)
    display_recommendations(results, show_full_recipe=False)

    # Example 4: Exclude specific domains and keywords
    print("\n\n" + "=" * 80)
    print("EXAMPLE 4: Search with domain and keyword exclusions")
    print("=" * 80 + "\n")

    filtered_recipe = {
        "title": "Chicken Recipe",
        "ingredients": ["chicken", "salt", "pepper"],
        "instructions": '["Cook chicken"]'
    }

    print(f"Query: {filtered_recipe['title']}")
    print("Excluding: cookbooks.com domain and recipes with 'vegan' in title\n")

    results = find_similar_recipes(
        filtered_recipe,
        top_k=5,
        exclude_domains=['cookbooks.com'],
        exclude_keywords=['vegan', 'vegetarian']
    )
    display_recommendations(results, show_full_recipe=False)


# ---- Function for programmatic use ----
def get_recommendations(recipe_json, top_k=5, exclude_domains=None, exclude_keywords=None):
    """
    Simple wrapper function for getting recommendations.

    Args:
        recipe_json (dict): Recipe JSON object
        top_k (int): Number of recommendations
        exclude_domains (list): List of domains to exclude
        exclude_keywords (list): List of keywords to exclude from titles

    Returns:
        list: List of recommended recipes with similarity scores
    """
    return find_similar_recipes(recipe_json, top_k=top_k,
                                exclude_domains=exclude_domains,
                                exclude_keywords=exclude_keywords)