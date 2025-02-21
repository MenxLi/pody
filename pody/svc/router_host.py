from .app_base import *

from fastapi import Depends
from fastapi.routing import APIRouter
from typing import Optional

from ..eng.errors import *
from ..eng.user import UserRecord
from ..eng.docker import ImageFilter, DockerController
from ..eng.gpu import list_processes_on_gpus, GPUProcess, GPUHandler
from ..eng.cpu import query_process

from ..config import config
from ..version import VERSION

router_host = APIRouter(prefix="/host")

def gpu_status_impl(gpu_ids: list[int]):
    def fmt_gpu_proc(gpu_proc: GPUProcess):
        c = DockerController()
        process_info = query_process(gpu_proc.pid)
        container_id = c.container_from_pid(gpu_proc.pid)
        container_name = c.check_container(container_id)["name"] if container_id else ""
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
    return gpu_status_impl(_ids)

@router_host.get("/images")
@handle_exception
def list_images(_: UserRecord = Depends(require_permission("all"))):
    return list(ImageFilter(config = config()))

@router_host.get("/spec")
def spec(_: UserRecord = Depends(require_permission("all"))):
    def get_docerk_version():
        return DockerController().client.version()["Version"]
    
    def get_nv_driver_version():
        try:
            import pynvml
            pynvml.nvmlInit()
            try:
                return pynvml.nvmlSystemGetDriverVersion()
            finally:
                pynvml.nvmlShutdown()
        except Exception:
            return "N/A"
    
    def get_nv_ctk_version():
        import subprocess
        try:
            r = subprocess.run(["nvidia-ctk", "--version"], capture_output=True)
            return r.stdout.decode().strip() if r.returncode == 0 else "N/A"
        except Exception:
            return "N/A"
    
    return {
        "pody_version": '.'.join(map(str, VERSION)),
        "docker_version": get_docerk_version(),
        "nvidia_driver_version": get_nv_driver_version(),
        "nvidia_ctk_version": get_nv_ctk_version(),
    }