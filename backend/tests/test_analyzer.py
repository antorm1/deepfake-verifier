from app.services.analyzer_service import analyze_image

def test_analyze_image():
    data = (
        b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 60 + b"\xff\xd9"
    )
    result = analyze_image(data, "sample.jpg")
    assert result["type"] == "image"
    assert 0 <= result["confidence"] <= 100
