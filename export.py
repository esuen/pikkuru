import cv2
import numpy as np


def create_title_frame(text, width, height):
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 2
    thickness = 3
    size = cv2.getTextSize(text, font, scale, thickness)[0]
    x = (width - size[0]) // 2
    y = (height + size[1]) // 2
    cv2.putText(frame, text, (x, y), font, scale, (255, 255, 255), thickness)
    return frame


def export_rallies_only_video(
    video_path, output_path, rally_segments, width, height, fps
):
    print(f"Exporting {len(rally_segments)} rally segments...")

    cap = cv2.VideoCapture(video_path)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    for idx, (start, end) in enumerate(rally_segments, 1):
        cap.set(cv2.CAP_PROP_POS_FRAMES, start)
        for _ in range(start, end + 1):
            ret, frame = cap.read()
            if not ret:
                break

            # Overlay rally number
            label = f"Rally {idx}"
            font = cv2.FONT_HERSHEY_SIMPLEX
            scale = 1
            thickness = 2
            color = (255, 255, 255)  # white text
            shadow_color = (0, 0, 0)  # black shadow for contrast
            pos = (50, 50)

            # Shadow text for visibility
            cv2.putText(
                frame, label, pos, font, scale, shadow_color, thickness + 2, cv2.LINE_AA
            )
            cv2.putText(frame, label, pos, font, scale, color, thickness, cv2.LINE_AA)

            out.write(frame)

    cap.release()
    out.release()
    print(f"✅ Done: {output_path} with rally titles created.")
