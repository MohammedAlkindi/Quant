import random

import numpy as np

DEFAULT_SEED = 1337


def set_seed(seed: int = DEFAULT_SEED) -> np.random.Generator:
    """Seed every RNG this project can touch and return a fresh seeded Generator.

    Seeds stdlib ``random``, NumPy's legacy global state, and torch when it is
    installed (it is optional and absent from the core environment).
    """
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch

        torch.manual_seed(seed)
    except ImportError:
        pass
    return np.random.default_rng(seed)
