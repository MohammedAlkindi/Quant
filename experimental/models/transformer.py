import torch
from torch import nn


class PriceTransformer(nn.Module):
    def __init__(self, input_size: int, d_model: int = 64, nhead: int = 4, num_layers: int = 2):
        super().__init__()
        self.proj = nn.Linear(input_size, d_model)
        encoder_layer = nn.TransformerEncoderLayer(d_model=d_model, nhead=nhead, batch_first=True)
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.head = nn.Linear(d_model, 5)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h = self.proj(x)
        e = self.encoder(h)
        return self.head(e[:, -1, :])
