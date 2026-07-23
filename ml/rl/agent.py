from pathlib import Path

import numpy as np

CHECKPOINT = Path('ml/models/checkpoints/ppo_agent.zip')


def train_agent(prices: np.ndarray, timesteps: int = 20_000):
    # Imported lazily: stable-baselines3 pulls in torch, which must not be a boot dependency.
    from stable_baselines3 import PPO

    from ml.rl.env import TradingEnv

    env = TradingEnv(prices)
    model = PPO('MlpPolicy', env, verbose=0)
    model.learn(total_timesteps=timesteps)
    CHECKPOINT.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(CHECKPOINT.with_suffix('')))
    return model


def get_rl_action(prices: np.ndarray) -> str:
    if not CHECKPOINT.exists() or len(prices) < 2:
        return 'hold'
    from stable_baselines3 import PPO

    from ml.rl.env import TradingEnv

    model = PPO.load(str(CHECKPOINT))
    env = TradingEnv(prices[-120:])
    obs, _ = env.reset()
    action, _ = model.predict(obs, deterministic=True)
    return {0: 'buy', 1: 'hold', 2: 'sell'}.get(int(action), 'hold')
