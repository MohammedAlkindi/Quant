import numpy as np

from ml.rl.agent import train_agent


if __name__ == '__main__':
    prices = np.cumprod(1 + np.random.normal(0.0005, 0.02, 1000)) * 100
    train_agent(prices)
    print('saved_to ml/models/checkpoints/ppo_agent.zip')
