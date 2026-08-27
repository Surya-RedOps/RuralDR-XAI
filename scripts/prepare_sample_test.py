import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import cv2
import numpy as np


def create_sample_fundus_fixture(output_path: Path):
    """Creates a sample test fundus image fixture for CLI testing."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img = np.zeros((512, 512, 3), dtype=np.uint8)
    y, x = np.ogrid[:512, :512]
    retina_mask = np.sqrt((x - 256)**2 + (y - 256)**2) <= 225

    # Radial orange/red gradient
    dist = np.sqrt((x - 256)**2 + (y - 256)**2)
    gradient = np.clip(180 - dist * 0.35, 40, 200).astype(np.uint8)
    img[retina_mask, 0] = gradient[retina_mask]
    img[retina_mask, 1] = (gradient[retina_mask] * 0.55).astype(np.uint8)
    img[retina_mask, 2] = (gradient[retina_mask] * 0.25).astype(np.uint8)

    # Optic Disc (Bright cluster at (160, 256))
    cv2.circle(img, (160, 256), 35, (240, 230, 160), -1)

    # Vessels branching
    cv2.line(img, (160, 256), (320, 180), (40, 25, 15), 3)
    cv2.line(img, (160, 256), (330, 320), (40, 25, 15), 3)

    # Microaneurysms
    cv2.circle(img, (290, 220), 2, (50, 15, 10), -1)
    cv2.circle(img, (310, 240), 2, (50, 15, 10), -1)

    # Hard Exudates
    cv2.circle(img, (340, 270), 8, (230, 220, 110), -1)

    bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    cv2.imwrite(str(output_path), bgr)
    print(f"Sample test fundus fixture created at {output_path}")


if __name__ == "__main__":
    sample_file = PROJECT_ROOT / "data/sample/sample_fundus.jpg"
    create_sample_fundus_fixture(sample_file)
