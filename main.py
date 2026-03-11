import cv2
import numpy as np
from collections import deque
from concurrent.futures import ThreadPoolExecutor

from tqdm import tqdm
from config import *
from models import load_models
from detection import detect_ball, detect_person_pose
from interpolation import interpolate_ball_positions
from activity import is_ball_active, smooth_ball_active, is_athletic_stance
from rally import extract_rallies
from render import draw_ball_trail, overlay_frame_state
from export import export_rallies_only_video
from utils import scale_box


def main():
    ball_trail = deque(maxlen=BALL_TRAIL_LENGTH)

    # Ball activity tracking
    ball_positions = {}
    ball_active = {}
    ball_detected = {}
    # debugging rallies
    # last_ball_active_frame = -1000

    # debugging rallies
    # ball_model, person_model, pose_model = load_models()
    ball_model, _, _ = load_models()

    # Thread pool for model inference
    # debugging rallies
    # executor = ThreadPoolExecutor(max_workers=3)

    # Video setup
    cap = cv2.VideoCapture("videos/eric_cindy_game_2_clip.mov")
    fps = cap.get(cv2.CAP_PROP_FPS) or 120
    set_fps(fps)

    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0  # total frames for tqdm
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    # debugging rallies
    # out = cv2.VideoWriter("output.mp4", fourcc, fps, (width, height))
    # target_width, target_height = 640, 360  # downsize for inference
    target_width, target_height = 480, 270  # downsize for inference

    # Processing frames
    frame_idx = 0
    ball_names = ball_model.names
    # debugging rallies
    # person_names = person_model.names

    with tqdm(
        total=frame_count if frame_count > 0 else None,
        desc="Processing frames",
        unit="frame",
    ) as pbar:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            resized_frame = cv2.resize(frame, (target_width, target_height))

            # cv2.polylines(resized_frame, [np.array(court_corners)], isClosed=True, color=(0, 255, 255), thickness=2)

            # --- stride decision ---
            RUN_DETECT = frame_idx % DETECT_EVERY_N_FRAMES == 0
            scale_x = frame.shape[1] / target_width
            scale_y = frame.shape[0] / target_height

            # Ball detection
            detected = False
            if RUN_DETECT:
                ball_results = detect_ball(ball_model, resized_frame)
                for box in ball_results.boxes:
                    cls = ball_names[int(box.cls)]
                    if cls == "ball" and box.conf[0] > 0.3:
                        xyxy = scale_box(box.xyxy[0].tolist(), scale_x, scale_y)
                        x_center = (xyxy[0] + xyxy[2]) / 2
                        y_center = (xyxy[1] + xyxy[3]) / 2
                        ball_positions[frame_idx] = (x_center, y_center)
                        ball_detected[frame_idx] = True
                        detected = True
                        break
            else:
                # no detection this frame (we'll interpolate later)
                ball_detected[frame_idx] = False
            # --- end stride ---

            # set activity ONCE (velocity only)
            ball_active[frame_idx] = (
                is_ball_active(frame_idx, ball_positions, []) if detected else False
            )
            # debugging rallies
            """
            if ball_active[frame_idx]:
                last_ball_active_frame = frame_idx

            # Update ball trail
            if frame_idx in ball_positions:
                x, y = ball_positions[frame_idx]
                is_detected = ball_detected.get(frame_idx, False)
                ball_trail.append(((int(x), int(y)), is_detected))

                draw_ball_trail(
                    frame, ball_trail, color_detected, color_interpolated, color_mixed
                )

                # Draw current ball
                color = color_detected if is_detected else color_interpolated
                cv2.circle(frame, (int(x), int(y)), CIRCLE_RADIUS, color, -1)

                cv2.putText(
                    frame,
                    "I" if not is_detected else "D",
                    (int(x), int(y) - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    color,
                    1,
                )
            else:
                ball_trail.clear()

            if frame_idx in ball_positions:
                x, y = ball_positions[frame_idx]
                color = (0, 255, 0) if ball_detected.get(frame_idx, False) else (0, 0, 255)
                cv2.circle(frame, (int(x), int(y)), CIRCLE_RADIUS, color, -1)

            # Run person/pose models if ball active recently
            run_pose_person = ball_active.get(frame_idx, False) or (
                frame_idx - last_ball_active_frame <= POSE_WINDOW_AFTER_ACTIVITY
            )

            if run_pose_person and frame_idx % POSE_SKIP_FRAMES == 0:
                person_future = executor.submit(
                    lambda: detect_person_pose(person_model, pose_model, frame)
                )
                person_results, pose_results = person_future.result()
            else:
                person_results = None
                pose_results = None

            # Extract pose keypoints
            pose_keypoints_list = []
            if pose_results is not None:
                for kp in pose_results.keypoints.xy:
                    pose_keypoints_list.append(kp.cpu().numpy())  # shape: (17, 2)
            else:
                pose_keypoints_list = []


            # Draw person boxes
            if person_results is not None:
                for box in person_results.boxes:
                    cls = person_names[int(box.cls)]
                    if cls == "person" and box.conf[0] > 0.3:
                        xyxy = scale_box(box.xyxy[0].tolist(), scale_x, scale_y)
                        conf = box.conf[0].item()
                        cv2.rectangle(
                            frame,
                            (int(xyxy[0]), int(xyxy[1])),
                            (int(xyxy[2]), int(xyxy[3])),
                            (0, 0, 255),
                            2,
                        )
                        cv2.putText(
                            frame,
                            f"{cls} {conf:.2f}",
                            (int(xyxy[0]), int(xyxy[1]) - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5,
                            (255, 255, 255),
                            1,
                        )

            # Overlay poses
            frame_with_poses = (
                pose_results.plot() if pose_results is not None else frame.copy()
            )

            frame_has_activity = ball_active[frame_idx] or (
                person_results is not None
                and sum(
                    1
                    for b in person_results.boxes
                    if person_names[int(b.cls)] == "person" and b.conf[0] > 0.3
                )
                > 1
            )

            overlay_frame_state(frame_with_poses, frame_idx, ball_active)

            if frame_has_activity:
                if WRITE_OUTPUT:
                    out.write(frame_with_poses)
                if SHOW_WINDOW:
                    cv2.imshow("Detection", frame_with_poses)
            """

            frame_idx += 1

            # ✅ progress bar updates (cheap every frame; or batch every n frames)
            pbar.update(1)
            # optional live info (keeps bar informative but lightweight)
            if frame_idx % 30 == 0:
                pbar.set_postfix(
                    det=detected, active=ball_active.get(frame_idx - 1, False)
                )

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    ball_positions = interpolate_ball_positions(ball_positions, MAX_INTERP_GAP)

    for i in range(frame_idx):
        ball_active[i] = is_ball_active(i, ball_positions, [])

    # Debug: Print ball_active transitions
    prev_active = False
    print("\n--- Raw ball_active transitions ---")
    for i in range(frame_idx):
        curr_active = ball_active[i]
        if curr_active != prev_active:
            print(
                f"Frame {i}: ball_active changed to {'ACTIVE' if curr_active else 'INACTIVE'}"
            )
        prev_active = curr_active

        if i in ball_positions:
            detected = ball_detected.get(i, False)
            source = "DETECTED" if detected else "INTERPOLATED"
            print(f"Frame {i}: {source} at {ball_positions[i]}")

    # Smooth ball_active: extend True over short gaps
    # ✅ Pass smoothing params explicitly (see function below)
    effective_grace = max(GRACE_PERIOD, INACTIVE_DEBOUNCE)
    ball_active_smoothed = smooth_ball_active(
        ball_active,
        frame_count=frame_idx,
        grace_period=effective_grace,
        active_debounce=ACTIVE_DEBOUNCE,
        inactive_debounce=INACTIVE_DEBOUNCE,
    )

    # Debug: Print smoothed ball_active transitions
    prev_smoothed = False
    print("\n--- Smoothed ball_active transitions ---")
    for i in range(frame_idx):
        curr_smoothed = ball_active_smoothed[i]
        if curr_smoothed != prev_smoothed:
            print(
                f"Frame {i}: ball_active_smoothed changed to {'ACTIVE' if curr_smoothed else 'INACTIVE'}"
            )
        prev_smoothed = curr_smoothed

    print("\nBall Active Timeline:")
    for i in range(frame_idx):
        if ball_active_smoothed.get(i, False):
            print(f"{i}: ACTIVE")
        else:
            print(f"{i}: INACTIVE")

    cap.release()
    cv2.destroyAllWindows()

    # debugging rallies
    """
    out.release()

    executor.shutdown()
    """

    rally_segments = extract_rallies(ball_active_smoothed, frame_idx)

    export_rallies_only_video(
        video_path="videos/eric_cindy_game_2_clip.mov",
        output_path="rallies_only.mp4",
        rally_segments=rally_segments,
        width=width,
        height=height,
        fps=fps,
    )


if __name__ == "__main__":
    main()
