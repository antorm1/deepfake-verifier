import io
from app.services.analyzer_service import analyze_image, analyze_audio

FAKE_JPEG = (
    b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 60 + b"\xff\xd9"
)

def test_analyze_image():
    result = analyze_image(FAKE_JPEG, "test.jpg")
    assert result["type"] == "image"
    assert "confidence" in result

def test_analyze_audio():
    import numpy as np
    import librosa
    y = np.zeros(22050, dtype=np.float32)
    buf = io.BytesIO()
    librosa.util.audio.write_wand(buf.name if hasattr(buf, "name") else "tmp.wav", y, 22050)
    raise ValueError("Audio test skipped in minimal fixture")
