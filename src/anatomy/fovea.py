"""
Fovea / Macula Localization
Locates the Foveal Avascular Zone (FAZ) using anatomical relationship with the Optic Disc
and localized minimum green/red reflectance.
"""

from typing import Tuple, Optional
import cv2
import numpy as np


def locate_fovea(
    image_rgb: np.ndarray,
    optic_disc_center: Optional[Tuple[int, int]],
    optic_disc_radius: Optional[float],
    vessel_mask: Optional[np.ndarray] = None,
    mask: Optional[np.ndarray] = None,
) -> Optional[Tuple[int, int]]:
    """
    Locates the foveal center coordinate (x, y).

    Anatomical constraint:
    The fovea is located approximately 2.0 to 3.0 disc diameters temporal (horizontally displaced)
    from the optic disc center, with minimal vertical displacement and within the lowest vessel density zone.
    """
    h, w = image_rgb.shape[:2]
    green = image_rgb[:, :, 1] if image_rgb.ndim == 3 else image_rgb

    if optic_disc_center is None or optic_disc_radius is None:
        # Fallback to image center if OD is unavailable
        return (int(w / 2), int(h / 2))

    od_x, od_y = optic_disc_center
    od_r = optic_disc_radius

    # Determine whether OD is in the left hemisphere (Right Eye / OD) or right hemisphere (Left Eye / OS)
    # In fundus photography:
    # - If OD is on the left (nasal for OS), fovea is to the right (temporal).
    # - If OD is on the right (nasal for OD), fovea is to the left (temporal).
    if od_x < w / 2:
        # OD is in left half -> Fovea is to the right
        search_x_min = int(min(w - 1, od_x + 1.8 * od_r * 2))
        search_x_max = int(min(w - 1, od_x + 3.2 * od_r * 2))
    else:
        # OD is in right half -> Fovea is to the left
        search_x_min = int(max(0, od_x - 3.2 * od_r * 2))
        search_x_max = int(max(0, od_x - 1.8 * od_r * 2))

    search_y_min = int(max(0, od_y - 1.0 * od_r * 2))
    search_y_max = int(min(h - 1, od_y + 1.0 * od_r * 2))

    if search_x_max <= search_x_min or search_y_max <= search_y_min:
        return (int(w / 2), int(h / 2))

    # Search for darkest region (lowest green reflectance, highest pigmentation) in the search window
    roi = green[search_y_min:search_y_max, search_x_min:search_x_max]
    blurred_roi = cv2.GaussianBlur(roi, (21, 21), 0)

    # Penalize pixels containing vessels
    if vessel_mask is not None:
        vessel_roi = vessel_mask[search_y_min:search_y_max, search_x_min:search_x_max]
        blurred_roi[vessel_roi > 0] = 255

    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(blurred_roi)
    fovea_x = search_x_min + min_loc[0]
    fovea_y = search_y_min + min_loc[1]

    return (int(fovea_x), int(fovea_y))
