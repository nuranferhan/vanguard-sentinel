#!/usr/bin/env python3
"""
Fetches (or bootstraps) the ML model artifacts used by the AI engine.

Model binaries (*.joblib) are intentionally NOT committed to git — see
.gitignore — because they are large binary blobs that don't diff well
and bloat repo size/clone time.

Two ways to get them:

1. Pretrained models (recommended for a realistic demo):
   Set MODEL_ARTIFACT_URL to a URL serving a zip/tarball of the
   `isolation_forest.joblib` and `autoencoder.joblib` files (e.g. a
   GitHub Release asset you've uploaded), then run this script:

       export MODEL_ARTIFACT_URL="https://github.com/<you>/vanguard-sentinel/releases/download/v1.0/models.zip"
       python scripts/download_models.py

2. Auto-bootstrap (zero config, default):
   If MODEL_ARTIFACT_URL is not set, do nothing here — `AnomalyDetector`
   and `AutoencoderAnomalyDetector` already train and save a baseline
   model from synthetic "normal traffic" on first run (see
   `app/ai/anomaly_detector.py` and `app/ai/autoencoder_model.py`,
   `_load_or_bootstrap_model`). Just start the app normally:

       uvicorn app.main:app --reload --port 8000

   The baseline models are good enough for local development and CI,
   but should be replaced with models retrained on real traffic before
   any production use.
"""

import os
import shutil
import sys
import tempfile
import urllib.request
import zipfile

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "backend", "app", "ai", "models")


def main() -> int:
    url = os.environ.get("MODEL_ARTIFACT_URL")
    if not url:
        print(
            "MODEL_ARTIFACT_URL not set — skipping download.\n"
            "The backend will auto-bootstrap baseline models on first run "
            "(see app/ai/anomaly_detector.py / autoencoder_model.py)."
        )
        return 0

    os.makedirs(MODELS_DIR, exist_ok=True)

    print(f"Downloading model artifacts from: {url}")
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        urllib.request.urlretrieve(url, tmp.name)
        archive_path = tmp.name

    try:
        with zipfile.ZipFile(archive_path) as zf:
            zf.extractall(MODELS_DIR)
        print(f"Model artifacts extracted to: {MODELS_DIR}")
    finally:
        os.remove(archive_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
