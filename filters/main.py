import serial
import time
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Button, CheckButtons
from filters import MovingAverage, LowPass, MedianFilter, EMA, Kalman, SavitzkyGolay

import numpy as np
from collections import deque

class AdaptiveHybridFilter:
    def __init__(self, window_size=10, alpha=0.3):
        self.window_size = window_size
        self.alpha = alpha
        self.buffer = deque(maxlen=window_size)
        self.ema = None

    def update(self, val):
        self.buffer.append(val)
        median = np.median(self.buffer)

        if self.ema is None:
            self.ema = val
        else:
            self.ema = self.alpha * val + (1 - self.alpha) * self.ema

        filtered = (median + self.ema) / 2
        return filtered

PORT = "/dev/ttyUSB0"
BAUD = 9600
MAX_POINTS = 100

ser = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(2)

ma = MovingAverage(size=10)
lp = LowPass(alpha=0.05)
med = MedianFilter(size=7)
ema = EMA(alpha=0.05)
kf = Kalman(err_measure=2.0, err_estimate=1.0, process_noise=0.05)
sg = SavitzkyGolay(window_size=11, poly_order=2)
ahf = AdaptiveHybridFilter(window_size=10, alpha=0.3)

raw_data, ma_data, lp_data, med_data, ema_data, kf_data, sg_data, ahf_data = [], [], [], [], [], [], [], []

fig, (ax, ax_text) = plt.subplots(2, 1, figsize=(12, 9), gridspec_kw={'height_ratios': [3, 1]})
plt.subplots_adjust(left=0.2, bottom=0.25)

lines = {
    "Ham Veri": ax.plot([], [], label="Ham Veri")[0],
    "Moving Avg": ax.plot([], [], label="Moving Avg")[0],
    "Low Pass": ax.plot([], [], label="Low Pass")[0],
    "Median": ax.plot([], [], label="Median")[0],
    "EMA": ax.plot([], [], label="EMA")[0],
    "Kalman": ax.plot([], [], label="Kalman")[0],
    "Savitzky-Golay": ax.plot([], [], label="Savitzky-Golay")[0],
    "Adaptive Hybrid": ax.plot([], [], label="Adaptive Hybrid")[0],
}

ax.set_xlim(0, MAX_POINTS)
ax.set_ylim(0, 60)
ax.legend(loc='upper right')
ax.grid(True)

text_box = ax_text.text(0.01, 0.95, "", fontsize=12, va='top', ha='left', family='monospace')
ax_text.axis("off")

ani_running = True

def update(frame):
    line = ser.readline().decode(errors='ignore').strip()
    try:
        val = float(line)
        raw_data.append(val)
        ma_val = ma.update(val)
        lp_val = lp.update(val)
        med_val = med.update(val)
        ema_val = ema.update(val)
        kf_val = kf.update(val)
        sg_val = sg.update(val)
        ahf_val = ahf.update(val)

        ma_data.append(ma_val)
        lp_data.append(lp_val)
        med_data.append(med_val)
        ema_data.append(ema_val)
        kf_data.append(kf_val)
        sg_data.append(sg_val)
        ahf_data.append(ahf_val)

        if len(raw_data) > MAX_POINTS:
            raw_data.pop(0)
            ma_data.pop(0)
            lp_data.pop(0)
            med_data.pop(0)
            ema_data.pop(0)
            kf_data.pop(0)
            sg_data.pop(0)
            ahf_data.pop(0)

        x = list(range(len(raw_data)))
        lines["Ham Veri"].set_data(x, raw_data)
        lines["Moving Avg"].set_data(x, ma_data)
        lines["Low Pass"].set_data(x, lp_data)
        lines["Median"].set_data(x, med_data)
        lines["EMA"].set_data(x, ema_data)
        lines["Kalman"].set_data(x, kf_data)
        lines["Savitzky-Golay"].set_data(x, sg_data)
        lines["Adaptive Hybrid"].set_data(x, ahf_data)

        table_text = f"""
Ham Veri           : {val:.2f} cm
Moving Average     : {ma_val:.2f} cm
Low Pass           : {lp_val:.2f} cm
Median Filter      : {med_val:.2f} cm
Exponential MA     : {ema_val:.2f} cm
Kalman Filter      : {kf_val:.2f} cm
Savitzky-Golay     : {sg_val:.2f} cm
Adaptive Hybrid    : {ahf_val:.2f} cm
"""
        text_box.set_text(table_text)

    except:
        pass

    return list(lines.values()) + [text_box]

ani = animation.FuncAnimation(fig, update, interval=100)

ax_button = plt.axes([0.8, 0.05, 0.1, 0.04])
button = Button(ax_button, 'Durdur')

def on_button_clicked(event):
    global ani_running
    if ani_running:
        ani.event_source.stop()
        button.label.set_text('Başlat')
    else:
        ani.event_source.start()
        button.label.set_text('Durdur')
    ani_running = not ani_running

button.on_clicked(on_button_clicked)

from matplotlib.widgets import CheckButtons
rax = plt.axes([0.02, 0.25, 0.15, 0.6])
labels = list(lines.keys())
visibility = [line.get_visible() for line in lines.values()]
check = CheckButtons(rax, labels, visibility)

def func(label):
    line = lines[label]
    line.set_visible(not line.get_visible())
    plt.draw()

check.on_clicked(func)

plt.show()

ser.close()

