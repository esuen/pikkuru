# Helper to compute ball velocity
def is_ball_active(frame_idx, ball_positions, pose_keypoints_list):
    # Velocity-based check
    if frame_idx < 2:
        return False
    if frame_idx not in ball_positions or frame_idx - 1 not in ball_positions:
        return False
    x1, y1 = ball_positions[frame_idx - 1]
    x2, y2 = ball_positions[frame_idx]
    velocity = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
    if velocity > VELOCITY_THRESHOLD:
        return True

    # Pose-based fallback (if available)
    if pose_keypoints_list:
        stances = [is_athletic_stance(pose) for pose in pose_keypoints_list]
        return any(stances)  # If at least one player is in an athletic stance

    return False


def smooth_ball_active(
    ball_active: dict[int, bool],
    frame_count: int,
    *,
    grace_period: int,  # extend True across short False gaps (≤ this)
    active_debounce: int,  # require this many consecutive True to flip to True
    inactive_debounce: int,  # require this many consecutive False to flip to False
) -> dict[int, bool]:
    # 1) Fill short OFF gaps inside active runs (grace)
    filled = ball_active.copy()
    i = 0
    while i < frame_count:
        if filled.get(i, False):
            i += 1
            continue
        # find length of consecutive False starting at i
        j = i
        while j < frame_count and not filled.get(j, False):
            j += 1
        gap_len = j - i
        # if bounded by True on both sides and short enough, flip to True
        if (
            i > 0
            and j < frame_count
            and filled.get(i - 1, False)
            and filled.get(j, False)
            and gap_len <= grace_period
        ):
            for k in range(i, j):
                filled[k] = True
        i = j

    # 2) Debounce edges (Schmitt trigger style)
    out = {}
    run_true = 0
    run_false = 0
    state = False  # current smoothed state

    for f in range(frame_count):
        if filled.get(f, False):
            run_true += 1
            run_false = 0
        else:
            run_false += 1
            run_true = 0

        if not state and run_true >= active_debounce:
            state = True
        elif state and run_false >= inactive_debounce:
            state = False

        out[f] = state

    return out


def is_athletic_stance(keypoints):
    try:
        left_hip = keypoints[11]
        right_hip = keypoints[12]
        left_knee = keypoints[13]
        right_knee = keypoints[14]

        if np.any(np.isnan([left_hip, right_hip, left_knee, right_knee])):
            return False

        # Y-distance from hips to knees: should be small if knees are bent
        left_drop = abs(left_knee[1] - left_hip[1])
        right_drop = abs(right_knee[1] - right_hip[1])

        # Tune this threshold based on your frame resolution
        return left_drop < 100 and right_drop < 100
    except:
        return False
