"""
Explainable AI Engine: Grad-CAM and Grad-CAM++
Generates class activation attribution maps for deep DR classifiers.

MEDICAL SAFETY NOTE:
Grad-CAM shows model attention regions that contributed to the predicted class.
It does NOT identify specific lesions or provide clinical diagnostic proof.
"""

from typing import Tuple, Optional, Dict, List
import cv2
import numpy as np
import torch
import torch.nn.functional as F

from ..models.classifier import DRClassifier
from ..core.contracts import GradCAMResult, DR_GRADE_NAMES, DRGrade


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

    def generate_with_validation(
        self,
        input_tensor: torch.Tensor,
        target_class: Optional[int] = None,
    ) -> Tuple[np.ndarray, np.ndarray, GradCAMResult]:
        """
        Generates Grad-CAM with quality validation checks.

        Returns:
            cam_heatmap: (H, W) float32 in [0, 1]
            cam_binary_mask: (H, W) uint8
            result: GradCAMResult with quality flags and metadata
        """
        cam_np, binary_mask = self.generate(input_tensor, target_class)

        # Determine actual target class
        self.model.eval()
        with torch.no_grad():
            logits = self.model(input_tensor)
            predicted_class = int(torch.argmax(logits, dim=1).item())
        actual_target = target_class if target_class is not None else predicted_class

        # Quality validation
        quality_flags = []
        peak_intensity = float(np.max(cam_np))
        activation_coverage = float(np.mean(cam_np > 0.1))

        if peak_intensity < 0.01:
            quality_flags.append("blank_heatmap")
        if peak_intensity > 0.99 and activation_coverage > 0.8:
            quality_flags.append("saturated_heatmap")
        if activation_coverage < 0.02:
            quality_flags.append("low_coverage")

        is_valid = len(quality_flags) == 0

        # Map class index to name
        try:
            class_name = DR_GRADE_NAMES[DRGrade(actual_target)]
        except (ValueError, KeyError):
            class_name = f"Class {actual_target}"

        result = GradCAMResult(
            target_class=actual_target,
            target_class_name=class_name,
            is_valid=is_valid,
            activation_coverage=round(activation_coverage, 4),
            peak_intensity=round(peak_intensity, 4),
            quality_flags=quality_flags,
        )

        return cam_np, binary_mask, result

    def generate_multi_class(
        self,
        input_tensor: torch.Tensor,
        class_indices: Optional[List[int]] = None,
    ) -> Dict[int, Tuple[np.ndarray, np.ndarray, GradCAMResult]]:
        """
        Generates Grad-CAM heatmaps for multiple classes.

        Args:
            input_tensor: (1, 3, H, W) normalized tensor
            class_indices: List of class indices to generate for.
                          If None, generates for all 5 DR classes.

        Returns:
            Dict mapping class_index -> (heatmap, binary_mask, GradCAMResult)
        """
        if class_indices is None:
            class_indices = list(range(5))

        results = {}
        for cls_idx in class_indices:
            cam_np, binary_mask, result = self.generate_with_validation(
                input_tensor, target_class=cls_idx
            )
            results[cls_idx] = (cam_np, binary_mask, result)

        return results
