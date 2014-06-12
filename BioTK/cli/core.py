import multiprocessing as mp

from click import group, command, argument, option

import BioTK.cli.geo

@group()
def btk():
    pass

@btk.group()
def db():
    """
    Query or modify the BioTK database
    """
    pass

@btk.group()
def geo():
    """
    Manipulate data from NCBI GEO
    """
    pass

@geo.command("extract-expression")
@argument("miniml_archive")
def geo_extract_expression(miniml_archive):
    return BioTK.cli.geo.extract_expression(miniml_archive)

@geo.command("attribute")
@argument("species_name")
@option("--default-age-unit", "-u")
def geo_attribute(*args, **kwargs):
    return BioTK.cli.geo.attribute(*args, **kwargs)
