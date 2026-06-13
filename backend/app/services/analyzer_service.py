from fastapi import UploadFile
import io
import os
from PIL import Image, ExifTags
import cv2
import numpy as np
import librosa

SUPPORTED_IMAGE = {"image/png", "image/jpeg", "image/webp"}
SUPPORTED_AUDIO = {"audio/wav", "audio/mpeg", "audio/mp3", "audio/x-wav"}
SUPPORTED_VIDEO = {"video/mp4"}
MAX_BYTES = int(os.getenv("MAX_UPLOAD_MB", "50")) * 1024 * 1024


async def analyze_file(file: UploadFile) -> dict:
    content_type = file.content_type or ""
    data = await file.read()
    if len(data) > MAX_BYTES:
        raise ValueError("File too large")
    if content_type in SUPPORTED_IMAGE:
        return analyze_image(data, file.filename or "image.bin")
    if content_type in SUPPORTED_AUDIO:
        return analyze_audio(data, file.filename or "audio.bin")
    if content_type in SUPPORTED_VIDEO:
        return analyze_video(data, file.filename or "video.mp4")
    raise ValueError("Unsupported media type")


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


def analyze_audio(data: bytes, filename: str) -> dict:
    try:
        y, sr = librosa.load(io.BytesIO(data), sr=None, mono=True)
        rms = float(np.sqrt(np.mean(y ** 2)))
        zcr = float(np.mean(librosa.feature.zero_crossing_rate(y)[0]))
        spectral = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
        rolloff_mean = float(np.mean(spectral))
        hints = []
        if zcr < 0.15:
            hints.append("Unusually smooth zero-crossing rate - may indicate synthetic audio")
        if rms < 1e-4:
            hints.append("Very low RMS - possible unnatural silence")
        score = _audio_score(zcr, rolloff_mean)
        return {
            "type": "audio",
            "filename": filename,
            "sample_rate": sr,
            "duration_seconds": round(float(len(y) / sr), 2),
            "rms": round(rms, 6),
            "zero_crossing_rate": round(zcr, 4),
            "spectral_rolloff": round(rolloff_mean, 2),
            "confidence": score,
            "verdict": "Likely authentic" if score > 55 else "Needs review",
            "hints": hints or ["No strong manipulation signals found"],
        }
    except Exception as e:
        raise ValueError(f"Audio analysis failed: {str(e)}")


def analyze_video(data: bytes, filename: str) -> dict:
    try:
        tmp_path = "/tmp/uploaded_video.mp4"
        with open(tmp_path, "wb") as f:
            f.write(data)
        cap = cv2.VideoCapture(tmp_path)
        if not cap.isOpened():
            raise ValueError("Unreadable video file")
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 0)
        sampled = []
        for idx in range(0, max(frame_count, 1), max(1, frame_count // 8)):
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ok, frame = cap.read()
            if not ok:
                break
            sampled.append(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
        cap.release()
        variances = []
        for frame in sampled:
            if frame.size:
                variances.append(float(np.var(cv2.Laplacian(frame, cv2.CV_64F))))
        ela_mean = float(np.mean(variances)) if variances else 0.0
        hints = []
        if frame_count == 0:
            hints.append("Could not read frames")
        elif fps < 10 or fps > 120:
            hints.append(f"Unusual FPS: {fps}")
        confidence = _confidence_from_score(ela_mean, baseline=0.5)
        return {
            "type": "video",
            "filename": filename,
            "frame_count": frame_count,
            "fps": round(fps, 2),
            "sampled_frame_ela_variance": round(ela_mean, 2),
            "confidence": confidence,
            "verdict": "Likely authentic" if confidence > 55 else "Needs review",
            "hints": hints or ["No strong manipulation signals found"],
        }
    except Exception as e:
        raise ValueError(f"Video analysis failed: {str(e)}")


def _confidence_from_score(score: float, baseline: float = 1.0) -> float:
    scaled = 100 / (1 + (max(score, 0.0) / baseline))
    return round(float(np.clip(scaled, 0, 100)), 1)


def _audio_score(zcr: float, rolloff: float) -> float:
    rolloff_component = min(rolloff / 3500, 1.0)
    zcr_component = min(zcr / 0.25, 1.0)
    score = 100 * (0.55 * rolloff_component + 0.45 * zcr_component)
    return round(float(np.clip(score, 0, 100)), 1)
