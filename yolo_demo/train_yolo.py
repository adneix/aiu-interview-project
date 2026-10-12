from ultralytics import YOLO
model = YOLO("yolov8n.pt")
# 使用官方 coco128 小数据集训练 10 轮
results = model.train(data="coco128.yaml", epochs=10, imgsz=640)