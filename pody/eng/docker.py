import docker
import docker.types
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from docker.models.containers import _RestartPolicy

from .errors import ContainerNotFoundError

@dataclass
class ContainerConfig:
    image_name: str
    container_name: str
    volumes: list[str]          # e.g. ["/host/path:/container/path"]
    port_mapping: list[str]     # e.g. ["8000:8000", "8888:8888"]
    gpu_ids: Optional[list[int]]
    memory_limit: str           # e.g. "8g"

    # default values
    restart_policy: Optional["_RestartPolicy"] = field(default_factory=lambda: {"Name": "always", "MaximumRetryCount": 0})
    tty = True
    auto_remove = False
    detach = True
    entrypoint: Optional[str | list[str]] = None

def create_container(
    client: docker.client.DockerClient,
    config: ContainerConfig
    ):
    if not config.gpu_ids is None:
        gpus = [
            docker.types.DeviceRequest(
                capabilities=[["compute", "utility", "graphics"]], 
                driver="nvidia", 
                device_ids=[f"{gpu_id}" for gpu_id in config.gpu_ids]
            )
        ]
    else:
        # all gpus
        gpus = [
            docker.types.DeviceRequest(
                capabilities=[["compute", "utility", "graphics"]], 
                driver="nvidia", 
                count=-1
            )
        ]
    # https://docker-py.readthedocs.io/en/stable/containers.html
    container = client.containers.run(
        image=config.image_name,
        name=config.container_name,
        volumes={vol.split(":")[0]: {"bind": vol.split(":")[1], "mode": "rw"} for vol in config.volumes},
        ports={port.split(":")[1]: port.split(":")[0] for port in config.port_mapping},     # type: ignore
        device_requests=gpus,
        mem_limit=config.memory_limit,
        memswap_limit=config.memory_limit,      # disable swap
        tty=config.tty, 
        detach=config.detach,                   # type: ignore
        restart_policy=config.restart_policy, 
        auto_remove=config.auto_remove, 
        entrypoint=config.entrypoint

    )   # type: ignore
    return container.logs()

def restart_container(
    client: docker.client.DockerClient,
    container_name: str, 
    execute_before_restart: Optional[str] = None, 
    execute_after_restart: Optional[str] = None
    ):
    container = client.containers.get(container_name)
    if not execute_before_restart is None:
        container.exec_run(execute_before_restart, tty=True)
    container.restart()
    if not execute_after_restart is None:
        container.exec_run(execute_after_restart, tty=True)
    return container.logs()

def query_container_by_id(
    client: docker.client.DockerClient,
    container_id: str
    ):
    container = client.containers.get(container_id)
    if container is None: raise ContainerNotFoundError(f"Container {container_id} not found")
    return {
        "name": container.name,
        "status": container.status,
        "ports": container.ports,
    }

if __name__ == "__main__":
    client = docker.from_env()
    config = ContainerConfig(
        image_name="ubuntu2204-cu121-base",
        container_name="utest",
        volumes=["/data/test-user:/data/test-user"],
        port_mapping=["15999:22", "15998:23"],
        gpu_ids=[1,2],
        memory_limit="8g", 
    )
    config.auto_remove = True
    config.restart_policy = None
    print(create_container(client, config))