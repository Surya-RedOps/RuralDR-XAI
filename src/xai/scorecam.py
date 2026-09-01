"""
Score-CAM: Score-Weighted Visual Explanations
Gradient-free CAM that removes gradient noise and saturation artifacts.
"""

from typing import Tuple, Optional
import cv2
import numpy as np
import torch
import torch.nn.functional as F

from ..models.classifier import DRClassifier


class ScoreCAM:
    """
    Score-CAM: Perturbation-based visual attribution.
    """

    def __init__(self, model: DRClassifier, max_channels: int = 32):
        self.model = model
        self.max_channels = max_channels

    def generate(
        self,
        input_tensor: torch.Tensor,
        target_class: Optional[int] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        self.model.eval()
        with torch.no_grad():
            logits = self.model(input_tensor)
            if target_class is None:
                target_class = int(torch.argmax(logits, dim=1).item())

            activations = self.model.activations
            if activations is None:
                h, w = input_tensor.shape[2:]
                return np.zeros((h, w), dtype=np.float32), np.zeros((h, w), dtype=np.uint8)

            b, c, h_f, w_f = activations.shape
            h, w = input_tensor.shape[2:]

            # Select top channels by activation variance to bound computation
            channel_vars = torch.var(activations, dim=(2, 3)).squeeze()
            top_channels = torch.topk(channel_vars, min(self.max_channels, c)).indices

            scores = []
            normalized_masks = []

            for ch in top_channels:
                act_map = activations[:, ch : ch + 1, :, :]
                act_min, act_max = torch.min(act_map), torch.max(act_map)
                if act_max > act_min:
                    norm_map = (act_map - act_min) / (act_max - act_min)
                else:
                    norm_map = act_map

                upsampled = F.interpolate(norm_map, size=(h, w), mode="bilinear", align_corners=False)
                masked_input = input_tensor * upsampled
                out = self.model(masked_input)
                score = out[0, target_class].item()

                scores.append(score)
                normalized_masks.append(upsampled.squeeze().cpu().numpy())

            weights = F.softmax(torch.tensor(scores, dtype=torch.float32), dim=0).numpy()
            cam = np.zeros((h, w), dtype=np.float32)
            for w_i, m_i in zip(weights, normalized_masks):
                cam += w_i * m_i

            cam_min, cam_max = np.min(cam), np.max(cam)
            if cam_max > cam_min:
                cam = (cam - cam_min) / (cam_max - cam_min)

            binary_mask = (cam >= 0.35).astype(np.uint8) * 255
            return cam.astype(np.float32), binary_mask
