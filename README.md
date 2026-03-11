# Pickleball Rally Clipper

Video analysis pipeline that automatically extracts rally segments from pickleball game footage by tracking ball movement and player activity.

## How It Works

1. **Ball Detection** — A custom-trained YOLOv8 model detects the pickleball in each frame (runs every 2nd frame for performance)
2. **Position Interpolation** — Fills gaps between detections using linear interpolation
3. **Velocity Tracking** — Computes frame-to-frame ball velocity to determine when the ball is in play
4. **Activity Smoothing** — Applies grace periods and Schmitt trigger-style debouncing to clean up noisy active/inactive signals
5. **Rally Extraction** — Identifies rally segments based on sustained ball activity and exports a new video containing only the rallies
6. **Pose Estimation** — YOLOv8-Pose tracks player joint positions for future shot classification (working, not yet integrated into rally logic)

## Project Structure

```
main.py              # Entry point — orchestrates the full pipeline
config.py            # Tunable parameters (thresholds, debounce, buffer times)
models.py            # YOLO model loading with MPS/CUDA/CPU device selection
detection.py         # Ball detection and pose estimation inference
interpolation.py     # Linear interpolation for missing ball positions
activity.py          # Ball velocity check, activity smoothing, stance detection
rally.py             # Rally segment extraction from smoothed activity signal
export.py            # Video export with rally labels
render.py            # Debug visualization (ball trail, frame state overlay)
utils.py             # Helper functions (bounding box scaling)
capture_frames.py    # Extract frames from video for dataset creation
select_random_frames.py  # Sample frames for annotation
```

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install ultralytics opencv-python numpy tqdm
```

## Usage

```bash
python main.py path/to/game.mov
python main.py path/to/game.mov -o highlights.mp4
python main.py path/to/game.mov --confidence 0.4 --verbose
```

Options:

| Flag | Default | Description |
|------|---------|-------------|
| `-o, --output` | `rallies_only.mp4` | Output video path |
| `--inference-size W H` | `480 270` | Downscaled resolution for inference |
| `--confidence` | `0.3` | Ball detection confidence threshold |
| `--verbose` | off | Print activity transition debug info |

## Training Data

Ball detection was trained on a custom dataset annotated via [Roboflow](https://universe.roboflow.com/ball-ghj0j/ball-uqwhw) (CC BY 4.0). Two dataset versions are included:

- `datasetv1/` — 95 images, YOLOv8 format, 640x640
- `datasetv2/` — Expanded dataset

The trained model weights are at `runs/detect/ball/weights/best.pt`.

## Configuration

Key parameters in `config.py` (all time-based values are in seconds, converted to frames at runtime):

| Parameter | Default | Description |
|-----------|---------|-------------|
| `VEL_THRESH_PX_PER_FRAME` | 3.0 | Ball velocity threshold (px/frame) |
| `SEC_ACTIVE_DEBOUNCE` | 0.35s | Consecutive active frames to start rally |
| `SEC_INACTIVE_DEBOUNCE` | 0.25s | Consecutive inactive frames to end rally |
| `SEC_MIN_RALLY_LEN` | 1.00s | Minimum rally duration |
| `SEC_BUFFER_BEFORE` | 0.75s | Pre-rally buffer in output |
| `SEC_BUFFER_AFTER` | 0.75s | Post-rally buffer in output |
| `DETECT_EVERY_N_FRAMES` | 2 | Run detection every N frames |

## Status

In progress. Ball detection and pose estimation are working. Rally segment extraction is functional but needs tuning for accurate clip boundaries.

## License

MIT
