import torch

# This is the unsafe way that YOLO uses under the hood
# torch.load("yolov8n-face-lindevs.pt")  # Not recommended

# Instead, inspect the content manually using:
with open("yolov8n-face-lindevs.pt", "rb") as f:
    head = f.read(4)
    print(head)
