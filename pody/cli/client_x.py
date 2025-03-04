
from typer import Typer
from .client import fetch

app = Typer()
app.command(
    help=\
        "Shorthand for `pody fetch` command, any additional arguments will be passed to the fetch command. "
        "Please refer to `pody fetch --help` for more information.",
    no_args_is_help=True
)(fetch)