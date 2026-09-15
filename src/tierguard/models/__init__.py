from __future__ import annotations

from .cifar_cnn import CifarCNN
from .mlp import MLP
from .mnist_cnn import MnistCNN
from .resnet_small import ResNetSmall


def build_model(name: str, num_classes: int = 10, input_dim: int | None = None):
    key = name.lower()
    if key in {"mnist_cnn", "fashionmnist_cnn"}:
        return MnistCNN(num_classes=num_classes)
    if key == "cifar_cnn":
        return CifarCNN(num_classes=num_classes)
    if key in {"resnet_small", "resnet9"}:
        return ResNetSmall(num_classes=num_classes)
    if key == "mlp":
        return MLP(input_dim=input_dim or 100, num_classes=num_classes)
    raise ValueError(f"Unknown model: {name}")
