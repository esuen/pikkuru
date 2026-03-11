import os
import random
import shutil
from pathlib import Path

# Set seed for reproducibility
random.seed(42)

# Source folders
game1_dir = Path("frames/eric_cindy_game_2")
game2_dir = Path("frames/eric_johnny_game_1")

# Output folders
output_dir = Path("frames/selected_frames")
game1_out = output_dir / "game1"
game2_out = output_dir / "game2"
game1_out.mkdir(parents=True, exist_ok=True)
game2_out.mkdir(parents=True, exist_ok=True)

# Number of frames to select
N = 170

def select_and_copy(src_dir, dst_dir, n):
    all_images = sorted([f for f in src_dir.iterdir() if f.suffix.lower() in [".jpg", ".jpeg", ".png"]])
    selected = random.sample(all_images, n)
    for img in selected:
        shutil.copy(img, dst_dir)
    return selected

# Select 170 frames from each game
selected_game1 = select_and_copy(game1_dir, game1_out, N)
selected_game2 = select_and_copy(game2_dir, game2_out, N)

print(f"✅ Selected {len(selected_game1)} from {game1_dir}")
print(f"✅ Selected {len(selected_game2)} from {game2_dir}")
