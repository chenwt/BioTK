import argparse
import functools

import numpy as np
import matplotlib.pyplot as plt

DEFAULT_COLOR = "blue"

def argparse_template():
    p = argparse.ArgumentParser()
    p.add_argument("--color", "-c", default="blue")
    p.add_argument("--y-label", "-y")
    p.add_argument("--x-label", "-x")
    p.add_argument("--y-range")
    p.add_argument("--title", "-t")
    p.add_argument("outfile")
    return p

def figure_builder(fn):
    @functools.wraps(fn)
    def wrap(*args, 
            x_label=None, y_label=None, title=None, y_range=None,
            **kwargs):

        _ = fn(*args, **kwargs)

        if x_label is not None:
            plt.xlabel(x_label)
        if y_label is not None:
            plt.ylabel(y_label)
        if title is not None:
            plt.title(title)
        if y_range is not None:
            y_min, y_max = map(float, y_range.split(","))
            plt.ylim((y_min, y_max))

        ax = plt.gcf()
        for ax in plt.gcf().get_axes():
            for item in [ax.title, ax.xaxis.label, ax.yaxis.label]:
                item.set_fontsize(35)
            for item in ax.get_xticklabels() + ax.get_yticklabels():
                item.set_fontsize(20)

        plt.tight_layout()
        return ax

    def cli(ap_args, *args, **kwargs):
        # ap_args = result of ArgumentParser.parse_args()
        keys = [k for k in dir(ap_args) if not k.startswith("_")]
        out_path = ap_args.outfile
        keys.remove("outfile")
        for k in keys:
            v = getattr(ap_args, k)
            if v is not None:
                kwargs[k] = v
        plot = wrap(*args, **kwargs)
        plt.savefig(out_path, dpi=180)

    wrap.cli = cli
    return wrap

@figure_builder
def histogram(data, bins=10, color=DEFAULT_COLOR):
    p = plt.hist(data, bins=bins, color=color)
    return p

@figure_builder
def barplot(y, error=None, horizontal=False, color=DEFAULT_COLOR):
    # NB: "y" local variables refer to the data direction 
    # (y in a normal bar plot), whereas matplotlib functions refer
    # to the actual axis in the final plot (x or y)

    bar_kwargs = {}
    error_kwargs = {}

    if error is not None:
        assert len(error) == len(y)
        error_key = "xerr" if horizontal else "yerr"
        bar_kwargs[error_key] = error

        error_kwargs["ecolor"] = "red"
        error_kwargs["elinewidth"] = 4
        error_kwargs["capsize"] = 4

    edge_scale_factor = 1.1 if error is None else 1.5
    x = np.arange(len(y))

    width = 1 - 0.2
    bar_fn = plt.barh if horizontal else plt.bar
    ylim_fn,xlim_fn = (plt.xlim,plt.ylim) if horizontal else (plt.ylim,plt.xlim)
    bar_fn(x, y, width, 
            color=color, error_kw=error_kwargs, 
            **bar_kwargs)
    ax = plt.gcf().get_axes()[0]
    y_min = y.min() * edge_scale_factor if y.min() < 0 else 0

    if horizontal:
        ax.set_yticks(x+width/2)
        ax.set_yticklabels(y.index)
        if y.min() < 0:
            plt.axvline(0, color="black", linewidth=0.3)
    else:
        ax.set_xticks(x+width/2)
        ax.set_xticklabels(y.index, rotation=45)
        if y.min() < 0:
            plt.axhline(0, color="black", linewidth=0.3)

    xlim_fn((-0.5,len(y)+0.5))
    ylim_fn((y_min, y.max() * edge_scale_factor))

    return ax
