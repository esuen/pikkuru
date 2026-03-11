import argparse
import cv2

from tqdm import tqdm
from config import *
from models import load_models
from detection import detect_ball
from interpolation import interpolate_ball_positions
from activity import is_ball_active, smooth_ball_active
from rally import extract_rallies
from export import export_rallies_only_video
from utils import scale_box


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract rally segments from pickleball game footage"
    )
    parser.add_argument("video", help="Path to input video file")
    parser.add_argument(
        "-o", "--output", default="rallies_only.mp4",
        help="Output video path (default: rallies_only.mp4)",
    )
    parser.add_argument(
        "--inference-size", type=int, nargs=2, default=[480, 270],
        metavar=("W", "H"),
        help="Downscaled resolution for inference (default: 480 270)",
    )
    parser.add_argument(
        "--confidence", type=float, default=0.3,
        help="Ball detection confidence threshold (default: 0.3)",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Print frame-by-frame activity transitions",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    ball_positions = {}
    ball_active = {}
    ball_detected = {}

    ball_model, _, _ = load_models()

    # Video setup
    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        print(f"Error: could not open video '{args.video}'")
        return

    fps = cap.get(cv2.CAP_PROP_FPS) or 120
    set_fps(fps)

    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    target_width, target_height = args.inference_size
    frame_idx = 0
    ball_names = ball_model.names

    # --- Pass 1: Detect ball positions ---
    with tqdm(
        total=frame_count if frame_count > 0 else None,
        desc="Detecting ball",
        unit="frame",
    ) as pbar:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            resized_frame = cv2.resize(frame, (target_width, target_height))
            scale_x = frame.shape[1] / target_width
            scale_y = frame.shape[0] / target_height

            # Run detection on every Nth frame, interpolate the rest
            detected = False
            if frame_idx % DETECT_EVERY_N_FRAMES == 0:
                ball_results = detect_ball(ball_model, resized_frame)
                for box in ball_results.boxes:
                    cls = ball_names[int(box.cls)]
                    if cls == "ball" and box.conf[0] > args.confidence:
                        xyxy = scale_box(box.xyxy[0].tolist(), scale_x, scale_y)
                        x_center = (xyxy[0] + xyxy[2]) / 2
                        y_center = (xyxy[1] + xyxy[3]) / 2
                        ball_positions[frame_idx] = (x_center, y_center)
                        ball_detected[frame_idx] = True
                        detected = True
                        break
            else:
                ball_detected[frame_idx] = False

            # Preliminary activity check (velocity only)
            ball_active[frame_idx] = (
                is_ball_active(frame_idx, ball_positions, []) if detected else False
            )

            frame_idx += 1
            pbar.update(1)
            if frame_idx % 30 == 0:
                pbar.set_postfix(
                    det=detected, active=ball_active.get(frame_idx - 1, False)
                )

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cap.release()
    cv2.destroyAllWindows()

    # --- Pass 2: Interpolate and smooth ---
    ball_positions = interpolate_ball_positions(ball_positions, MAX_INTERP_GAP)

    # Recompute activity with interpolated positions
    for i in range(frame_idx):
        ball_active[i] = is_ball_active(i, ball_positions, [])

    if args.verbose:
        prev = False
        print("\n--- Raw ball_active transitions ---")
        for i in range(frame_idx):
            curr = ball_active[i]
            if curr != prev:
                print(f"Frame {i}: {'ACTIVE' if curr else 'INACTIVE'}")
            prev = curr

    # Smooth: fill short gaps and debounce edges
    effective_grace = max(GRACE_PERIOD, INACTIVE_DEBOUNCE)
    ball_active_smoothed = smooth_ball_active(
        ball_active,
        frame_count=frame_idx,
        grace_period=effective_grace,
        active_debounce=ACTIVE_DEBOUNCE,
        inactive_debounce=INACTIVE_DEBOUNCE,
    )

    if args.verbose:
        prev = False
        print("\n--- Smoothed ball_active transitions ---")
        for i in range(frame_idx):
            curr = ball_active_smoothed[i]
            if curr != prev:
                print(f"Frame {i}: {'ACTIVE' if curr else 'INACTIVE'}")
            prev = curr

    # --- Pass 3: Extract and export rallies ---
    rally_segments = extract_rallies(ball_active_smoothed, frame_idx)
    print(f"\nFound {len(rally_segments)} rally segments")

    export_rallies_only_video(
        video_path=args.video,
        output_path=args.output,
        rally_segments=rally_segments,
        width=width,
        height=height,
        fps=fps,
    )


if __name__ == "__main__":
    main()
