import torch
from torch.utils.data import DataLoader, TensorDataset

from experimental.models.lstm import PriceLSTM
from experimental.models.trainer import train_model


def make_dataset(points=500, seq=60, feat=8):
    x = torch.randn(points, seq, feat)
    y = torch.randn(points, 5)
    ds = TensorDataset(x, y)
    return DataLoader(ds, batch_size=32, shuffle=True)


if __name__ == '__main__':
    train_loader = make_dataset()
    val_loader = make_dataset(points=120)
    model = PriceLSTM(input_size=8)
    loss = train_model(model, train_loader, val_loader, epochs=5, save_name='lstm.pt')
    print({'best_val_loss': loss, 'saved_to': 'ml/models/checkpoints/lstm.pt'})
