from typing import Optional
import pynvml
from dataclasses import dataclass
from .errors import InvalidInputError

@dataclass
class GPUProcess:
    pid: int
    gpu_memory_used: int

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
            ) for proc in info
        ]
    pynvml.nvmlShutdown()
    return processes

@dataclass()
class GPUDevice:
    idx: int
    uid: str
    temperature: float
    memory_used: int
    memory_total: int
    power_usage: float
    power_limit: float
    util: float

    def memory_util(self) -> float:
        return self.memory_used / self.memory_total
    
    def power_util(self) -> float:
        return self.power_usage / self.power_limit

class GPUHandler:
    def __init__(self):
        pynvml.nvmlInit()
    
    def __del__(self):
        pynvml.nvmlShutdown()
    
    def device_count(self) -> int:
        return pynvml.nvmlDeviceGetCount()
    
    def all_devices(self) -> list[GPUDevice]:
        return [gpu_device for i in range(self.device_count()) if (gpu_device := self.query_device(i)) is not None]
    
    def query_device(self, idx: int) -> Optional[GPUDevice]:
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(idx)
            info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            power = pynvml.nvmlDeviceGetPowerUsage(handle)
            limit = pynvml.nvmlDeviceGetPowerManagementLimit(handle)
            temperature = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            return GPUDevice(
                idx=idx,
                uid=pynvml.nvmlDeviceGetUUID(handle),
                memory_used=info.used,      # type: ignore
                memory_total=info.total,    # type: ignore
                power_usage=power / 1000,
                power_limit=limit / 1000,
                temperature=temperature, 
                util=util.gpu               # type: ignore
            )
        except pynvml.NVMLError:
            return None

if __name__ == "__main__":
    print(list_processes_on_gpus([0, 1]))