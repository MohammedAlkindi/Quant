import numpy as np
from sklearn.ensemble import IsolationForest


def detect_anomaly(series: list[float]) -> dict:
    if len(series) < 20:
        return {'is_anomaly': False, 'z_score': 0.0, 'model_flag': 1}
    arr = np.array(series, dtype=float)
    z = float((arr[-1] - arr.mean()) / (arr.std() + 1e-6))
    model = IsolationForest(contamination=0.05, random_state=42)
    flags = model.fit_predict(arr.reshape(-1, 1))
    model_flag = int(flags[-1])
    return {'is_anomaly': abs(z) > 2.5 or model_flag == -1, 'z_score': z, 'model_flag': model_flag}
