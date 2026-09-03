"""
Retinal Lesion Segmentation Model: U-Net with ResNet-34 Encoder
Multi-label binary segmentation for Microaneurysms, Haemorrhages, Hard Exudates, Soft Exudates.

Architecture rationale:
- U-Net skip connections preserve spatial detail critical for tiny lesions (MAs: 2-30 pixels)
- ResNet-34 encoder provides pretrained ImageNet features while staying lightweight
- Multi-label (4 binary channels) because IDRiD provides separate binary masks and lesions
  can spatially overlap (e.g., MA within hemorrhage region)
"""

from typing import List, Optional
import torch
import torch.nn as nn
import torch.nn.functional as F
import timm


class DecoderBlock(nn.Module):
    """Single decoder block with transposed conv upsampling + skip connection."""

    def __init__(self, in_channels: int, skip_channels: int, out_channels: int):
        super().__init__()
        self.upsample = nn.ConvTranspose2d(in_channels, out_channels, kernel_size=2, stride=2)
        self.conv = nn.Sequential(
            nn.Conv2d(out_channels + skip_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor, skip: Optional[torch.Tensor] = None) -> torch.Tensor:
        x = self.upsample(x)
        if skip is not None:
            # Handle potential size mismatch from odd dimensions
            if x.shape[2:] != skip.shape[2:]:
                x = F.interpolate(x, size=skip.shape[2:], mode="bilinear", align_corners=False)
            x = torch.cat([x, skip], dim=1)
        x = self.conv(x)
        return x


class LesionUNet(nn.Module):
    """
    U-Net with ResNet-34 encoder for multi-label retinal lesion segmentation.

    Input: (B, 3, H, W) RGB image, H and W should be multiples of 32
    Output: (B, num_classes, H, W) per-pixel logits
    """

    LESION_CLASSES = ["microaneurysms", "haemorrhages", "hard_exudates", "soft_exudates"]

    def __init__(
        self,
        encoder_name: str = "resnet34",
        num_classes: int = 4,
        pretrained: bool = True,
    ):
        super().__init__()
        self.num_classes = num_classes
        self.encoder_name = encoder_name

        # Create encoder with feature extraction at multiple stages
        self.encoder = timm.create_model(
            encoder_name,
            pretrained=pretrained,
            features_only=True,
            out_indices=(0, 1, 2, 3, 4),
        )

        # Get channel counts from the encoder
        encoder_channels = self.encoder.feature_info.channels()
        # ResNet-34: [64, 64, 128, 256, 512]

        # Decoder path
        self.decoder4 = DecoderBlock(encoder_channels[4], encoder_channels[3], 256)
        self.decoder3 = DecoderBlock(256, encoder_channels[2], 128)
        self.decoder2 = DecoderBlock(128, encoder_channels[1], 64)
        self.decoder1 = DecoderBlock(64, encoder_channels[0], 32)

        # Final upsampling to match input resolution (encoder has stride-2 stem)
        self.final_upsample = nn.ConvTranspose2d(32, 32, kernel_size=2, stride=2)
        self.final_conv = nn.Sequential(
            nn.Conv2d(32, 32, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, num_classes, kernel_size=1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Encoder forward pass
        features = self.encoder(x)  # List of feature maps at different resolutions

        # Decoder path with skip connections
        d4 = self.decoder4(features[4], features[3])
        d3 = self.decoder3(d4, features[2])
        d2 = self.decoder2(d3, features[1])
        d1 = self.decoder1(d2, features[0])

        # Final upsampling + classification
        out = self.final_upsample(d1)

        # Ensure output matches input spatial dimensions
        if out.shape[2:] != x.shape[2:]:
            out = F.interpolate(out, size=x.shape[2:], mode="bilinear", align_corners=False)

        out = self.final_conv(out)
        return out

    def predict_masks(
        self,
        x: torch.Tensor,
        threshold: float = 0.5,
    ) -> torch.Tensor:
        """
        Runs inference and returns thresholded binary masks.

        Returns:
            masks: (B, num_classes, H, W) uint8 binary tensor {0, 1}
        """
        self.eval()
        with torch.no_grad():
            logits = self.forward(x)
            probs = torch.sigmoid(logits)
            masks = (probs >= threshold).to(torch.uint8)
        return masks

    def predict_probabilities(self, x: torch.Tensor) -> torch.Tensor:
        """
        Runs inference and returns per-pixel probabilities.

        Returns:
            probs: (B, num_classes, H, W) float tensor in [0, 1]
        """
        self.eval()
        with torch.no_grad():
            logits = self.forward(x)
            probs = torch.sigmoid(logits)
        return probs
