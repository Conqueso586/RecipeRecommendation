import json
import tensorflow as tf
import tensorflow_hub as hub


print("TensorFlow version:", tf.__version__)
print("Built with CUDA:", tf.test.is_built_with_cuda())
print("GPU devices:", tf.config.list_physical_devices("GPU"))

gpus = tf.config.list_physical_devices('GPU')
if gpus:
    try:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
        tf.config.set_visible_devices(gpus[0], 'GPU')
        print("✅ Using GPU:", gpus[0])
    except RuntimeError as e:
        print("GPU error:", e)
else:
    print("❌ No GPU found")
# ---- Load dataset ----
with open("../data/processed/recipes.json", "r") as f:
    recipes = json.load(f)

train_data = []
for i, recipe in enumerate(recipes):
    query = recipe["title"]
    positive = recipe["text"]
    negative = recipes[(i + 1) % len(recipes)]["text"]  # simple negative
    train_data.append((query, positive, negative))

queries, positives, negatives = zip(*train_data)
dataset = tf.data.Dataset.from_tensor_slices(
    (list(queries), list(positives), list(negatives))
).shuffle(2000).batch(16)

# ---- Encoder ----
encoder = hub.KerasLayer("https://tfhub.dev/google/universal-sentence-encoder/4", trainable=True)

# ---- Triplet Loss ----
def triplet_loss(q, p, n, margin=0.2):
    pos_dist = tf.reduce_sum(tf.square(q - p), axis=1)
    neg_dist = tf.reduce_sum(tf.square(q - n), axis=1)
    return tf.reduce_mean(tf.maximum(pos_dist - neg_dist + margin, 0.0))

# ---- Custom Model ----
class TripletModel(tf.keras.Model):
    def __init__(self, encoder):
        super().__init__()
        self.encoder = encoder

    def train_step(self, data):
        q, p, n = data  # unpack batch
        with tf.GradientTape() as tape:
            q_emb = self.encoder(q, training=True)
            p_emb = self.encoder(p, training=True)
            n_emb = self.encoder(n, training=True)
            loss = triplet_loss(q_emb, p_emb, n_emb)

        grads = tape.gradient(loss, self.encoder.trainable_variables)
        self.optimizer.apply_gradients(zip(grads, self.encoder.trainable_variables))
        return {"loss": loss}

# ---- Train ----
model = TripletModel(encoder)
model.compile(optimizer=tf.keras.optimizers.Adam(1e-5))
model.fit(dataset, epochs=3)

# ---- Save encoder ----
encoder.save("models/fine_tuned/")
print("✅ Fine-tuned model saved at models/fine_tuned/")
