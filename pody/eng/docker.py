import docker
import docker.errors
import docker.models
import docker.models.images
import docker.types
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from docker.models.containers import _RestartPolicy

import time
from multiprocessing import Process, Queue
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

@dataclass
class ContainerInfo:
    name: str
    status: str
    image: str
    port_mapping: list[str]     # e.g. ["8000:8000", "8888:8888"]
    gpu_ids: Optional[list[int]]
    memory_limit: int

def _get_image_name(image: docker.models.images.Image):
    image_name = image.tags[0] if image and image.tags else image.short_id if image.short_id else ""
    return image_name

def create_container(
    client: docker.client.DockerClient,
    config: ContainerConfig
    ) -> str:
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
        volumes={vol.split(":")[0]: {"bind": vol.split(":")[1], "mode": vol.split(":")[2] if len(vol) > 2 else 'ro'} for vol in config.volumes},
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
    return container.logs().decode()

class ContainerAction(Enum):
    START = "start"
    STOP = "stop"
    RESTART = "restart"
    KILL = "kill"
    DELETE = "delete"
    
def container_action(
    client: docker.client.DockerClient,
    container_name: str,
    action: ContainerAction,
    before_action: Optional[str] = None,
    after_action: Optional[str] = None
    ) -> str:
    container = client.containers.get(container_name)
    if not before_action is None:
        container.exec_run(before_action, tty=True)
    match action:
        case ContainerAction.START: container.start()
        case ContainerAction.STOP: container.stop()
        case ContainerAction.RESTART: container.restart()
        case ContainerAction.KILL: container.kill()
        case ContainerAction.DELETE: 
            container.remove(force=True)
            return f"Container {container_name} deleted"
        case _: raise ValueError(f"Invalid action {action}")
    if not after_action is None:
        container.exec_run(after_action, tty=True)
    return container.logs().decode()

def inspect_container(client: docker.client.DockerClient, container_id: str) -> ContainerInfo:
    container = client.containers.get(container_id)
    raw_gpu_ids = container.attrs.get('HostConfig', {}).get('DeviceRequests')
    dev_ids = raw_gpu_ids[0].get('DeviceIDs')
    if dev_ids is None:
        gpu_ids = None
    else:
        gpu_ids = [int(id) for id in raw_gpu_ids[0].get('DeviceIDs')] if raw_gpu_ids is not None and len(raw_gpu_ids) > 0 else []
    
    port_mappings_dict = {}
    port_dict = container.attrs['NetworkSettings']['Ports']
    for host_port, container_ports in port_dict.items():
        if container_ports:
            for port in container_ports:
                port_mappings_dict[port['HostPort']] = host_port.split('/')[0]

    container_info = ContainerInfo(
        name=container.name if container.name else container.id if container.id else "unknown",
        status=container.status,
        image=_get_image_name(container.image) if container.image else "unknown",
        port_mapping=[f"{host_port}:{container_port}" for host_port, container_port in port_mappings_dict.items()],
        gpu_ids=gpu_ids, 
        memory_limit=container.attrs['HostConfig']['Memory'] if container.attrs['HostConfig']['Memory'] else -1
    )
    return container_info

def check_container(
    client: docker.client.DockerClient,
    container_id: str
    ):
    """ Check if the container exists and return the very basic information """
    container = client.containers.get(container_id)
    if container is None: raise ContainerNotFoundError(f"Container {container_id} not found")
    return {
        "name": container.name,
        "status": container.status,
    }

def list_docker_containers(
    client: docker.client.DockerClient,
    filter_name: str,
    all: bool = True
    ) -> list[str]:
    containers = client.containers.list(all=all, filters={"name": filter_name})
    return [container.name for container in containers]

def list_docker_images(client: docker.client.DockerClient):
    filters = None
    images = client.images.list(filters=filters)
    return [_get_image_name(image) for image in images]

def get_docker_used_ports(client: docker.client.DockerClient):
    containers = client.containers.list(all=True)
    used_ports = []
    for container in containers:
        port_dict = container.attrs['NetworkSettings']['Ports']
        for host_port, container_ports in port_dict.items():
            if container_ports:
                for port in container_ports:
                    used_ports.append(int(port['HostPort']))
    return used_ports

def _exec_container_bash_worker(container_name, command: str, q: Queue):
    client = docker.from_env()
    def escape_command(command: str):
        return command.replace('\\', '\\\\').replace('"', '\\"')
    cmd = f'/bin/bash -c "{escape_command(command)}"'
    try:
        container = client.containers.get(container_name)
        result = container.exec_run(cmd, tty=True)
    except docker.errors.APIError as e:
        q.put((-1, f"Docker API error: {e}"))
        return
    except Exception as e:
        q.put((-1, f"Error: {e}"))
        return
    q.put((
            result.exit_code,
            result.output.decode('utf-8') if result.output else ""
        ))

def exec_container_bash(
    container_name: str,
    command: str, 
    timeout: int = 10
    ) -> tuple[int, str]:
    client = docker.from_env()
    check_container(client, container_name)
    start_time = time.time()
    q = Queue()
    proc = Process(target=_exec_container_bash_worker, args=(container_name, command, q), daemon=True)
    proc.start()
    while proc.is_alive():
        time.sleep(0.01)
        if time.time() - start_time > timeout:
            proc.terminate()
            return -1, "Timeout"
    proc.join()
    return q.get()

if __name__ == "__main__":
    client = docker.from_env()
    config = ContainerConfig(
        image_name="exp:latest",
        container_name="limengxun-test1",
        volumes=[],
        port_mapping=[],
        gpu_ids=[0,1],
        memory_limit="8g", 
    )
    config.restart_policy = None
    create_container(client, config)

    try:
        out = exec_container_bash("limengxun-test", "echo 'hello' > /tmp/hello.txt && ls /tmp")
        print(out)
        out = exec_container_bash("limengxun-test", "cat /tmp/hello.txt")
        print(out)
        out = exec_container_bash("limengxun-test", "mkdir -p ~/.ssh && echo 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDZQ7' > ~/.ssh/authorized_keys")
        print(out)
        out = exec_container_bash("limengxun-test", "cat ~/.ssh/authorized_keys")
        print(out)

    finally:
        container_action(client, "limengxun-test1", ContainerAction.DELETE)