from typing import List, Optional
import sys, os, json

from pody.api import PodyAPI, ClientRequestError
from rich.console import Console
import typer

def cli_command():
    return sys.argv[0].split(os.sep)[-1]
def error_dict(e: ClientRequestError):
    return {
        "error_code": e.error_code,
        "message": e.error_message,
        "context": e.error_context,
    }

app = typer.Typer(
    help = """Pody CLI client, please refer to [docs]/api for more information. """, 
    no_args_is_help=True
)
console = Console()

def parse_param_va_args(args: Optional[List[str]]):
    res = {}
    if not args: return res
    for arg in args:
        sp = arg.split(':')
        res[sp[0]] = ':'.join(sp[1:])
    return res

@app.command(
    no_args_is_help=True, help=f"Send HTTP GET request to Pody API, e.g. {cli_command()} get /host/gpu-ps id:0,1", 
    rich_help_panel="Request"
    )
def get(
    path: str, 
    args: Optional[List[str]] = typer.Argument(None, help="Query parameters in the form of key:value, separated by space"), 
    raw: bool = False
    ):
    api = PodyAPI()
    try:
        res = api.get(path, parse_param_va_args(args))
        if raw: print(json.dumps(res))
        else: console.print(res)
    except ClientRequestError as e:
        console.print(error_dict(e))
        exit(1)

@app.command(
    no_args_is_help=True, help=f"Send HTTP POST request to Pody API, e.g. {cli_command()} post /pod/restart ins:my_pod", 
    rich_help_panel="Request"
    )
def post(
    path: str, 
    args: Optional[List[str]] = typer.Argument(None, help="Query parameters in the form of key:value, separated by space"), 
    raw: bool = False
    ):
    api = PodyAPI()
    try:
        res = api.post(path, parse_param_va_args(args))
        if raw: print(json.dumps(res))
        else: console.print(res)
    except ClientRequestError as e:
        console.print(error_dict(e))
        exit(1)

@app.command(
    no_args_is_help=True, help=
        "Send HTTP request to Pody API. "
        "Automatic infer method verb for the path "
        "(an additional request will be made to fetch the path info), \n"
        f"e.g. {cli_command()} auto /pod/restart ins:my_pod",
    rich_help_panel="Request"
    )
def fetch(
    path: str, 
    args: Optional[List[str]] = typer.Argument(None, help="Query parameters in the form of key:value, separated by space"), 
    raw: bool = False
    ):
    api = PodyAPI()
    try:
        res = api.fetch_auto(path, parse_param_va_args(args))
        if raw: print(json.dumps(res))
        else: console.print(res)
    except ClientRequestError as e:
        console.print(error_dict(e))
        exit(1)

@app.command(
    help=f"Display help for the path, e.g. {cli_command()} help /pod/restart", 
    rich_help_panel="Help"
    )
def help(
    path: Optional[str] = typer.Argument('/', help="Path to get help for"),
    _: Optional[List[str]] = typer.Argument(None, help="Ignored"), 
    ):
    def fmt_path_info(r):
        return f"{r['path']} [{', '.join(r['methods'])}]: {r['params']}"
    api = PodyAPI()
    try:
        res = api.get("/help", {"path": path})
        for r in res:
            console.print(fmt_path_info(r))
    except ClientRequestError as e:
        console.print(error_dict(e))
        exit(1)

@app.command(
    help = "Open the API documentation in the browser",
    rich_help_panel="Help"
    )
def manual():
    import webbrowser
    api = PodyAPI()
    webbrowser.open_new_tab(f"{api.api_base}/docs/pody-cli.html")