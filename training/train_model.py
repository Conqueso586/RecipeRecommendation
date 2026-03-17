import json
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sentence_transformers import SentenceTransformer
from torch.optim.lr_scheduler import CosineAnnealingLR
from sklearn.model_selection import train_test_split
import random
import os
import pickle
from datetime import datetime

# ---- Configuration ----
BATCH_SIZE = 32  # Increased for efficiency with large dataset
LEARNING_RATE = 2e-5
EPOCHS_PER_SESSION = 3  # Train for 3 epochs per session
MARGIN = 0.5
NEGATIVES_PER_QUERY = 2
VAL_SPLIT = 0.05  # Smaller validation set for large datasets
PATIENCE = 5
MAX_GRAD_NORM = 1.0
RANDOM_SEED = 42

# Data processing settings
CHUNK_SIZE = 10000  # Process 100k recipes at a time
MAX_RECIPES_PER_SESSION = 100000  # Train on 500k recipes per session
SHUFFLE_DATA = True

# Checkpoint settings
CHECKPOINT_DIR = "../models/checkpoints"
RESUME_FROM_CHECKPOINT = True  # Set to False to start fresh

# Set random seeds
random.seed(RANDOM_SEED)
torch.manual_seed(RANDOM_SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed(RANDOM_SEED)

# ---- GPU Setup ----
print("=" * 80)
print("INCREMENTAL TRAINING SETUP")
print("=" * 80)
print(f"\nPyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU name: {torch.cuda.get_device_name(0)}")
    device = torch.device("cuda:0")
    print(f"✅ Using GPU: {device}")
else:
    device = torch.device("cpu")
    print(f"❌ No GPU found, using CPU")

# Create directories
os.makedirs(CHECKPOINT_DIR, exist_ok=True)
os.makedirs("../models/fine_tuned", exist_ok=True)
os.makedirs("../models/best_model", exist_ok=True)


# ---- Helper function to format recipe text ----
def format_recipe(recipe):
    """Create a structured text representation of the recipe"""
    try:
        ingredients = ', '.join(recipe['ingredients'])
        instructions = ' '.join(
            json.loads(recipe['instructions']) if isinstance(recipe['instructions'], str) else recipe['instructions'])
        return f"Title: {recipe['title']}. Ingredients: {ingredients}. Instructions: {instructions}"
    except Exception as e:
        # Fallback if formatting fails
        return f"Title: {recipe['title']}. {str(recipe)}"


# ---- Load or create training state ----
def load_training_state():
    """Load the training state from checkpoint"""
    state_path = os.path.join(CHECKPOINT_DIR, "training_state.pkl")

    if RESUME_FROM_CHECKPOINT and os.path.exists(state_path):
        print("\n📂 Loading training state from checkpoint...")
        with open(state_path, "rb") as f:
            state = pickle.load(f)
        print(f"✅ Resumed from session {state['session_number']}")
        print(f"   Total recipes processed: {state['recipes_processed']}")
        print(f"   Best validation loss: {state['best_val_loss']:.4f}")
        return state
    else:
        print("\n🆕 Starting fresh training session...")
        return {
            'session_number': 0,
            'recipes_processed': 0,
            'total_epochs_trained': 0,
            'best_val_loss': float('inf'),
            'training_history': []
        }


def save_training_state(state):
    """Save the training state to checkpoint"""
    state_path = os.path.join(CHECKPOINT_DIR, "training_state.pkl")
    with open(state_path, "wb") as f:
        pickle.dump(state, f)
    print(f"💾 Training state saved")


# ---- Load dataset in chunks ----
def load_recipe_chunk(start_idx, chunk_size):
    """Load a chunk of recipes from the JSON file"""
    print(f"\n📚 Loading recipes {start_idx} to {start_idx + chunk_size}...")

    with open("../data/processed/recipes.json", "r") as f:
        recipes = json.load(f)

    total_recipes = len(recipes)
    end_idx = min(start_idx + chunk_size, total_recipes)

    chunk = recipes[start_idx:end_idx]

    print(f"✅ Loaded {len(chunk)} recipes (Total in dataset: {total_recipes})")
    return chunk, total_recipes


# ---- Generate training triplets ----
def generate_triplets(recipes, num_samples=None):
    """Generate training triplets from recipes"""
    print(f"\n🔄 Generating training triplets...")

    if num_samples and num_samples < len(recipes):
        recipes = random.sample(recipes, num_samples)
        print(f"   Sampling {num_samples} recipes from chunk")

    train_data = []
    for i, recipe in enumerate(recipes):
        try:
            query = recipe["title"]
            positive = format_recipe(recipe)

            # Generate multiple random negatives per query
            available_indices = [j for j in range(len(recipes)) if j != i]
            neg_indices = random.sample(available_indices, min(NEGATIVES_PER_QUERY, len(available_indices)))

            for neg_idx in neg_indices:
                negative = format_recipe(recipes[neg_idx])
                train_data.append((query, positive, negative))
        except Exception as e:
            print(f"   Warning: Skipped recipe {i} due to error: {e}")
            continue

        if (i + 1) % 10000 == 0:
            print(f"   Processed {i + 1}/{len(recipes)} recipes...")

    print(f"✅ Generated {len(train_data)} training triplets")
    return train_data


# ---- Custom Dataset ----
class TripletDataset(Dataset):
    def __init__(self, triplets):
        self.triplets = triplets

    def __len__(self):
        return len(self.triplets)

    def __getitem__(self, idx):
        return self.triplets[idx]


# ---- Triplet Loss ----
def triplet_loss(q, p, n, margin=MARGIN):
    """Compute triplet loss"""
    pos_dist = torch.sum((q - p) ** 2, dim=1)
    neg_dist = torch.sum((q - n) ** 2, dim=1)
    loss = torch.mean(torch.clamp(pos_dist - neg_dist + margin, min=0.0))
    return loss


# ---- Evaluation Function ----
def evaluate(model, val_loader, device):
    """Evaluate the model on validation set"""
    model.eval()
    total_loss = 0
    num_batches = 0

    with torch.no_grad():
        for batch in val_loader:
            queries, positives, negatives = batch

            q_inputs = model.tokenizer(queries, padding=True, truncation=True, return_tensors='pt', max_length=512)
            p_inputs = model.tokenizer(positives, padding=True, truncation=True, return_tensors='pt', max_length=512)
            n_inputs = model.tokenizer(negatives, padding=True, truncation=True, return_tensors='pt', max_length=512)

            q_inputs = {k: v.to(device) for k, v in q_inputs.items()}
            p_inputs = {k: v.to(device) for k, v in p_inputs.items()}
            n_inputs = {k: v.to(device) for k, v in n_inputs.items()}

            q_emb = model(q_inputs)['sentence_embedding']
            p_emb = model(p_inputs)['sentence_embedding']
            n_emb = model(n_inputs)['sentence_embedding']

            loss = triplet_loss(q_emb, p_emb, n_emb)
            total_loss += loss.item()
            num_batches += 1

    model.train()
    return total_loss / num_batches if num_batches > 0 else float('inf')


# ---- Main Training Function ----
def train_session(state):
    """Train for one session"""

    session_num = state['session_number'] + 1
    start_recipe_idx = state['recipes_processed']

    print("\n" + "=" * 80)
    print(f"TRAINING SESSION {session_num}")
    print("=" * 80)
    print(f"Starting from recipe index: {start_recipe_idx}")
    print(f"Max recipes this session: {MAX_RECIPES_PER_SESSION}")
    print(f"Epochs per session: {EPOCHS_PER_SESSION}")

    # Load recipe chunk
    recipes_chunk, total_recipes = load_recipe_chunk(start_recipe_idx, MAX_RECIPES_PER_SESSION)

    if len(recipes_chunk) == 0:
        print("\n✅ All recipes have been processed!")
        return state, True  # Return True to indicate completion

    # Generate triplets
    train_data = generate_triplets(recipes_chunk)

    # Split train/val
    print(f"\n📊 Splitting data (validation: {VAL_SPLIT * 100}%)...")
    train_triplets, val_triplets = train_test_split(train_data, test_size=VAL_SPLIT, random_state=RANDOM_SEED)
    print(f"Training triplets: {len(train_triplets)}")
    print(f"Validation triplets: {len(val_triplets)}")

    train_dataset = TripletDataset(train_triplets)
    val_dataset = TripletDataset(val_triplets)

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False)

    # Load or create model
    checkpoint_path = os.path.join(CHECKPOINT_DIR, "model_checkpoint")

    if RESUME_FROM_CHECKPOINT and os.path.exists(checkpoint_path):
        print(f"\n🤖 Loading model from checkpoint...")
        encoder = SentenceTransformer(checkpoint_path)
        print(f"✅ Model loaded from checkpoint")
    else:
        print(f"\n🤖 Loading base model...")
        encoder = SentenceTransformer('all-MiniLM-L6-v2')
        print(f"✅ Base model loaded")

    encoder = encoder.to(device)

    # Setup optimizer and scheduler
    optimizer = torch.optim.Adam(encoder.parameters(), lr=LEARNING_RATE)
    scheduler = CosineAnnealingLR(optimizer, T_max=EPOCHS_PER_SESSION * len(train_loader))

    # Load optimizer state if resuming
    optimizer_path = os.path.join(CHECKPOINT_DIR, "optimizer_state.pt")
    if RESUME_FROM_CHECKPOINT and os.path.exists(optimizer_path):
        print(f"📂 Loading optimizer state...")
        optimizer.load_state_dict(torch.load(optimizer_path))

    # Training loop
    print(f"\n🚀 Starting training...")
    print(f"Batch size: {BATCH_SIZE}, Learning rate: {LEARNING_RATE}, Margin: {MARGIN}\n")

    best_val_loss = state['best_val_loss']
    patience_counter = 0

    encoder.train()
    for epoch in range(EPOCHS_PER_SESSION):
        total_loss = 0
        num_batches = 0

        for batch_idx, batch in enumerate(train_loader):
            queries, positives, negatives = batch

            # Tokenize
            q_inputs = encoder.tokenizer(queries, padding=True, truncation=True, return_tensors='pt', max_length=512)
            p_inputs = encoder.tokenizer(positives, padding=True, truncation=True, return_tensors='pt', max_length=512)
            n_inputs = encoder.tokenizer(negatives, padding=True, truncation=True, return_tensors='pt', max_length=512)

            # Move to device
            q_inputs = {k: v.to(device) for k, v in q_inputs.items()}
            p_inputs = {k: v.to(device) for k, v in p_inputs.items()}
            n_inputs = {k: v.to(device) for k, v in n_inputs.items()}

            # Forward pass
            q_emb = encoder(q_inputs)['sentence_embedding']
            p_emb = encoder(p_inputs)['sentence_embedding']
            n_emb = encoder(n_inputs)['sentence_embedding']

            # Compute loss
            loss = triplet_loss(q_emb, p_emb, n_emb)

            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(encoder.parameters(), max_norm=MAX_GRAD_NORM)
            optimizer.step()
            scheduler.step()

            total_loss += loss.item()
            num_batches += 1

            if (batch_idx + 1) % 100 == 0:
                print(f"  Batch {batch_idx + 1}/{len(train_loader)} - Loss: {loss.item():.4f}")

        avg_train_loss = total_loss / num_batches
        val_loss = evaluate(encoder, val_loader, device)

        print(f"\n{'=' * 60}")
        print(f"Epoch {epoch + 1}/{EPOCHS_PER_SESSION}")
        print(f"  Train Loss: {avg_train_loss:.4f}")
        print(f"  Val Loss:   {val_loss:.4f}")
        print(f"  Learning Rate: {scheduler.get_last_lr()[0]:.6f}")
        print(f"{'=' * 60}\n")

        # Save best model
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            encoder.save("../models/best_model/")
            print(f"✅ New best model saved! (Val Loss: {val_loss:.4f})\n")
            patience_counter = 0
        else:
            patience_counter += 1

    # Save checkpoint
    print(f"\n💾 Saving checkpoint...")
    encoder.save(checkpoint_path)
    torch.save(optimizer.state_dict(), optimizer_path)

    # Update state
    state['session_number'] = session_num
    state['recipes_processed'] = start_recipe_idx + len(recipes_chunk)
    state['total_epochs_trained'] += EPOCHS_PER_SESSION
    state['best_val_loss'] = best_val_loss
    state['training_history'].append({
        'session': session_num,
        'recipes_processed': state['recipes_processed'],
        'best_val_loss': best_val_loss,
        'timestamp': datetime.now().isoformat()
    })

    save_training_state(state)

    # Check if we've processed all recipes
    is_complete = state['recipes_processed'] >= total_recipes

    print(f"\n{'=' * 80}")
    print(f"SESSION {session_num} COMPLETE")
    print(f"{'=' * 80}")
    print(f"Recipes processed this session: {len(recipes_chunk)}")
    print(f"Total recipes processed: {state['recipes_processed']}/{total_recipes}")
    print(f"Progress: {(state['recipes_processed'] / total_recipes) * 100:.1f}%")
    print(f"Best validation loss: {best_val_loss:.4f}")
    print(f"{'=' * 80}\n")

    return state, is_complete


