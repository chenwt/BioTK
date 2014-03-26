import matplotlib.pyplot as plt
import numpy as np

from .heatmap import heatmap

def histogram(data, bins=20, title=None, xlabel=None, ylabel=None):
    """
    Create a histogram from a collection of data points.
    """
    hist, bins = np.histogram(data, bins)
    width = 0.85 * (bins[1] - bins[0])
    center = (bins[:-1] + bins[1:]) / 2
    if title:
        plt.title(title)
    if xlabel:
        plt.xlabel(xlabel)
    if ylabel:
        plt.ylabel(ylabel)
    return plt.bar(center, hist, align="center", width=width)
