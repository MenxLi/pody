import uvicorn
from typing import Optional

from .app_base import *
from .router_resource import router_resource
from .router_pod import router_pod

app.include_router(router_resource)
app.include_router(router_pod)
                
def start_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    workers: Optional[int] = None,
):
    uvicorn.run(f"pody.svc.app:app", host=host, port=port, workers=workers)