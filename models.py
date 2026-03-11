from ultralytics import YOLO
import torch


def pick_device():
    if torch.backends.mps.is_available() and torch.backends.mps.is_built():
        return "mps"
    elif torch.cuda.is_available():
        return "cuda"
    else:
        return "cpu"


def load_models():
    DEVICE = pick_device()
    ball_model = YOLO("runs/detect/ball/weights/best.pt")
    ball_model.to(DEVICE)
    ball_model.fuse()
    person_model = YOLO("yolov8n.pt")
    person_model.to(DEVICE)
    person_model.fuse()
    pose_model = YOLO("yolov8n-pose.pt")
    pose_model.to(DEVICE)
    pose_model.fuse()
    return ball_model, person_model, pose_model
