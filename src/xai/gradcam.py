"""
Explainable AI Engine: Grad-CAM and Grad-CAM++
Generates class activation attribution maps for deep DR classifiers.
"""

from typing import Tuple, Optional
import cv2
import numpy as np
import torch
import torch.nn.functional as F

from ..models.classifier import DRClassifier


class GradCAM:
    """
    Gradient-weighted Class Activation Mapping (Grad-CAM & Grad-CAM++).
    """

    def __init__(self, model: DRClassifier, use_plus_plus: bool = True):
        self.model = model
        self.use_plus_plus = use_plus_plus

    def generate(
        self,
        input_tensor: torch.Tensor,
        target_class: Optional[int] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generates Grad-CAM heatmap for the target class.

        Args:
            input_tensor: (1, 3, H, W) normalized tensor with requires_grad=True
            target_class: Target class index in [0, 4] (if None, uses predicted class)

        Returns:
            cam_heatmap: (H, W) float32 in [0, 1]
            cam_binary_mask: (H, W) uint8 {0, 255} high-activation zone (top 25% intensity)
        """
        self.model.eval()
        self.model.zero_grad()

        input_tensor = input_tensor.clone().detach().requires_grad_(True)
        logits = self.model(input_tensor)

        if target_class is None:
            target_class = int(torch.argmax(logits, dim=1).item())

        score = logits[0, target_class]
        score.backward(retain_graph=True)

        activations = self.model.activations  # (1, C, H_feat, W_feat)
        gradients = self.model.gradients      # (1, C, H_feat, W_feat)

        if activations is None or gradients is None:
            h, w = input_tensor.shape[2:]
            return np.zeros((h, w), dtype=np.float32), np.zeros((h, w), dtype=np.uint8)

        if self.use_plus_plus:
            # Grad-CAM++: Second and third order gradients for multiple lesion instances
            grad_2 = gradients.pow(2)
            grad_3 = gradients.pow(3)
            sum_act = activations.sum(dim=(2, 3), keepdim=True)
            alpha_num = grad_2
            alpha_denom = 2 * grad_2 + sum_act * grad_3 + 1e-8
            alpha = alpha_num / alpha_denom
            weights = (alpha * F.relu(gradients)).sum(dim=(2, 3), keepdim=True)
        else:
            # Standard Grad-CAM: Global average pooling of gradients
            weights = torch.mean(gradients, dim=(2, 3), keepdim=True)

        cam = torch.sum(weights * activations, dim=1, keepdim=True)
        cam = F.relu(cam)  # Only positive influence on class score

        # Normalize to [0, 1]
        cam_min, cam_max = torch.min(cam), torch.max(cam)
        if cam_max > cam_min:
            cam = (cam - cam_min) / (cam_max - cam_min)
        else:
            cam = torch.zeros_like(cam)

        # Upsample to input tensor size
        h, w = input_tensor.shape[2:]
        cam_resized = F.interpolate(cam, size=(h, w), mode="bilinear", align_corners=False)
        cam_np = cam_resized.squeeze().detach().cpu().numpy()

        # High activation threshold (e.g., top 30% intensity for pointing game)
        binary_mask = (cam_np >= 0.35).astype(np.uint8) * 255

        return cam_np, binary_mask
