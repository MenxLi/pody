from .app_base import *
from fastapi.routing import APIRouter

from ..eng.docker import restart_container

router_pod = APIRouter(prefix="/pod")

@router_pod.post("/restart")
@handle_exception
def restart_pod(container_name: str):
    return restart_container(docker_client, container_name, execute_after_restart="service ssh start")
