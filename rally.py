def extract_rallies(ball_active_smoothed, total_frames):
    rally_segments = []
    consecutive_active = 0
    consecutive_inactive = 0
    current_start = None
    last_rally_end = -RALLY_COOLDOWN

    for i in range(total_frames):
        if i < last_rally_end + RALLY_COOLDOWN:
            continue

        if ball_active_smoothed.get(i, False):
            consecutive_active += 1
            consecutive_inactive = 0
            if consecutive_active == ACTIVE_DEBOUNCE:
                current_start = i - ACTIVE_DEBOUNCE + 1
                print(f"[rally] START @ {current_start} (i={i})")
        else:
            consecutive_inactive += 1
            if current_start is not None and consecutive_inactive >= INACTIVE_DEBOUNCE:
                end_i = i - INACTIVE_DEBOUNCE
                duration = end_i - current_start + 1
                print(
                    f"[rally] END? i={i}, end_i={end_i}, inactive_streak={consecutive_inactive}, duration={duration}"
                )
                if duration >= MIN_RALLY_LENGTH:
                    start = max(0, current_start - BUFFER_BEFORE)
                    end = min(total_frames - 1, end_i + BUFFER_AFTER)
                    rally_segments.append((start, end))
                    print(f"[rally] SAVED: ({start} → {end})")
                    last_rally_end = i
                current_start = None
                consecutive_active = 0
            else:
                consecutive_active = 0

        # optional periodic debug
        if i % 60 == 0:
            print(
                f"[dbg] i={i} act_streak={consecutive_active} inact_streak={consecutive_inactive}"
            )

    if current_start is not None:
        end_i = total_frames - 1
        duration = end_i - current_start + 1
        print(f"[rally] TAIL close: end_i={end_i}, duration={duration}")
        if duration >= MIN_RALLY_LENGTH:
            start = max(0, current_start - BUFFER_BEFORE)
            end = min(total_frames - 1, end_i + BUFFER_AFTER)
            rally_segments.append((start, end))
            print(f"[rally] SAVED tail: ({start} → {end})")

    return rally_segments
