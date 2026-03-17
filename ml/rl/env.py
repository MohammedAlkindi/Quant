import gymnasium as gym
import numpy as np
from gymnasium import spaces


class TradingEnv(gym.Env):
    metadata = {'render_modes': ['human']}

    def __init__(self, prices: np.ndarray):
        super().__init__()
        self.prices = prices.astype(np.float32)
        self.action_space = spaces.Discrete(3)
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(3,), dtype=np.float32)
        self.reset()

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.idx = 1
        self.position = 0
        self.returns = []
        return self._obs(), {}

    def _obs(self):
        price = self.prices[self.idx]
        prev = self.prices[self.idx - 1]
        momentum = (price - prev) / max(prev, 1e-6)
        return np.array([price, momentum, self.position], dtype=np.float32)

    def step(self, action: int):
        prev = self.prices[self.idx - 1]
        price = self.prices[self.idx]
        if action == 0:
            self.position = 1
        elif action == 2:
            self.position = -1
        ret = ((price - prev) / max(prev, 1e-6)) * self.position
        self.returns.append(ret)
        sharpe = np.mean(self.returns) / (np.std(self.returns) + 1e-6)
        reward = float(sharpe)
        self.idx += 1
        done = self.idx >= len(self.prices)
        obs = self._obs() if not done else np.zeros(3, dtype=np.float32)
        return obs, reward, done, False, {'sharpe': sharpe}
