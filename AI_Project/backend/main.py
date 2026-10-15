"""FastAPI application with an injectable, lazily loaded detector."""
import io
from functools import lru_cache
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, UnidentifiedImageError


@lru_cache(maxsize=1)
def get_model():
    from ultralytics import YOLO
    return YOLO(str(Path(__file__).with_name("yolo_model.pt")))


def create_app():
    application = FastAPI()
    application.add_middleware(
        CORSMiddleware, allow_origins=["*"], allow_credentials=True,
        allow_methods=["*"], allow_headers=["*"],
    )

    @application.post("/detect")
    async def detect_objects(file: UploadFile = File(...), model=Depends(get_model)):
        try:
            image = Image.open(io.BytesIO(await file.read()))
            image.load()
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            raise HTTPException(status_code=400, detail="Invalid image") from exc
        finally:
            await file.close()
        try:
            objects = []
            for result in model(image):
                for box in result.boxes:
                    name = model.names[int(box.cls[0])]
                    if name not in objects:
                        objects.append(name)
            return {"status": "success", "objects": objects, "count": len(objects)}
        finally:
            image.close()

    return application


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
