import random

import numpy as np

from quant.seeds import set_seed


def test_set_seed_makes_stdlib_and_numpy_reproducible():
    set_seed(123)
    first = (random.random(), np.random.rand(3).tolist())
    set_seed(123)
    second = (random.random(), np.random.rand(3).tolist())
    assert first == second


def test_set_seed_returns_independently_seeded_generator():
    gen_a = set_seed(7)
    gen_b = set_seed(7)
    assert gen_a.standard_normal(4).tolist() == gen_b.standard_normal(4).tolist()


def test_different_seeds_diverge():
    gen_a = set_seed(1)
    gen_b = set_seed(2)
    assert gen_a.standard_normal(4).tolist() != gen_b.standard_normal(4).tolist()
