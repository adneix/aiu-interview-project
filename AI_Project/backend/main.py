from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
from PIL import Image
import io

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = YOLO("yolo_model.pt")

@app.post("/detect")
async def detect_objects(file: UploadFile = File(...)):
    # 1. 读取前端上传的图片
    image_data = await file.read()
    image = Image.open(io.BytesIO(image_data))

    # 2. 进行推理
    results = model(image)

    # 3. 提取识别结果（只提取类别名称，去重）
    detected_objects = []
    for result in results:
        for box in result.boxes:
            class_id = int(box.cls[0])
            class_name = model.names[class_id]
            if class_name not in detected_objects:
                detected_objects.append(class_name)

    # 4. 返回JSON格式的清单给前端
    return {
        "status": "success",
        "objects": detected_objects,
        "count": len(detected_objects)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)