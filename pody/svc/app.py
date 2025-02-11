import uvicorn
from typing import Optional

from .app_base import *
from .router_resource import router_resource
from .router_pod import router_pod

app.include_router(router_resource)
app.include_router(router_pod)

@app.get("/pinfo")
@handle_exception
async def path_info(path: str):
    """
    return the http method and params for the path
    """
    import inspect
    from pody.eng.errors import NotFoundError
    from starlette.routing import Route
    path = path.split("?")[0]
    for route in app.routes:
        if not isinstance(route, Route): continue
        if route.path == path:
            params = inspect.signature(route.endpoint).parameters
            return {
                "path": path,
                "methods": route.methods,
                "params": [str(p) for p in params if 'Depends(' not in str(params[p])]
            }
    raise NotFoundError(f"Path {path} not found")
                
def start_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    workers: Optional[int] = None,
):
    uvicorn.run(f"pody.svc.app:app", host=host, port=port, workers=workers)