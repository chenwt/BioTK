import sys

import pandas as pd
import click

@click.command("transpose")
def transpose():
    try:
        pd.read_csv(sys.stdin, sep="\t", header=0, index_col=0)\
                .T\
                .to_csv(sys.stdout, sep="\t")
    except BrokenPipeError:
        pass
