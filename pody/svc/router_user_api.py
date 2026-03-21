
from .app_base import *
from fastapi import Depends, Request, Query, Response
from fastapi.routing import APIRouter
from fastapi.exceptions import HTTPException
from functools import wraps
from typing import Callable, Optional

from ..eng.user import UserDatabase
from ..config import config

router_user_api = APIRouter(prefix="/user_api")

def authorized_local_userdb(request: Request) -> UserDatabase:
    cfg = config()

    if not (cfg.remote_user_profile.service.enabled):
        raise HTTPException(status_code=501, detail="Remote user profile service is not enabled")
    if not (cfg.remote_user_profile.service.access_token):
        raise HTTPException(status_code=500, detail="Remote user profile service is not properly configured")
    
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    token = auth_header[len("Bearer "):]
    if token != cfg.remote_user_profile.service.access_token:
        raise HTTPException(status_code=403, detail="Invalid access token")

    return UserDatabase(mode='local')

def mut_ops(fn: Callable):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if config().remote_user_profile.service.readonly:
            raise HTTPException(status_code=423, detail="User profile service is in read-only mode")
        return fn(*args, **kwargs)
    return wrapper

@router_user_api.post("/add_user")
@mut_ops
def add_user(
    user_db: UserDatabase = Depends(authorized_local_userdb),
    username: str = Query(..., description="Username of the new user"),
    password: str = Query(..., description="Password of the new user"),
    is_admin: bool = Query(False, description="Whether the new user is an admin")
):
    user_db.add_user(username, password, is_admin)
    return {"message": f"User '{username}' added successfully"}

@router_user_api.post("/update_user")
@mut_ops
def update_user(
    user_db: UserDatabase = Depends(authorized_local_userdb),
    username: str = Query(..., description="Username of the user to update"),
    password: Optional[str] = Query(None, description="New password of the user"),
    is_admin: Optional[bool] = Query(None, description="Whether to make the user an admin")
    ):
    update_fields = {}
    if password is not None:
        update_fields['password'] = password
    if is_admin is not None:
        update_fields['is_admin'] = is_admin
    
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    user_db.update_user(username, **update_fields)
    return {"message": f"User '{username}' updated successfully"}

@router_user_api.post("/delete_user")
@mut_ops
def delete_user(
    user_db: UserDatabase = Depends(authorized_local_userdb),
    username: str = Query(..., description="Username of the user to delete")
):
    user_db.delete_user(username)
    return {"message": f"User '{username}' deleted successfully"}

@router_user_api.get("/get_user")
def get_user(
    response: Response,
    user_db: UserDatabase = Depends(authorized_local_userdb),
    user_id: Optional[int] = Query(None, description="ID of the user to retrieve"),
    username: Optional[str] = Query(None, description="Username of the user to retrieve")
):
    response.headers["X-Skip-Log"] = "1"
    if user_id is None and username is None:
        raise HTTPException(status_code=400, detail="Either user_id or username must be provided")
    if user_id is not None and username is not None:
        raise HTTPException(status_code=400, detail="Only one of user_id or username should be provided")
    user = user_db.get_user(user_id or username)    # type: ignore
    return user

@router_user_api.get("/check_user")
def check_user(
    response: Response,
    user_db: UserDatabase = Depends(authorized_local_userdb),
    credential: str = Query(..., description="Credential to check")
):
    response.headers["X-Skip-Log"] = "1"
    user = user_db.check_user(credential)
    return user

@router_user_api.get("/list_users")
def list_users(
    response: Response,
    user_db: UserDatabase = Depends(authorized_local_userdb),
    usernames: Optional[str] = Query(None, description="Comma-separated list of usernames to filter by")
):
    response.headers["X-Skip-Log"] = "1"
    username_list = [u.strip() for u in usernames.split(",")] if usernames else None
    users = user_db.list_users(username_list)
    return users