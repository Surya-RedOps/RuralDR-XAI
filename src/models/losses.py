from typing import Optional
import torch
import torch.nn as nn
import torch.nn.functional as F


class QuadraticWeightedKappaLoss(nn.Module):
    """
    Differentiable approximation of Quadratic Weighted Kappa (QWK).
    Penalizes ordinal misclassifications proportional to (i - j)^2.
    """

    def __init__(self, num_classes: int = 5, epsilon: float = 1e-6):
        super().__init__()
        self.num_classes = num_classes
        self.epsilon = epsilon
        # Quadratic weight matrix W_ij = (i - j)^2 / (K - 1)^2
        w = torch.zeros((num_classes, num_classes), dtype=torch.float32)
        for i in range(num_classes):
            for j in range(num_classes):
                w[i, j] = ((i - j) ** 2) / ((num_classes - 1) ** 2)
        self.register_buffer("weight_matrix", w)

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        """
        logits: (N, num_classes)
        targets: (N,) with class indices in [0, num_classes - 1]
        """
        probs = F.softmax(logits, dim=1)
        targets_onehot = F.one_hot(targets, num_classes=self.num_classes).float()

        # Observed matrix O = P^T * Y
        observed = torch.matmul(probs.t(), targets_onehot)
        observed = observed / (torch.sum(observed) + self.epsilon)

        # Expected matrix E = (sum_rows(P) * sum_cols(Y)^T)
        hist_pred = torch.sum(probs, dim=0, keepdim=True)
        hist_target = torch.sum(targets_onehot, dim=0, keepdim=True)
        expected = torch.matmul(hist_pred.t(), hist_target)
        expected = expected / (torch.sum(expected) + self.epsilon)

        # QWK numerator and denominator
        num = torch.sum(self.weight_matrix * observed)
        den = torch.sum(self.weight_matrix * expected)

        loss = num / (den + self.epsilon)
        return loss


class FocalLoss(nn.Module):
    """
    Multi-Class Focal Loss for handling severe DR class imbalance.
    """

    def __init__(self, alpha: Optional[torch.Tensor] = None, gamma: float = 2.0):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        ce_loss = F.cross_entropy(logits, targets, reduction="none", weight=self.alpha)
        pt = torch.exp(-ce_loss)
        focal_loss = ((1.0 - pt) ** self.gamma) * ce_loss
        return torch.mean(focal_loss)
