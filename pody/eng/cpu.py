import psutil, time
from dataclasses import dataclass
from .errors import ProcessNotFoundError

@dataclass
class ProcessInfo:
    pid: int
    cmd: str
    uptime: float
    cgroup: str
    memory_used: int

# https://man7.org/linux/man-pages/man5/proc_pid_stat.5.html
def query_process(pid: int) -> ProcessInfo:
    def _cgroup_from_pid(pid: int) -> str:
        with open(f"/proc/{pid}/cgroup") as f:
            return f.read()
    
    try:
        proc = psutil.Process(pid)
    except psutil.NoSuchProcess as e:
        raise ProcessNotFoundError(f"Process {pid} not found") from e
    return ProcessInfo(
        pid=pid,
        cmd=" ".join(proc.cmdline()),
        uptime=time.time() - proc.create_time(),
        cgroup=_cgroup_from_pid(pid),
        memory_used=proc.memory_info().rss
    )
