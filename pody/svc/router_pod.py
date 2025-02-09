from .app_base import *
from fastapi import Depends
from fastapi.routing import APIRouter

from ..eng.user import UserRecord
from ..eng.docker import ContainerAction, container_action

router_pod = APIRouter(prefix="/pod")

@router_pod.post("/restart")
@handle_exception
def restart_pod(tag: str, user: UserRecord = Depends(get_user)):
    container_name = f"{user.name}-{tag}"
    return container_action(docker_client, container_name, ContainerAction.RESTART, after_action="service ssh restart")
