from click import group, command

@group()
def btk():
    pass

@btk.group()
def db():
    """
    Query or modify the BioTK database
    """
    pass

@db.group()
def geo():
    pass
