import sqlite3

import click

@click.group()
def cli():
    pass

##################
# Label extraction
##################

@cli.group()
def labels():
    pass

@labels.command()
def extract():
    pass

@labels.command()
def validate():
    pass

if __name__ == "__main__":
    cli()
