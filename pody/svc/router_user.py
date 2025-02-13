import dataclasses

from .app_base import *
from fastapi import Depends
from fastapi.routing import APIRouter

from ..eng.user import UserRecord, UserDatabase

router_user = APIRouter(prefix="/user")

@router_user.get("/info")
@handle_exception
def info_user(user: UserRecord = Depends(require_permission("all"))):
    user_quota = UserDatabase().check_user_quota(user.name)
    user_dict = dataclasses.asdict(user)
    quota_dict = dataclasses.asdict(user_quota)
    user_dict.pop("userid")
    quota_dict.pop("userid")
    return {"user": user_dict, "quota": quota_dict}

@router_user.get("/list")
@handle_exception
def list_user(user: UserRecord = Depends(require_permission("all"))):
    users = UserDatabase().list_users()
    return [dataclasses.asdict(u).pop("name") for u in users]

@router_user.post("/ch-passwd")
@handle_exception
def change_passwd(passwd: str, user: UserRecord = Depends(require_permission("all"))):
    UserDatabase().update_user(user.name, password=passwd)
    return {"message": "Password updated"}
