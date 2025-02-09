from .app_base import *

from fastapi.routing import APIRouter
from typing import Optional
from docker import DockerClient

from ..eng.errors import *
from ..eng.docker import query_container_by_id
from ..eng.gpu import list_processes_on_gpus, GPUProcess
from ..eng.cpu import query_process

router_resource = APIRouter(prefix="/resource")

def gpu_status_impl(client: DockerClient, gpu_ids: list[int]):
    def container_id_from_cgroup(cgoup: str) -> Optional[str]:
        last = cgoup.split("/")[-1]
        if not last.startswith("docker-"): return None
        if not last.endswith(".scope"): return None
        return last[len("docker-"):-len(".scope")]
    def fmt_gpu_proc(gpu_proc: GPUProcess):
        process_info = query_process(gpu_proc.pid)
        container_id = container_id_from_cgroup(process_info.cgroup)
        container_name = query_container_by_id(client, container_id)["name"] if container_id else ""
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

@router_resource.get("/gpu")
@handle_exception
def gpu_status(id: str):
    try:
        _ids = [int(i.strip()) for i in id.split(",")]
    except ValueError:
        raise InvalidInputError("Invalid GPU ID")
    return gpu_status_impl(docker_client, _ids)
