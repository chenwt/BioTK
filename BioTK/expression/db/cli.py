from cement.core import controller, foundation, handler

from .core import ExpressionDB

class BaseController(controller.CementBaseController):
    class Meta:
        label = "base"
        description = "foo"
        config_defaults = dict()

        arguments = [
                (["-d", "--db-path"], dict(action="store",
                    required=True,
                    help="Path to the expression DB file."))
        ]

class LoadController(controller.CementBaseController):
    class Meta:
        label = "load"
        stacked_on = "base"
        arguments = [
                (["file_or_accession"], dict(nargs="+")),
        ]

    @controller.expose(hide=True, aliases=["load", "import"],
            help="Import expression data into the database.")
    def default(self):
        db = ExpressionDB(self.app.pargs.db_path)
        for file in self.app.pargs.file_or_accession:
            self.app.log.info("Importing %s" % file)
            db.add_family(file)

class CLI(foundation.CementApp):
    class Meta:
        label = "expression-db"
        base_controller = BaseController

def main():
    cli = CLI()
    handler.register(LoadController)
    try:
        cli.setup()
        cli.run()
    finally:
        cli.close()

if __name__ == "__main__":
    main()

"""
import argparse

def main(args):
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", "-d",
            required=True)
    parser.add_argument("soft_file", nargs="+")
    args = parser.parse_args(args)

    db = ExpressionDB(args.db_path)
    for path in args.soft_file:
        try:
            db.add_family(path)
        except:
            pass

if __name__ == "__main__":
    main(sys.argv[1:])
"""
