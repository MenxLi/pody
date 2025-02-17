from .app_base import *

from fastapi import Depends
from fastapi.routing import APIRouter
from typing import Optional
from docker import DockerClient

from ..eng.errors import *
from ..eng.user import UserRecord
from ..eng.docker import check_container, list_docker_images, container_from_pid
from ..eng.gpu import list_processes_on_gpus, GPUProcess, GPUHandler
from ..eng.cpu import query_process

from ..config import config

router_host = APIRouter(prefix="/host")

def gpu_status_impl(client: DockerClient, gpu_ids: list[int]):
    def fmt_gpu_proc(gpu_proc: GPUProcess):
        process_info = query_process(gpu_proc.pid)
        container_id = container_from_pid(g_client, gpu_proc.pid)
        container_name = check_container(client, container_id)["name"] if container_id else ""
        return {
            "pid": gpu_proc.pid,
            "pod": container_name,
            "cmd": process_info.cmd,
            "uptime": process_info.uptime,
            "memory_used": process_info.memory_used,
            "gpu_memory_used": gpu_proc.gpu_memory_used,
        }
    gpu_procs = list_processes_on_gpus(gpu_ids)
    return {gpu_id: [fmt_gpu_proc(proc) for proc in gpu_procs[gpu_id]] for gpu_id in gpu_procs}

@router_host.get("/gpu-ps")
@handle_exception
def gpu_status(id: Optional[str] = None):
    if id is None:
        _ids = list(range(GPUHandler().device_count()))
    else:
        try:
            _ids = [int(i.strip()) for i in id.split(",")]
        except ValueError:
            raise InvalidInputError("Invalid GPU ID")
    return gpu_status_impl(g_client, _ids)

@router_host.get("/images")
@handle_exception
def list_images(user: UserRecord = Depends(require_permission("all"))):
    server_config = config()
    raw_images = list_docker_images(g_client)
    allowed_images = [image.name for image in server_config.images]
    return [image for image in raw_images if image in allowed_images]
