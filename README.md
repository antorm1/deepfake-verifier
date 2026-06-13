# Deepfake Verifier

Free open-source deepfake and media manipulation detector for images, audio, and video.

## Features

- Image analysis: EXIF/metadata forensics + ELA
- Audio analysis: spectral anomaly detection
- Video analysis: frame consistency + lip-sync signal checks
- Confidence scoring with plain-language findings
- Shareable verification reports
- Browser bookmarklet for on-page checks
- Docker-first deployment

## Stack

- Backend: FastAPI
- Analysis: OpenCV, Pillow, librosa
- Frontend: vanilla JS + Tailwind
- Deployment: Docker / Fly.io
