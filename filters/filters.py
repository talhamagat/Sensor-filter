import numpy as np
from collections import deque
from scipy.signal import savgol_filter

class MovingAverage:
    def __init__(self, size=10):
        self.buffer = deque(maxlen=size)

    def update(self, val):
        self.buffer.append(val)
        return sum(self.buffer) / len(self.buffer)

class LowPass:
    def __init__(self, alpha=0.1):
        self.prev = None
        self.alpha = alpha

    def update(self, val):
        if self.prev is None:
            self.prev = val
        self.prev = self.alpha * val + (1 - self.alpha) * self.prev
        return self.prev

class MedianFilter:
    def __init__(self, size=5):
        self.buffer = deque(maxlen=size)

    def update(self, val):
        self.buffer.append(val)
        return np.median(list(self.buffer))

class EMA:
    def __init__(self, alpha=0.2):
        self.ema = None
        self.alpha = alpha

    def update(self, val):
        if self.ema is None:
            self.ema = val
        self.ema = self.alpha * val + (1 - self.alpha) * self.ema
        return self.ema

class Kalman:
    def __init__(self, err_measure=1.0, err_estimate=1.0, estimate=0.0, process_noise=0.01):
        self.err_measure = err_measure
        self.err_estimate = err_estimate
        self.estimate = estimate
        self.process_noise = process_noise

    def update(self, measurement):
        gain = self.err_estimate / (self.err_estimate + self.err_measure)
        self.estimate = self.estimate + gain * (measurement - self.estimate)
        self.err_estimate = (1 - gain) * self.err_estimate + self.process_noise
        return self.estimate

class SavitzkyGolay:
    def __init__(self, window_size=11, poly_order=2):
        self.window_size = window_size
        self.poly_order = poly_order
        self.buffer = deque(maxlen=window_size)

    def update(self, val):
        self.buffer.append(val)
        if len(self.buffer) < self.window_size:
            return val
        return savgol_filter(list(self.buffer), self.window_size, self.poly_order)[-1]

class AdaptiveHybridFilter:
    def __init__(self, window_size=10, alpha_min=0.1, alpha_max=0.5, n_sigma=3):
        self.window_size = window_size
        self.alpha_min = alpha_min
        self.alpha_max = alpha_max
        self.n_sigma = n_sigma
        self.buffer = deque(maxlen=window_size)
        self.ema_prev = None

    def update(self, x):
        self.buffer.append(x)
        if len(self.buffer) < self.window_size:
            self.ema_prev = x if self.ema_prev is None else self.ema_prev
            return x

        med = np.median(self.buffer)
        std = np.std(self.buffer)

        if std > 0 and abs(x - med) > self.n_sigma * std:
            if self.ema_prev is None:
                self.ema_prev = med
            return self.ema_prev

        std_norm = min(std, 1.0)
        alpha = self.alpha_max - (self.alpha_max - self.alpha_min) * std_norm

        if self.ema_prev is None:
            self.ema_prev = x
        else:
            self.ema_prev = alpha * x + (1 - alpha) * self.ema_prev

        return self.ema_prev

