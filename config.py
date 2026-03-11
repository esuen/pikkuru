# config.py

# ---------- FPS / helpers ----------
FPS_DEFAULT = 120  # fallback if video FPS can't be read


def frames(sec: float, fps: float) -> int:
    return int(round(sec * fps))


# ---------- User-tunable knobs (seconds or per-frame) ----------
# Velocity threshold — using px/frame for now (stable across FPS).
# If you prefer px/second, add VEL_THRESH_PX_PER_SEC and compute below instead.
VEL_THRESH_PX_PER_FRAME = 3.0

SEC_MAX_INTERP_GAP = 0.30
SEC_ACTIVE_DEBOUNCE = 0.35
SEC_INACTIVE_DEBOUNCE = 0.25
SEC_MIN_RALLY_LEN = 1.00
SEC_BUFFER_BEFORE = 0.75
SEC_BUFFER_AFTER = 0.75
SEC_RALLY_COOLDOWN = 0.25

# Detection stride
DETECT_EVERY_N_FRAMES = 2  # run ball detect every N frames (interpolate gaps)

# Pose (currently disabled while rally-debugging)
POSE_SKIP_FRAMES = 999_999
POSE_WINDOW_AFTER_ACTIVITY = 0
USE_POSE_HEURISTICS = False

# Rendering / output
ENABLE_RENDER = False
WRITE_OUTPUT = False
SHOW_WINDOW = False

# Drawing / trails
BALL_TRAIL_LENGTH = 60  # frames
CIRCLE_RADIUS = 7
color_detected = (0, 255, 0)  # Green
color_interpolated = (0, 0, 255)  # Red
color_mixed = (0, 255, 255)  # Yellow
prev_ball_pos = None
prev_ball_detected = None

# Debug switches
SKIP_FRAMEWISE_ACTIVE = False


# ---------- Derived (computed from FPS) ----------
# These are populated by set_fps(...) and *also* seeded at import time (see bottom).
FPS = FPS_DEFAULT
VELOCITY_THRESHOLD = VEL_THRESH_PX_PER_FRAME  # px/frame

MAX_INTERP_GAP = frames(SEC_MAX_INTERP_GAP, FPS)
ACTIVE_DEBOUNCE = frames(SEC_ACTIVE_DEBOUNCE, FPS)
INACTIVE_DEBOUNCE = frames(SEC_INACTIVE_DEBOUNCE, FPS)
MIN_RALLY_LENGTH = frames(SEC_MIN_RALLY_LEN, FPS)
BUFFER_BEFORE = frames(SEC_BUFFER_BEFORE, FPS)
BUFFER_AFTER = frames(SEC_BUFFER_AFTER, FPS)
RALLY_COOLDOWN = frames(SEC_RALLY_COOLDOWN, FPS)
# Grace defaults to at least the inactive debounce
GRACE_PERIOD = max(INACTIVE_DEBOUNCE, INACTIVE_DEBOUNCE)


def set_fps(fps: float):
    """
    Compute frame-based knobs from seconds-based ones.
    Call this ASAP in main.py after reading the video's true FPS.
    Safe to call multiple times.
    """
    global FPS, VELOCITY_THRESHOLD, MAX_INTERP_GAP, ACTIVE_DEBOUNCE, INACTIVE_DEBOUNCE
    global MIN_RALLY_LENGTH, BUFFER_BEFORE, BUFFER_AFTER, RALLY_COOLDOWN, GRACE_PERIOD

    FPS = fps or FPS_DEFAULT

    # Choose ONE velocity convention. Using px/frame (stable across FPS):
    VELOCITY_THRESHOLD = float(VEL_THRESH_PX_PER_FRAME)
    # If you ever switch to px/second, do:
    # VELOCITY_THRESHOLD = float(VEL_THRESH_PX_PER_SEC) / FPS

    MAX_INTERP_GAP = frames(SEC_MAX_INTERP_GAP, FPS)
    ACTIVE_DEBOUNCE = frames(SEC_ACTIVE_DEBOUNCE, FPS)
    INACTIVE_DEBOUNCE = frames(SEC_INACTIVE_DEBOUNCE, FPS)
    MIN_RALLY_LENGTH = frames(SEC_MIN_RALLY_LEN, FPS)
    BUFFER_BEFORE = frames(SEC_BUFFER_BEFORE, FPS)
    BUFFER_AFTER = frames(SEC_BUFFER_AFTER, FPS)
    RALLY_COOLDOWN = frames(SEC_RALLY_COOLDOWN, FPS)

    # Grace: ensures tiny OFF gaps inside a rally don't end it immediately
    GRACE_PERIOD = max(INACTIVE_DEBOUNCE, INACTIVE_DEBOUNCE)


# ---------- Seed defaults so imports never crash ----------
# This ensures modules that import ACTIVE_DEBOUNCE, etc. have values
# even before main.py calls set_fps(real_fps).
set_fps(FPS_DEFAULT)
