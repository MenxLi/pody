import inspect
from functools import wraps
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException
import docker

from ..eng.errors import *

app = FastAPI()
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

__all__ = ["app", "docker_client", "handle_exception"]
                