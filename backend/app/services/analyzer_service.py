from fastapi import UploadFile
from PIL import Image, ExifTags
import numpy as np
import cv2
import io

SUPPORTED_IMAGE = {"image/png", "image/jpeg", "image/webp"}
MAX_BYTES = 25 * 1024 * 1024


async def analyze_file(file: UploadFile) -> dict:
    content_type = file.content_type or ""
    data = await file.read()
    if len(data) > MAX_BYTES:
        raise ValueError("File too large")
    if content_type in SUPPORTED_IMAGE:
        return analyze_image(data, file.filename or "image.bin")
    raise ValueError("Unsupported media type for this build")


def analyze_image(data: bytes, filename: str) -> dict:
    try:
        pil = Image.open(io.BytesIO(data)).convert("RGB")
        width, height = pil.size
        exif = {}
        try:
            raw = pil._getexif() or {}
            exif = {ExifTags.TAGS.get(k, str(k)): str(v) for k, v in raw.items()}
        except Exception:
            pass
        obj = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
        if obj is None:
            raise ValueError("Unreadable image file")
        gray = cv2.cvtColor(obj, cv2.COLOR_BGR2GRAY)
        ela = cv2.Laplacian(gray, cv2.CV_64F)
        ela_score = float(np.var(ela))
        hints = []
        if ela_score < 120:
            hints.append("Low ELA variance - unusually smooth for natural images")
        if not exif:
            hints.append("No EXIF data found")
        confidence = _confidence_from_score(ela_score)
        return {
            "type": "image",
            "filename": filename,
            "dimensions": {"width": width, "height": height},
            "ela_variance": round(ela_score, 2),
            "exif_keys": sorted(list(exif.keys()))[:20],
            "confidence": confidence,
            "verdict": "Likely authentic" if confidence > 55 else "Needs review",
            "hints": hints or ["No strong manipulation signals found"],
        }
    except Exception as e:
        raise ValueError(f"Image analysis failed: {str(e)}")


def _confidence_from_score(score: float, baseline: float = 1.0) -> float:
    scaled = 100 / (1 + (max(score, 0.0) / baseline))
    return round(float(np.clip(scaled, 0, 100)), 1)
