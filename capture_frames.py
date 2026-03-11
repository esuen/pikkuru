import cv2
import time
import sys

# Open video
video_name = "eric_johnny_game_1"
video_fmt = ".mov"
video_path = f"videos/{video_name}{video_fmt}"
cap = cv2.VideoCapture(video_path)

total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
i = 0

start_time = time.time()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Example: Save every 30th frame
    if i % 30 == 0:
        cv2.imwrite(f"frames/{video_name}/{i}.jpg", frame)

    i += 1

    # Print progress every 30 frames
    if i % 30 == 0 or i == total_frames:
        elapsed = time.time() - start_time
        avg_time_per_frame = elapsed / i
        frames_left = total_frames - i
        eta_seconds = int(avg_time_per_frame * frames_left)

        # Convert ETA to H:M:S
        eta_h = eta_seconds // 3600
        eta_m = (eta_seconds % 3600) // 60
        eta_s = eta_seconds % 60
        eta_str = f"{eta_h:02}:{eta_m:02}:{eta_s:02}"

        sys.stdout.write(f"\r[{i}/{total_frames}] frames processed — ETA: {eta_str}")
        sys.stdout.flush()

cap.release()
print("\n✅ Frame capture complete!")
