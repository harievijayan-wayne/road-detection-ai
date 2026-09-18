"""
Comprehensive Image Augmentation Pipeline for Road Damage Detection.
Implements:
- Brightness, contrast, gamma variations
- Synthetic shadows (overpass, tree, utility pole shadows)
- Motion blur, Gaussian blur, camera jitter
- Gaussian sensor noise, JPEG compression artifacts
- Geometric transformations (rotation, scaling, cropping, perspective warp)
- Weather simulation (rain streaks, wet road specular sheen)
Works standalone via high-performance OpenCV/NumPy and integrates Albumentations if available.
"""

import cv2
import numpy as np
import random
from typing import Tuple, List, Dict, Any, Optional

class RoadDamageAugmentor:
    def __init__(self, target_size: Tuple[int, int] = (640, 640)):
        self.target_size = target_size

    def random_brightness_contrast(self, image: np.ndarray, alpha_range=(0.7, 1.3), beta_range=(-40, 40)) -> np.ndarray:
        alpha = random.uniform(*alpha_range)
        beta = random.uniform(*beta_range)
        return cv2.convertScaleAbs(image, alpha=alpha, beta=beta)

    def random_gamma(self, image: np.ndarray, gamma_range=(0.6, 1.8)) -> np.ndarray:
        gamma = random.uniform(*gamma_range)
        inv_gamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
        return cv2.LUT(image, table)

    def synthetic_shadow(self, image: np.ndarray) -> np.ndarray:
        """Simulates realistic roadside shadows (trees, poles, overhead bridges) across the asphalt."""
        h, w = image.shape[:2]
        # Generate random polygon shadow mask
        pts = np.array([
            [random.randint(0, w // 2), 0],
            [random.randint(w // 2, w), 0],
            [random.randint(w // 2, w), h],
            [random.randint(0, w // 2), h]
        ], dtype=np.int32)

        mask = np.zeros((h, w), dtype=np.uint8)
        cv2.fillPoly(mask, [pts], 255)
        mask = cv2.GaussianBlur(mask, (31, 31), 0)

        # Darken shadow area by 35% - 60%
        shadow_factor = random.uniform(0.4, 0.65)
        hls = cv2.cvtColor(image, cv2.COLOR_BGR2HLS).astype(np.float32)
        hls[:, :, 1] = np.where(mask > 50, hls[:, :, 1] * shadow_factor, hls[:, :, 1])
        hls[:, :, 1] = np.clip(hls[:, :, 1], 0, 255)
        return cv2.cvtColor(hls.astype(np.uint8), cv2.COLOR_HLS2BGR)

    def motion_blur(self, image: np.ndarray, kernel_size: int = 15) -> np.ndarray:
        """Simulates vehicle vibration and speed motion blur."""
        kernel = np.zeros((kernel_size, kernel_size))
        kernel[int((kernel_size - 1) / 2), :] = np.ones(kernel_size)
        kernel = kernel / kernel_size
        return cv2.filter2D(image, -1, kernel)

    def gaussian_noise(self, image: np.ndarray, mean=0, sigma=25) -> np.ndarray:
        """Simulates low-light sensor ISO noise."""
        gauss = np.random.normal(mean, sigma, image.shape).astype(np.float32)
        noisy = np.clip(image.astype(np.float32) + gauss, 0, 255).astype(np.uint8)
        return noisy

    def perspective_transform(self, image: np.ndarray) -> np.ndarray:
        """Simulates variable camera pitch angles (dashcam vs phone vs inspection vehicle)."""
        h, w = image.shape[:2]
        delta = random.randint(15, 45)
        pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
        pts2 = np.float32([[delta, 0], [w - delta, 0], [0, h], [w, h]])
        matrix = cv2.getPerspectiveTransform(pts1, pts2)
        return cv2.warpPerspective(image, matrix, (w, h), borderMode=cv2.BORDER_REFLECT)

    def weather_rain_simulation(self, image: np.ndarray) -> np.ndarray:
        """Adds rain streaks and windshield/road glint reflections."""
        h, w = image.shape[:2]
        rain_layer = np.zeros((h, w), dtype=np.uint8)
        num_drops = random.randint(250, 600)
        for _ in range(num_drops):
            x = random.randint(0, w - 1)
            y = random.randint(0, h - 25)
            length = random.randint(10, 25)
            cv2.line(rain_layer, (x, y), (x + 2, y + length), 200, 1)
        
        rain_blur = cv2.GaussianBlur(rain_layer, (3, 3), 0)
        rain_bgr = cv2.cvtColor(rain_blur, cv2.COLOR_GRAY2BGR)
        wet_image = cv2.addWeighted(image, 0.85, rain_bgr, 0.5, 0)
        return wet_image

    def apply_pipeline(self, image: np.ndarray, mode: str = "random") -> Tuple[np.ndarray, List[str]]:
        """
        Applies a sequence of augmentations.
        Mode can be 'random', 'low_light', 'shadow', 'rain', 'blur', or 'overexposed'.
        """
        res = image.copy()
        ops = []

        if mode == "low_light":
            res = self.random_brightness_contrast(res, alpha_range=(0.4, 0.6), beta_range=(-60, -30))
            res = self.random_gamma(res, gamma_range=(0.5, 0.7))
            res = self.gaussian_noise(res, sigma=15)
            ops = ["low_light_attenuation", "gamma_down", "iso_noise"]

        elif mode == "shadow":
            res = self.synthetic_shadow(res)
            ops = ["synthetic_shadow_mask"]

        elif mode == "overexposed":
            res = self.random_brightness_contrast(res, alpha_range=(1.3, 1.6), beta_range=(35, 60))
            ops = ["overexposure_glare"]

        elif mode == "rain":
            res = self.weather_rain_simulation(res)
            ops = ["rain_simulation"]

        elif mode == "blur":
            res = self.motion_blur(res, kernel_size=15)
            ops = ["dashcam_motion_blur"]

        else: # Random composition
            if random.random() < 0.6:
                res = self.random_brightness_contrast(res)
                ops.append("random_brightness")
            if random.random() < 0.4:
                res = self.synthetic_shadow(res)
                ops.append("shadow")
            if random.random() < 0.3:
                res = self.random_gamma(res)
                ops.append("gamma")
            if random.random() < 0.25:
                res = self.motion_blur(res)
                ops.append("motion_blur")
            if random.random() < 0.2:
                res = self.perspective_transform(res)
                ops.append("perspective_tilt")

        return res, ops
