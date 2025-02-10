import inspect
from functools import wraps
import docker.errors
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException
from fastapi.security import HTTPBasicCredentials, HTTPBasic
import docker

from ..eng.errors import *
from ..eng.user import UserDatabase, hash_password

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
g_client = docker.from_env()
g_user_db = UserDatabase()
                    
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
            if isinstance(e, docker.errors.NotFound): raise HTTPException(status_code=404, detail=str(e))
            if isinstance(e, docker.errors.APIError): raise HTTPException(status_code=500, detail=str(e))
            raise
    return wrapper

async def get_user(credentials: HTTPBasicCredentials = Depends(HTTPBasic(auto_error=True))):
    key = hash_password(credentials.username, credentials.password)
    user = g_user_db.check_user(key)
    if user.userid == 0:
        raise InsufficientPermissionsError("Invalid username or password")
    return user

@app.middleware("http")
async def log_requests(request, call_next):
    print(f"Request: {request.url}")
    print(f"Headers: {request.headers}")
    print(f"From: {request.client.host}")
    response = await call_next(request)
    return response

__all__ = ["app", "g_client", "g_user_db", "get_user", "handle_exception"]
                