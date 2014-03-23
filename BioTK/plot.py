import matplotlib.pyplot as plt
import numpy as np

def histogram(data, bins=20):
    """
    Create a histogram from a collection of data points.
    """
    hist, bins = np.histogram(data, bins)
    width = 0.85 * (bins[1] - bins[0])
    center = (bins[:-1] + bins[1:]) / 2
    return plt.bar(center, hist, align="center", width=width)
