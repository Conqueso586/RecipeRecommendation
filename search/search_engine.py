import json
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub

# ---- Load fine-tuned encoder ----
encoder = hub.KerasLayer("models/fine_tuned", trainable=False)

def embed_texts(texts):
    return encoder(texts).numpy()

# ---- Load recipes ----
with open("/data/processed/recipes.json", "r") as f:
    recipes = json.load(f)

recipe_texts = [r["text"] for r in recipes]
recipe_embeddings = embed_texts(recipe_texts)

def search(query, top_k=5):
    q_vec = embed_texts([query])[0]
    sims = np.dot(recipe_embeddings, q_vec) / (
        np.linalg.norm(recipe_embeddings, axis=1) * np.linalg.norm(q_vec)
    )
    top_idx = sims.argsort()[-top_k:][::-1]
    return [
        {
            "title": recipes[i]["title"],
            "url": recipes[i]["url"],
            "score": float(sims[i])
        }
        for i in top_idx
    ]
