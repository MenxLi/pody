from typing import List, Optional
import sys, os

from pody.api import PodyAPI
from rich.console import Console
import typer


def cli_command():
    return sys.argv[0].split(os.sep)[-1]

app = typer.Typer(
    help = """Pody CLI client, please refer to [docs]/api for more information. """, 
    no_args_is_help=True
)
console = Console()

def parse_va_args(args: Optional[List[str]]):
    res = {}
    if not args: return res
    for arg in args:
        sp = arg.split(':')
        res[sp[0]] = ':'.join(sp[1:])
    return res

@app.command(no_args_is_help=True, help=f"GET request to Pody API, e.g. {cli_command()} get /host/gpu-ps id:0,1")
def get(
    path: str, 
    args: Optional[List[str]] = typer.Argument(None, help="Query parameters in the form of key:value, separated by space"), 
    plain: bool = False
    ):
    api = PodyAPI()
    res = api.get(path, parse_va_args(args))
    if plain: print(res)
    else: console.print(res)

@app.command(no_args_is_help=True, help=f"POST request to Pody API, e.g. {cli_command()} post /pod/restart ins:my_pod")
def post(
    path: str, 
    args: Optional[List[str]] = typer.Argument(None, help="Query parameters in the form of key:value, separated by space"), 
    plain: bool = False
    ):
    api = PodyAPI()
    res = api.post(path, parse_va_args(args))
    if plain: print(res)
    else: console.print(res)