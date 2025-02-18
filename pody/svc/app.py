import uvicorn
from typing import Optional

from fastapi.staticfiles import StaticFiles
from .daemon import daemon_context
from .app_base import *
from .router_host import router_host
from .router_pod import router_pod
from .router_user import router_user
from ..config import SRC_HOME
from ..version import VERSION

app.mount("/pody", StaticFiles(directory=SRC_HOME / "doc", html=True), name="pody-doc")
app.include_router(router_host)
app.include_router(router_pod)
app.include_router(router_user)

import inspect
from fastapi import Depends
from starlette.routing import Route, BaseRoute
from pody.eng.user import UserRecord
@app.get("/help")
@handle_exception
async def help(path: Optional[str] = None, _: UserRecord = Depends(get_user)):
    """
    return the http method and params for the path
    """
    def get_path_info(route: Route):
        params = inspect.signature(route.endpoint).parameters
        def fmt_param(p: inspect.Parameter) -> Optional[dict]:
            try:
                if p.annotation == UserRecord:  # skip user dependency
                    return None
                return {
                    "name": p.name,
                    "optional": p.default != inspect.Parameter.empty, 
                    # "type": str(p.annotation),    # or p.annotation.__name__
                }
            except Exception:
                return None
        return {
            "path": route.path,
            "methods": route.methods,
            "params": [x for p in params if (x:=fmt_param(params[p])) is not None]
        }
    def filter_routes(routes: list[BaseRoute]) -> list[Route]:
        def criteria(route: BaseRoute):
            return isinstance(route, Route) and not route.path in [
                "/docs", "/openapi.json", "/redoc", "/docs", "/docs/oauth2-redirect", 
            ]
        return [route for route in routes if criteria(route)]   # type: ignore
        

    route_candidates = filter_routes(app.routes)
    if path is None:
        return [get_path_info(route) for route in route_candidates if isinstance(route, Route)]

    path = path.split("?")[0]   # remove query string
    ret = []
    for route in route_candidates:
        if not isinstance(route, Route): continue
        if (path.endswith("/") and route.path.startswith(path)) or route.path == path:
            ret.append(get_path_info(route))
    return ret

@app.get("/version")
def version():
    return VERSION
                
def start_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    workers: Optional[int] = None,
):
    with daemon_context():
        uvicorn.run(f"pody.svc.app:app", host=host, port=port, workers=workers)