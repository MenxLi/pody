import inspect
from typing import Optional
from functools import wraps
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException
import docker

from ..eng.docker import restart_container
from ..eng.errors import *

from .impl import *

app = FastAPI(docs_url=None, redoc_url=None)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
docker_client = docker.from_env()
                    
def handle_exception(fn):
    @wraps(fn)
    async def wrapper(*args, **kwargs):
        try:
            if inspect.iscoroutinefunction(fn):
                return await fn(*args, **kwargs)
            return fn(*args, **kwargs)
        except Exception as e:
            if isinstance(e, HTTPException): 
                print(f"HTTPException: {e}, detail: {e.detail}")
            if isinstance(e, HTTPException): raise e
            if isinstance(e, InvalidInputError): raise HTTPException(status_code=400, detail=str(e))
            if isinstance(e, NotFoundError): raise HTTPException(status_code=404, detail=str(e))
            raise
    return wrapper


@app.middleware("http")
async def log_requests(request, call_next):
    print(f"Request: {request.url}")
    print(f"Headers: {request.headers}")
    print(f"From: {request.client.host}")
    response = await call_next(request)
    return response

@app.post("/restart")
@handle_exception
def restart_pod(container_name: str):
    return restart_container(docker_client, container_name, execute_after_restart="service ssh start")

@app.get("/gpu-status")
@handle_exception
def gpu_status(id: str):
    try:
        _ids = [int(i.strip()) for i in id.split(",")]
    except ValueError:
        raise InvalidInputError("Invalid GPU ID")
    return gpu_status_impl(docker_client, _ids)
                
def start_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    workers: Optional[int] = None,
):
    import uvicorn
    uvicorn.run(f"pody.svc.app:app", host=host, port=port, workers=workers)