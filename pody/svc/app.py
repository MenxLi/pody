import uvicorn
from typing import Optional

from .app_base import *
from .router_resource import router_resource
from .router_pod import router_pod

app.include_router(router_resource)
app.include_router(router_pod)

import inspect
from fastapi import Depends
from starlette.routing import Route, BaseRoute
from pody.eng.user import UserRecord
from pody.eng.errors import NotFoundError
@app.get("/help")
@handle_exception
async def help(path: Optional[str] = None, _: UserRecord = Depends(get_user)):
    """
    return the http method and params for the path
    """
    def get_path_info(route: Route):
        params = inspect.signature(route.endpoint).parameters
        return {
            "path": route.path,
            "methods": route.methods,
            "params": [str(p) for p in params if 'Depends(' not in str(params[p])]
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
                
def start_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    workers: Optional[int] = None,
):
    uvicorn.run(f"pody.svc.app:app", host=host, port=port, workers=workers)