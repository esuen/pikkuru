def scale_box(xyxy, scale_x, scale_y):
    return [
        int(xyxy[0] * scale_x),
        int(xyxy[1] * scale_y),
        int(xyxy[2] * scale_x),
        int(xyxy[3] * scale_y),
    ]
