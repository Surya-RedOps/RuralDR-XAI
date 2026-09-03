"""
Confidence Calibration and Uncertainty Estimation
Implements Temperature Scaling (Guo et al., ICML 2017) and Expected Calibration Error (ECE).
"""

from typing import Tuple, Dict, List, Any
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F


class TemperatureScaler(nn.Module):
    """
    Learns a post-hoc temperature parameter T > 0 on validation set logits.
    Calibrated Softmax: p_i = exp(z_i / T) / sum_j exp(z_j / T)
    """

    def __init__(self, initial_temperature: float = 1.25):
        super().__init__()
        self.temperature = nn.Parameter(torch.ones(1) * initial_temperature)

    def scale(self, logits: torch.Tensor) -> torch.Tensor:
        """
        Scales logits by 1 / T.
        """
        temp = self.temperature.unsqueeze(1).expand(logits.size(0), logits.size(1))
        return logits / temp

    def forward(self, logits: torch.Tensor) -> torch.Tensor:
        return self.scale(logits)

    def fit(self, val_logits: torch.Tensor, val_labels: torch.Tensor, max_iter: int = 50) -> float:
        """
        Fits temperature parameter on validation logits using L-BFGS to minimize NLL.
        """
        nll_criterion = nn.CrossEntropyLoss()
        optimizer = optim.LBFGS([self.temperature], lr=0.01, max_iter=max_iter)

        def eval_loss():
            optimizer.zero_grad()
            scaled_logits = self.scale(val_logits)
            loss = nll_criterion(scaled_logits, val_labels)
            loss.backward()
            return loss

        optimizer.step(eval_loss)
        return float(self.temperature.item())


def compute_ece(
    probabilities: np.ndarray,
    labels: np.ndarray,
    num_bins: int = 10,
) -> Tuple[float, Dict[str, Any]]:
    """
    Computes Expected Calibration Error (ECE) and reliability bin statistics.

    ECE = sum_{m=1}^M (|B_m| / N) * |acc(B_m) - conf(B_m)|
    """
    confidences = np.max(probabilities, axis=1)
    predictions = np.argmax(probabilities, axis=1)
    accuracies = (predictions == labels).astype(float)

    bin_boundaries = np.linspace(0.0, 1.0, num_bins + 1)
    ece = 0.0
    bin_accuracies = []
    bin_confidences = []
    bin_counts = []

    total_samples = len(labels)

    for i in range(num_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]

        in_bin = (confidences > bin_lower) & (confidences <= bin_upper)
        prop_in_bin = np.mean(in_bin)
        bin_size = int(np.sum(in_bin))

        if bin_size > 0:
            accuracy_in_bin = float(np.mean(accuracies[in_bin]))
            confidence_in_bin = float(np.mean(confidences[in_bin]))
            ece += np.abs(accuracy_in_bin - confidence_in_bin) * prop_in_bin
            bin_accuracies.append(accuracy_in_bin)
            bin_confidences.append(confidence_in_bin)
            bin_counts.append(bin_size)
        else:
            bin_accuracies.append(0.0)
            bin_confidences.append(float((bin_lower + bin_upper) / 2.0))
            bin_counts.append(0)

    stats = {
        "ece": float(ece),
        "bin_accuracies": bin_accuracies,
        "bin_confidences": bin_confidences,
        "bin_counts": bin_counts,
        "num_bins": num_bins,
    }

    return float(ece), stats
