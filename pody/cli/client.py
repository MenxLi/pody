from typing import List, Optional
from functools import wraps
import sys, os, json

from rich.console import Console
from rich.table import Table
import typer

from pody.eng.utils import format_storage_size, format_time
from pody.api import PodyAPI, ClientRequestError
from pody import __version__

app = typer.Typer(
    help = """Pody CLI client, please refer to [docs]/api for more information. """, 
    no_args_is_help=True
)

def cli_command():
    return sys.argv[0].split(os.sep)[-1]
def error_dict(e: ClientRequestError):
    return {
        "error_code": e.error_code,
        "message": e.error_message,
        "context": e.error_context,
    }
def handle_request_error():
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if 'raw' in kwargs:
                print_raw = kwargs['raw']
                assert isinstance(print_raw, bool)
            else:
                print_raw = False

            try:
                return f(*args, **kwargs)
            except ClientRequestError as e:
                if print_raw: print(json.dumps(error_dict(e)))
                else: console.print(f"[bold red]Error - {e.error_message}")
                exit(1)
            except ValueError as e:
                if print_raw: print(json.dumps(error_dict(ClientRequestError(-1, str(e)))))
                else: console.print(f"[bold red]Error - {e}")
                exit(1)
        return wrapped
    return wrapper

console = Console()

def parse_param_va_args(args: Optional[List[str]]):
    def infer_sep(s: str):
        if not (':' in s or '=' in s): return None
        if ':' in s and not '=' in s: return ':'
        if '=' in s and not ':' in s: return '='
        return ':' if s.index(':') < s.index('=') else '='

    res = {}
    if not args: return res
    for i, arg in enumerate(args):
        sep = infer_sep(arg)
        if not sep: 
            raise ValueError(f"Invalid argument: {arg}, the format should be key:value or key=value")
        arg_sp = arg.split(sep)
        key, val = arg_sp[0], sep.join(arg_sp[1:])
        if val == '':
            assert i == len(args) - 1, f"Invalid argument: {key}, only last argument can be read from stdin"
            val = sys.stdin.read().strip()
        res[key] = val
    return res

@handle_request_error()
def fetch_impl(method: str, path: str, args: Optional[list[str]], raw: bool):
    def fmt_unit(res):
        """ Format some numeric values in the response to human-readable format """
        storage_size_kw = set(("memory_limit", "gpu_memory_used", "memory_used", "shm_size"))
        time_size_kw = ["uptime"]
        if isinstance(res, list):
            return [fmt_unit(r) for r in res]
        if isinstance(res, dict):
            for k,v in res.items():
                if isinstance(v, int) and k in storage_size_kw and v != -1: 
                    res[k] = f"{format_storage_size(v, 1)} ({v})"
                elif isinstance(v, (int, float)) and k in time_size_kw:
                    res[k] = f"{format_time(v)} ({v})"
                else:
                    res[k] = fmt_unit(v)
        return res
    
    # if the path ends with /, fetch the help info
    if path.endswith('/'):
        return help(path, None)

    api = PodyAPI()
    match method:
        case "get": res = api.get(path, parse_param_va_args(args))
        case "post": res = api.post(path, parse_param_va_args(args))
        case "auto": res = api.fetch_auto(path, parse_param_va_args(args))
        case _: raise ValueError(f"Invalid method {method}")
    if raw: print(json.dumps(res))
    else: console.print(fmt_unit(res))

@app.command(
    no_args_is_help=True, help=f"Send HTTP GET request to Pody API, e.g. {cli_command()} get /host/gpu-ps id:0,1", 
    rich_help_panel="Request"
    )
def get(
    path: str, 
    args: Optional[List[str]] = typer.Argument(None, help="Query parameters in the form of key:value, separated by space"), 
    raw: bool = False
    ):
    return fetch_impl("get", path, args, raw = raw)

@app.command(
    no_args_is_help=True, help=f"Send HTTP POST request to Pody API, e.g. {cli_command()} post /pod/restart ins:my_pod", 
    rich_help_panel="Request"
    )
def post(
    path: str, 
    args: Optional[List[str]] = typer.Argument(None, help="Query parameters in the form of key:value, separated by space"), 
    raw: bool = False
    ):
    return fetch_impl("post", path, args, raw = raw)

def fetch(
    path: str, 
    args: Optional[List[str]] = typer.Argument(None, help="Query parameters in the form of key:value, separated by space"), 
    raw: bool = False
    ):
    return fetch_impl("auto", path, args, raw = raw)
app.command(
    no_args_is_help=True, help=
        "Send HTTP request to Pody API. "
        "Automatic infer method verb for the path "
        "(an additional request will be made to fetch the path info), \n"
        f"e.g. {cli_command()} fetch /pod/restart ins:my_pod",
    rich_help_panel="Request"
    )(fetch)

@handle_request_error()
def help(
    path: Optional[str] = typer.Argument('/', help="Path to get help for"),
    _: Optional[List[str]] = typer.Argument(None, help="Ignored"), 
    ):
    table = Table(title=None, show_header=True)
    table.add_column("Path", style="cyan")
    table.add_column("Methods", style="magenta")
    table.add_column("Params", style="green")

    api = PodyAPI()
    if not path is None and not path.startswith("/"):
        path = f"/{path}"
    res = api.get("/help", {"path": path})
    for r in res:
        table.add_row(r['path'], ', '.join(r['methods']), ', '.join([
            f"{p['name']}{'?' if p['optional'] else ''}" for p in r['params']
        ]))
    console.print(table)
app.command(
    help=f"Display help for the path, e.g. {cli_command()} help /pod/restart", 
    rich_help_panel="Help"
    )(help)

@app.command(
    help = "Open the API documentation in the browser",
    rich_help_panel="Help"
    )
def manual():
    import webbrowser
    api = PodyAPI()
    webbrowser.open_new_tab(f"{api.api_base}/pody/pody-cli.html")

@app.command(
    help = "Display the version of the Pody client and server",
    rich_help_panel="Help"
    )
def version():
    def fmt_version(v: tuple[int, ...]):
        return '.'.join(map(str, v))
    client_version = __version__
    console.print(f"Client version: [bold]{fmt_version(client_version)}")
    try:
        # in case the server is not available, or credentials not set
        api = PodyAPI()
        server_version = tuple(api.get("/version"))
        console.print(f"Server version: [bold]{fmt_version(server_version)}")

        if client_version != server_version:
            console.print(f"[bold yellow]Warning: Version mismatch, you may consider re-install the client with `pip install pody=={fmt_version(server_version)}`")
    except Exception as e:
        console.print(f"[bold red]Failed to fetch server version: {e}")