from pathlib import Path

import numpy as np
from stable_baselines3 import PPO

from ml.rl.env import TradingEnv


def train_agent(prices: np.ndarray, timesteps: int = 20_000) -> PPO:
    env = TradingEnv(prices)
    model = PPO('MlpPolicy', env, verbose=0)
    model.learn(total_timesteps=timesteps)
    ckpt = Path('ml/models/checkpoints')
    ckpt.mkdir(parents=True, exist_ok=True)
    model.save(str(ckpt / 'ppo_agent'))
    return model


def get_rl_action(prices: np.ndarray) -> str:
    ckpt = Path('ml/models/checkpoints/ppo_agent.zip')
    if not ckpt.exists() or len(prices) < 2:
        return 'hold'
    model = PPO.load(str(ckpt))
    env = TradingEnv(prices[-120:])
    obs, _ = env.reset()
    action, _ = model.predict(obs, deterministic=True)
    return {0: 'buy', 1: 'hold', 2: 'sell'}.get(int(action), 'hold')
