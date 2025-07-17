"""
Resource monitoring utilities (High-level docker and GPU process monitoring)
"""
import psutil, time
from typing import Iterator, Callable, Optional
import dataclasses
from .log import get_logger
from .gpu import GPUHandler, list_processes_on_gpus, GPUProcessInfo
from .docker import DockerController
from .errors import ProcessNotFoundError

@dataclasses.dataclass
class ProcessInfo:
    pid: int
    cmd: str
    cgroup: str
    uptime: float
    cputime: float      # CPU time in seconds
    memory_used: int    # in bytes

    def json(self):
        return dataclasses.asdict(self)

# https://man7.org/linux/man-pages/man5/proc_pid_stat.5.html
def query_process(pid: int) -> ProcessInfo:
    def _cgroup_from_pid(pid: int) -> str:
        with open(f"/proc/{pid}/cgroup") as f:
            return f.read()
    
    try:
        proc = psutil.Process(pid)
    except psutil.NoSuchProcess as e:
        raise ProcessNotFoundError(f"Process {pid} not found") from e
    
    cputimes = proc.cpu_times()
    return ProcessInfo(
        pid=pid,
        cmd=" ".join(proc.cmdline()),
        cgroup=_cgroup_from_pid(pid),
        uptime=time.time() - proc.create_time(),
        cputime=cputimes.user + cputimes.system, 
        memory_used=proc.memory_info().rss, 
    )

@dataclasses.dataclass
class ContainerProcessInfo:
    container_name: str
    cproc: ProcessInfo
    gproc: Optional[GPUProcessInfo] = None

    def json(self):
        return {
            "container_name": self.container_name,
            "cproc": self.cproc.json(),
            "gproc": dataclasses.asdict(self.gproc) if self.gproc else None,
        }

class ResourceMonitor:
    def __init__(self, filter_fn: Callable[[ContainerProcessInfo], bool] = lambda _: True):
        self.logger = get_logger("resmon")
        self.filter_fn = filter_fn
        self.docker_con = DockerController()
        self.gpu_handler = GPUHandler()
    
    def docker_proc_iter(self) -> Iterator[ContainerProcessInfo]:
        for proc in psutil.process_iter(['pid']):
            try:
                pid = proc.info['pid']
                if not (name:=self.docker_con.container_from_pid(pid)):
                    continue
                p = ContainerProcessInfo(
                    container_name = name,
                    cproc = query_process(pid),
                    gproc = None
                )
                if self.filter_fn(p):
                    yield p
            except Exception as e:
                self.logger.error(f"Error querying process {pid} [{type(e)}]: {e}")
                continue
    
    def docker_gpu_proc_iter(self, gpu_ids: list[int]) -> Iterator[ContainerProcessInfo]:
        gpu_procs = list_processes_on_gpus(gpu_ids)
        for _, procs in gpu_procs.items():
            for proc in procs:
                try:
                    pid = proc.pid
                    if not (name := self.docker_con.container_from_pid(pid)):
                        continue
                    cproc = query_process(pid)
                    p = ContainerProcessInfo(
                        container_name=name,
                        cproc=cproc,
                        gproc=proc
                    )
                    if self.filter_fn(p):
                        yield p
                except Exception as e:
                    self.logger.error(f"Error querying process {pid} [{type(e)}]: {e}")
                    continue

if __name__ == "__main__":
    monitor = ResourceMonitor()
    for proc in monitor.docker_proc_iter():
        print(proc.json())
