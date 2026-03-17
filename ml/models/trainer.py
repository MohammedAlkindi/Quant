from pathlib import Path

import torch
from torch import nn


def train_model(model: nn.Module, train_loader, val_loader, epochs: int = 10, lr: float = 1e-3, save_name: str = 'lstm.pt'):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.MSELoss()

    best_loss = float('inf')
    checkpoint_dir = Path('ml/models/checkpoints')
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    for _ in range(epochs):
        model.train()
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            optimizer.zero_grad()
            loss = criterion(model(xb), yb)
            loss.backward()
            optimizer.step()

        model.eval()
        total = 0.0
        count = 0
        with torch.no_grad():
            for xb, yb in val_loader:
                xb, yb = xb.to(device), yb.to(device)
                total += criterion(model(xb), yb).item()
                count += 1
        val_loss = total / max(1, count)
        if val_loss < best_loss:
            best_loss = val_loss
            torch.save(model.state_dict(), checkpoint_dir / save_name)
    return best_loss