# ---- Main execution ----
if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("LARGE-SCALE INCREMENTAL TRAINING")
    print("=" * 80)
    print(f"\nConfiguration:")
    print(f"  Max recipes per session: {MAX_RECIPES_PER_SESSION:,}")
    print(f"  Epochs per session: {EPOCHS_PER_SESSION}")
    print(f"  Batch size: {BATCH_SIZE}")
    print(f"  Resume from checkpoint: {RESUME_FROM_CHECKPOINT}")

    # Load training state
    state = load_training_state()

    # Run training session
    state, is_complete = train_session(state)

    if is_complete:
        print("\n" + "=" * 80)
        print("🎉 TRAINING COMPLETE!")
        print("=" * 80)
        print(f"Total sessions: {state['session_number']}")
        print(f"Total recipes processed: {state['recipes_processed']:,}")
        print(f"Total epochs trained: {state['total_epochs_trained']}")
        print(f"Best validation loss: {state['best_val_loss']:.4f}")
        print(f"\n✅ Best model saved at: ../models/best_model/")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("⏸️  SESSION PAUSED")
        print("=" * 80)
        print(f"Run this script again to continue training from session {state['session_number'] + 1}")
        print(f"Progress: {(state['recipes_processed'] / 2200000) * 100:.1f}% (estimated)")
        print("=" * 80)