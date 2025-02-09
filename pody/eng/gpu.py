import pynvml
from dataclasses import dataclass
from .errors import InvalidInputError

@dataclass
class GPUProcess:
    pid: int
    gpu_memory_used: int
    cgoup: str

def _cgoup_from_pid(pid: int) -> str:
    with open(f"/proc/{pid}/cgroup") as f:
        return f.read().split("\n")[0]

def list_processes_on_gpus(gpu_ids: list[int]) -> dict[int, list[GPUProcess]]:
    """
    Query the process running on the specified GPUs.
    return a dictionary with GPU ID as key and a list of process IDs as value.
    """
    pynvml.nvmlInit()
    processes = {}
    for gpu_id in gpu_ids:
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(gpu_id)
        except pynvml.NVMLError as e:
            if "invalid argument" in str(e).lower():
                raise InvalidInputError(f"GPU ID {gpu_id} is invalid")
            raise e
        info = pynvml.nvmlDeviceGetComputeRunningProcesses(handle)
        processes[gpu_id] = [
            GPUProcess(
                pid=proc.pid,
                gpu_memory_used=proc.usedGpuMemory,
                cgoup=_cgoup_from_pid(proc.pid)
            ) for proc in info
        ]
    pynvml.nvmlShutdown()
    return processes

if __name__ == "__main__":
    print(_cgoup_from_pid(1))
    print(list_processes_on_gpus([0, 1]))