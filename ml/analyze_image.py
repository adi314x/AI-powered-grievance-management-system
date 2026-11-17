"""Smoke-test the exported vision models on a local image.

Usage (from the project root):
    .\\.venv\\Scripts\\python.exe ml\\analyze_image.py path\\to\\photo.jpg
"""

import argparse
import base64
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.services.image_ai_service import image_ai_service


def main():
    parser = argparse.ArgumentParser(
        description="Run the grievance issue classifier and AI-image detector on an image."
    )
    parser.add_argument("image", type=Path, help="Path to a JPG/PNG/WebP image")
    args = parser.parse_args()

    if not args.image.is_file():
        raise SystemExit(f"Image not found: {args.image}")

    payload = base64.b64encode(args.image.read_bytes()).decode("ascii")
    result = image_ai_service.analyze_images([f"data:image/jpeg;base64,{payload}"])
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
