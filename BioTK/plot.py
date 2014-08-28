import matplotlib.pyplot as plt

def histogram(data, bins=10, 
        x_label=None, y_label=None,
        title=None, color="blue"):
    p = plt.hist(data, bins=bins, color=color)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.title(title)
    return p
