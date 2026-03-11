import cv2
import numpy as np


def draw_ball_trail(frame, trail, color_detected, color_interpolated, color_mixed):
    for i in range(1, len(trail)):
        (x1, y1), d1 = trail[i - 1]
        (x2, y2), d2 = trail[i]
        color = (
            color_detected
            if d1 and d2
            else color_interpolated
            if not d1 and not d2
            else color_mixed
        )
        cv2.line(frame, (x1, y1), (x2, y2), color, 2)


def overlay_frame_state(frame, frame_idx, ball_active):
    text = f"Frame {frame_idx} - {'ACTIVE' if ball_active.get(frame_idx, False) else 'INACTIVE'}"
    cv2.putText(
        frame,
        text,
        (50, frame.shape[0] - 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255, 255, 255),
        2,
    )
