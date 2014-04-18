import matplotlib.pyplot as plt
import numpy as np

from .heatmap import heatmap

def histogram(data, bins=20, 
        title=None, x_label=None, y_label=None,
        color="blue"):
    """
    Create a histogram from a collection of data points.
    """
    hist, bins = np.histogram(data, bins)
    width = 0.85 * (bins[1] - bins[0])
    center = (bins[:-1] + bins[1:]) / 2
    if title:
        plt.title(title)
    if x_label:
        plt.xlabel(x_label)
    if y_label:
        plt.ylabel(y_label)
    return plt.bar(center, hist, align="center", width=width,
            color=color)
