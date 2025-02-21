import inspect, json
from functools import wraps
import docker.errors
from fastapi import FastAPI, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException
from fastapi.security import HTTPBasicCredentials, HTTPBasic
from contextlib import asynccontextmanager
from typing import Literal
import docker

from ..eng.errors import *
from ..eng.log import get_logger
from ..config import config
from ..eng.user import UserDatabase, hash_password

g_user_db = UserDatabase()

@asynccontextmanager
async def life_span(app: FastAPI):
    config()    # maybe init configuration file at the beginning
    yield
    g_user_db.close()

app = FastAPI(docs_url=None, redoc_url=None, lifespan=life_span)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
                    
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
            if isinstance(e, PermissionError): raise HTTPException(status_code=403, detail=str(e))
            if isinstance(e, NotFoundError): raise HTTPException(status_code=404, detail=str(e))
            if isinstance(e, DuplicateError): raise HTTPException(status_code=409, detail=str(e))
            if isinstance(e, docker.errors.NotFound): raise HTTPException(status_code=404, detail=str(e))
            if isinstance(e, docker.errors.APIError): raise HTTPException(status_code=500, detail=str(e))
            raise
    return wrapper

async def get_user(credentials: HTTPBasicCredentials = Depends(HTTPBasic(auto_error=True))):
    key = hash_password(credentials.username, credentials.password)
    user = g_user_db.check_user(key)
    if user.userid == 0:
        raise HTTPException(403, "Invalid username or password")
    return user

def require_permission(permission: Literal['all', 'admin'] = "all"):
    def _require_permission(user = Depends(get_user)):
        if permission == 'all' or user.is_admin: 
            return user
        if permission == 'admin' and not user.is_admin:
            raise HTTPException(403, f"User does not have permission: {permission}")
        return user
    return _require_permission

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger = get_logger('requests')
    response: Response = await call_next(request)
    logger.debug(json.dumps({
        "url": str(request.url),
        "method": str(request.method),
        "client": str(request.client.host if request.client else 'unknown'),
        "headers": dict(request.headers),
        "status": response.status_code,
    }))
    return response

__all__ = ["app", "g_user_db", "get_user", "require_permission", "handle_exception"]
                