from activity import is_ball_active


def interpolate_ball_positions(ball_positions, max_gap=90):
    keys = sorted(ball_positions.keys())
    for i in range(len(keys) - 1):
        start, end = keys[i], keys[i + 1]
        gap = end - start
        if 1 < gap <= max_gap:
            x1, y1 = ball_positions[start]
            x2, y2 = ball_positions[end]
            for f in range(start + 1, end):
                alpha = (f - start) / (end - start)
                x = x1 + alpha * (x2 - x1)
                y = y1 + alpha * (y2 - y1)
                ball_positions[f] = (x, y)
    return ball_positions
