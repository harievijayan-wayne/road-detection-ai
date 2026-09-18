"""
Lighting Robustness and Preprocessing Module for Road Damage Detection.
Evaluates image quality (blur, contrast, brightness) and applies adaptive enhancement
(CLAHE, gamma correction, adaptive color normalization) to improve detector robustness.
"""

import cv2
import numpy as np
from typing import Tuple, Dict, Any

class LightingRobustnessEngine:
    def __init__(self,
                 blur_threshold: float = 100.0,
                 low_light_threshold: float = 60.0,
                 high_light_threshold: float = 200.0,
                 low_contrast_threshold: float = 40.0):
        self.blur_threshold = blur_threshold
        self.low_light_threshold = low_light_threshold
        self.high_light_threshold = high_light_threshold
        self.low_contrast_threshold = low_contrast_threshold

    def assess_quality(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Assess image quality metrics:
        - sharpness (Laplacian variance)
        - brightness (mean of V channel in HSV)
        - contrast (std dev of grayscale)
        """
        if image is None or image.size == 0:
            return {
                "sharpness": 0.0,
                "is_blurry": True,
                "brightness": 0.0,
                "exposure_state": "corrupted",
                "contrast": 0.0,
                "is_low_contrast": True,
                "quality_score": 0.0
            }

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        # Sharpness / Blur estimation
        laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        is_blurry = laplacian_var < self.blur_threshold

        # Brightness & Exposure estimation
        if len(image.shape) == 3:
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            mean_brightness = float(np.mean(hsv[:, :, 2]))
        else:
            mean_brightness = float(np.mean(gray))

        if mean_brightness < self.low_light_threshold:
            exposure_state = "low_light"
        elif mean_brightness > self.high_light_threshold:
            exposure_state = "overexposed"
        else:
            exposure_state = "normal"

        # Contrast
        contrast = float(np.std(gray))
        is_low_contrast = contrast < self.low_contrast_threshold

        # Composite Quality Score (0 to 100)
        sharp_score = min(1.0, laplacian_var / 300.0)
        bright_score = 1.0 - (abs(mean_brightness - 128.0) / 128.0)
        contrast_score = min(1.0, contrast / 70.0)
        overall_quality = round((0.4 * sharp_score + 0.3 * bright_score + 0.3 * contrast_score) * 100, 1)

        return {
            "sharpness": round(laplacian_var, 2),
            "is_blurry": is_blurry,
            "brightness": round(mean_brightness, 2),
            "exposure_state": exposure_state,
            "contrast": round(contrast, 2),
            "is_low_contrast": is_low_contrast,
            "quality_score": overall_quality
        }

    def apply_clahe(self, image: np.ndarray, clip_limit: float = 2.5, tile_grid_size: Tuple[int, int] = (8, 8)) -> np.ndarray:
        """Apply Contrast Limited Adaptive Histogram Equalization in LAB color space."""
        if len(image.shape) == 3:
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
            cl = clahe.apply(l)
            merged = cv2.merge((cl, a, b))
            return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
        else:
            clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
            return clahe.apply(image)

    def apply_gamma_correction(self, image: np.ndarray, gamma: float = 1.0) -> np.ndarray:
        """Apply non-linear gamma curve to brighten dark areas or darken overexposed areas."""
        if gamma == 1.0 or gamma <= 0:
            return image
        inv_gamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
        return cv2.LUT(image, table)

    def adaptive_normalize(self, image: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Intelligently enhance the image ONLY if lighting/contrast deficiencies are diagnosed.
        Returns:
            enhanced_image, report_dict
        """
        metrics = self.assess_quality(image)
        enhanced = image.copy()
        applied_ops = []

        # 1. Low light handling: gamma correction + moderate CLAHE
        if metrics["exposure_state"] == "low_light":
            gamma_val = max(1.2, min(2.0, 128.0 / max(10.0, metrics["brightness"])))
            enhanced = self.apply_gamma_correction(enhanced, gamma=gamma_val)
            enhanced = self.apply_clahe(enhanced, clip_limit=2.0)
            applied_ops.append(f"gamma_boost_{round(gamma_val, 2)}")
            applied_ops.append("clahe_lab")

        # 2. Overexposed handling: darken with gamma < 1.0
        elif metrics["exposure_state"] == "overexposed":
            gamma_val = max(0.6, min(0.85, 128.0 / metrics["brightness"]))
            enhanced = self.apply_gamma_correction(enhanced, gamma=gamma_val)
            applied_ops.append(f"gamma_attenuation_{round(gamma_val, 2)}")

        # 3. Low contrast in normal exposure (e.g. foggy, overcast, dusty road)
        elif metrics["is_low_contrast"]:
            enhanced = self.apply_clahe(enhanced, clip_limit=3.0)
            applied_ops.append("contrast_clahe")

        # 4. Shadow equalization for sunny road images with harsh tree/pole shadows
        else:
            if metrics["contrast"] > 75.0:
                enhanced = self.apply_clahe(enhanced, clip_limit=1.5)
                applied_ops.append("shadow_softening_clahe")

        return enhanced, {
            "initial_metrics": metrics,
            "applied_operations": applied_ops,
            "enhancement_applied": len(applied_ops) > 0
        }
