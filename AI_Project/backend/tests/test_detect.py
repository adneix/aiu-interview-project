import io
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from fastapi.testclient import TestClient
from PIL import Image

from backend.main import create_app, get_model


class DetectTests(unittest.TestCase):
    def setUp(self):
        self.model = Mock()
        self.model.names = {0: "keyboard", 1: "mouse"}
        self.model.return_value = []
        app = create_app()
        app.dependency_overrides[get_model] = lambda: self.model
        self.client = self.enterContext(TestClient(app, raise_server_exceptions=False))
        buffer = io.BytesIO()
        with Image.new("RGB", (8, 8), "white") as image:
            image.save(buffer, format="PNG")
        self.image = buffer.getvalue()

    def upload(self, data=None):
        return self.client.post("/detect", files={
            "file": ("desktop.png", self.image if data is None else data, "image/png")
        })

    def test_unique_objects_preserve_order(self):
        self.model.return_value = [
            SimpleNamespace(boxes=[SimpleNamespace(cls=[i]) for i in ids])
            for ids in ([1, 0], [1])
        ]
        response = self.upload()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "status": "success", "objects": ["mouse", "keyboard"], "count": 2
        })
        self.model.assert_called_once()
        self.assertEqual(self.model.call_args.args[0].size, (8, 8))

    def test_no_detections(self):
        self.assertEqual(self.upload().json(), {
            "status": "success", "objects": [], "count": 0
        })

    def test_invalid_image(self):
        self.assertEqual(self.upload(b"invalid").status_code, 400)
        self.model.assert_not_called()

    def test_empty_file(self):
        self.assertEqual(self.upload(b"").status_code, 400)
        self.model.assert_not_called()

    def test_missing_file(self):
        self.assertEqual(self.client.post("/detect").status_code, 422)
        self.model.assert_not_called()

    def test_inference_failure(self):
        self.model.side_effect = RuntimeError("simulated inference failure")
        self.assertEqual(self.upload().status_code, 500)
