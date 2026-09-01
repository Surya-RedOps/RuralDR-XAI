"""
Diabetic Retinopathy Severity Classification Model
Supports EfficientNet, ConvNeXt, and ResNet backbones with Grad-CAM feature map hooks.
"""

from typing import Tuple, Optional, Dict, Any
from pathlib import Path
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import timm

from ..core.contracts import DRGrade, DR_GRADE_NAMES, SeverityPrediction
from .calibrate import TemperatureScaler


class DRClassifier(nn.Module):
    """
    Deep Neural Network for 5-Class International Clinical Diabetic Retinopathy (ICDR) Grading.
    """

    def __init__(
        self,
        backbone_name: str = "efficientnet_b4",
        num_classes: int = 5,
        pretrained: bool = True,
        dropout_rate: float = 0.3,
    ):
        super().__init__()
        self.backbone_name = backbone_name
        self.num_classes = num_classes

        # Load backbone from timm
        self.backbone = timm.create_model(
            backbone_name,
            pretrained=pretrained,
            num_classes=0,  # Remove original classifier head to get pooling output
            drop_rate=dropout_rate,
        )

        num_features = self.backbone.num_features
        self.classifier_head = nn.Sequential(
            nn.Linear(num_features, 256),
            nn.BatchNorm1d(256),
            nn.SiLU(),
            nn.Dropout(p=dropout_rate),
            nn.Linear(256, num_classes),
        )

        # Gradient and activation storage for Grad-CAM hooks
        self.gradients = None
        self.activations = None
        self._register_hooks()

    def _register_hooks(self):
        """
        Registers forward and backward hooks on the final convolutional layer for Grad-CAM.
        """
        target_layer = None
        if hasattr(self.backbone, "conv_head"):
            target_layer = self.backbone.conv_head
        elif hasattr(self.backbone, "act2"):
            target_layer = self.backbone.act2
        elif hasattr(self.backbone, "layer4"):
            target_layer = self.backbone.layer4
        elif hasattr(self.backbone, "stages"):
            target_layer = self.backbone.stages[-1]

        if target_layer is not None:
            def forward_hook(module, input, output):
                self.activations = output

            def backward_hook(module, grad_in, grad_out):
                self.gradients = grad_out[0]

            target_layer.register_forward_hook(forward_hook)
            target_layer.register_full_backward_hook(backward_hook)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        features = self.backbone(x)
        logits = self.classifier_head(features)
        return logits

    def predict(
        self,
        x: torch.Tensor,
        temperature_scaler: Optional[TemperatureScaler] = None,
    ) -> SeverityPrediction:
        """
        Executes forward inference and produces calibrated prediction contracts.
        """
        self.eval()
        with torch.no_grad():
            logits = self.forward(x)
            raw_probs = F.softmax(logits, dim=1).cpu().numpy()[0]

            if temperature_scaler is not None:
                calibrated_logits = temperature_scaler.scale(logits)
                calibrated_probs = F.softmax(calibrated_logits, dim=1).cpu().numpy()[0]
                temp_factor = float(temperature_scaler.temperature.item())
            else:
                calibrated_probs = raw_probs
                temp_factor = 1.0

            predicted_class_idx = int(np.argmax(calibrated_probs))
            predicted_grade = DRGrade(predicted_class_idx)
            is_referable = predicted_class_idx >= 2  # Grade 2+ is Referable DR

            return SeverityPrediction(
                predicted_grade=predicted_grade,
                grade_name=DR_GRADE_NAMES[predicted_grade],
                is_referable=is_referable,
                raw_probabilities=[float(p) for p in raw_probs],
                calibrated_probabilities=[float(p) for p in calibrated_probs],
                calibrated_confidence=float(calibrated_probs[predicted_class_idx]),
                temperature_scaling_factor=temp_factor,
            )

    def load_checkpoint(self, checkpoint_path: Path, device: torch.device = torch.device("cpu")):
        """
        Safely loads model weights from a state dictionary file.
        """
        checkpoint_path = Path(checkpoint_path)
        if not checkpoint_path.is_file():
            raise FileNotFoundError(f"Model checkpoint not found at {checkpoint_path}")

        checkpoint = torch.load(checkpoint_path, map_location=device)
        if "model_state_dict" in checkpoint:
            self.load_state_dict(checkpoint["model_state_dict"])
        else:
            self.load_state_dict(checkpoint)
