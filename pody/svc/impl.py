""" Service logic implementation, independent of the server framework. """
from typing import Optional
from docker import DockerClient

from ..eng.docker import query_container_by_id
from ..eng.gpu import list_processes_on_gpus, GPUProcess

def gpu_status_impl(client: DockerClient, gpu_ids: list[int]):
    def container_id_from_cgroup(cgoup: str) -> Optional[str]:
        last = cgoup.split("/")[-1]
        if not last.startswith("docker-"): return None
        if not last.endswith(".scope"): return None
        return last[len("docker-"):-len(".scope")]
    def fmt_gpu_proc(gpu_proc: GPUProcess):
        container_id = container_id_from_cgroup(gpu_proc.cgoup)
        if container_id is None: return {"pid": gpu_proc.pid, "gpu_memory_used": gpu_proc.gpu_memory_used, "container": None}   # not running in a container
        container_info = query_container_by_id(client, container_id)
        if container_info is not None:
            del container_info["ports"]
            del container_info["status"]
        return {
            "pid": gpu_proc.pid,
            "gpu_memory_used": gpu_proc.gpu_memory_used,
            "container": container_info
        }
    gpu_procs = list_processes_on_gpus(gpu_ids)
    return {gpu_id: [fmt_gpu_proc(proc) for proc in gpu_procs[gpu_id]] for gpu_id in gpu_procs}