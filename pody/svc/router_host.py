from .app_base import *

from fastapi import Depends
from fastapi.routing import APIRouter
from fastapi.responses import RedirectResponse
from typing import Optional

from ..eng.errors import *
from ..eng.user import UserRecord
from ..eng.docker import DockerController
from ..eng.gpu import GPUHandler
from ..eng.resmon import ProcessIter

from ..version import VERSION

router_host = APIRouter(prefix="/host")

def gpu_status_impl(gpu_ids: list[int]):
    def gpu_proc_filter(p: ProcessIter.ContainerProcessInfo):
        if p.gproc is None:
            return ProcessIter.FilterReturn(is_valid=False)
        r = {
            "pid": p.gproc.pid,
            "pod": p.container_name,
            "cmd": p.cproc.cmd if p.container_name else "[host process]",
            "uptime": p.cproc.uptime,
            "memory_used": p.cproc.memory_used,
            "gpu_memory_used": p.gproc.gpu_memory_used,
        }
        return ProcessIter.FilterReturn(is_valid=True, extra=r)
    
    piter = ProcessIter(filter_fn=gpu_proc_filter, docker_only=False)
    return {i: list(map(lambda x: x[1], piter.gpu_process([i]))) for i in gpu_ids}

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

@router_host.get("/images")
@deprecated_route("Use /image/list instead, will be removed in 0.4.0")
def list_images_deprecated(_: UserRecord = Depends(require_permission("all"))):
    ...