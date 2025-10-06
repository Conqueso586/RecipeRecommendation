import pandas as pd

CHUNK_SIZE = 10000  # number of rows per file
csv_path = "../data/raw/RecipeNLG/full_dataset.csv"
output_dir = "../data/raw/RecipeNLG/split/"

# Read in chunks
for i, chunk in enumerate(pd.read_csv(csv_path, chunksize=CHUNK_SIZE)):
    out_file = f"{output_dir}recipes_part_{i}.csv"
    chunk.to_csv(out_file, index=False)
    print(f"✅ Wrote {out_file} with {len(chunk)} rows")
