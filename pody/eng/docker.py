"""
References:
- https://docker-py.readthedocs.io/en/stable/containers.html
- https://docs.docker.com/engine/containers/resource_constraints/
"""

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

import time, os
from multiprocessing import Process, Queue
from .errors import *
from .log import get_logger
from .utils import parse_storage_size

@dataclass
class ContainerConfig:
    image_name: str
    container_name: str
    volumes: list[str]                      # e.g. ["/host/path:/container/path", "/host/path2:/container/path2:ro"]
    port_mapping: list[str]                 # e.g. ["8000:8000", "8888:8888"]

    # resource constraints
    # NOTE: `storage_limit` only works for certain storage driver:
    # - https://docs.docker.com/reference/cli/docker/container/run/#storage-opt
    # - https://docs.docker.com/reference/cli/dockerd/#daemon-storage-driver
    gpu_ids: Optional[list[int]] = None
    memory_limit: Optional[str] = None      # e.g. "8g"
    storage_size: Optional[str] = None      # e.g. "8g"
    shm_size: Optional[str] = None          # e.g. "8g"

    # other default settings
    network: str = ""                       # e.g. "pody-net", if empty, the default bridge network will be used
    restart_policy: Optional["_RestartPolicy"] = field(default_factory=lambda: {"Name": "always", "MaximumRetryCount": 0})
    tty = True
    auto_remove = False
    detach = True
    entrypoint: Optional[str | list[str]] = None

@dataclass
class ContainerInfo:
    container_id: Optional[str]
    name: str
    status: str
    image: str
    networks: list[str]
    port_mapping: list[str]     # e.g. ["8000:8000", "8888:8888"]
    gpu_ids: Optional[list[int]]
    memory_limit: int
    shm_size: int

class ContainerAction(Enum):
    START = "start"
    STOP = "stop"
    RESTART = "restart"
    KILL = "kill"
    DELETE = "delete"

@dataclass
class ContainerSize:
    total: int
    virtual: int

def _get_image_name(image: docker.models.images.Image):
    image_name = image.tags[0] if image and image.tags else image.short_id if image.short_id else ""
    return image_name


class DockerController():
    """
    This is a simple wrapper class for Docker SDK, 
    the only data members are:
    1. `client`: a docker.DockerClient object
    2. `logger`: a logging.Logger object
    """
    def __init__(self):
        self.client = docker.from_env(timeout = 600)
        self.logger = get_logger('engine')

    def create_container(self, config: ContainerConfig) -> str:
        def parse_mount(mount: str, create_source = True) -> docker.types.Mount:
            mount_sp = mount.split(":")
            if len(mount_sp) < 2:
                raise ValueError(f"Invalid volume mapping: {mount}")
            source = mount_sp[0]
            target = mount_sp[1]
            if len(mount_sp) == 3:
                read_only = mount_sp[2] == "ro"
            else:
                read_only = False
            if create_source and not os.path.exists(source):
                os.makedirs(source)
            return docker.types.Mount(target=target, source=source, type="bind", read_only=read_only)

        def parse_gpus(gpu_ids: Optional[list[int]]) -> list[docker.types.DeviceRequest]:
            if gpu_ids is None:
                # all gpus
                return [
                    docker.types.DeviceRequest(
                        capabilities=[["compute", "utility", "graphics"]], 
                        driver="nvidia", 
                        count=-1
                    )
                ]
            else:
                return [
                    docker.types.DeviceRequest(
                        capabilities=[["compute", "utility", "graphics"]], 
                        driver="nvidia", 
                        device_ids=[f"{gpu_id}" for gpu_id in gpu_ids]
                    )
                ]
        
        def parse_network(network: str) -> Optional[str]:
            if not network:
                return None
            try:
                self.client.networks.get(network)
                return network
            except docker.errors.NotFound:
                raise IncorrectConfigError(f"Network {network} not found.")
        
        # https://docker-py.readthedocs.io/en/stable/containers.html
        container = self.client.containers.run(
            image=config.image_name,
            name=config.container_name,
            mounts=[parse_mount(vol) for vol in config.volumes],
            ports={port.split(":")[1]: port.split(":")[0] for port in config.port_mapping},     # type: ignore
            device_requests=parse_gpus(config.gpu_ids),
            mem_limit=config.memory_limit,
            mem_swappiness=0,                       # disable swap
            memswap_limit=config.memory_limit,      # disable swap
            shm_size=config.shm_size,
            tty=config.tty, 
            detach=config.detach,                   # type: ignore
            network=parse_network(config.network),
            restart_policy=config.restart_policy, 
            auto_remove=config.auto_remove, 
            entrypoint=config.entrypoint, 
            storage_opt={"size": config.storage_size} if config.storage_size else None
        )   # type: ignore
        self.logger.info(f"Container {container.name} created")
        return container.logs().decode()
    
    def container_action(
        self, container_name: str,
        action: ContainerAction,
        before_action: Optional[str] = None,
        after_action: Optional[str] = None
        ) -> str:
        container = self.client.containers.get(container_name)
        if not before_action is None:
            container.exec_run(before_action, tty=True)
        match action:
            case ContainerAction.START: container.start()
            case ContainerAction.STOP: container.stop()
            case ContainerAction.RESTART: container.restart()
            case ContainerAction.KILL: container.kill()
            case ContainerAction.DELETE: 
                container.remove(force=True)
                self.logger.info(f"Container {container.name} deleted")
                return f"Container {container_name} deleted"
            case _: raise ValueError(f"Invalid action {action}")
        if not after_action is None:
            container.exec_run(after_action, tty=True)
        self.logger.info(f"Container {container.name} {action.value}")
        return container.logs().decode()
    
    def commit_container(
        self, container_name: str, image_name: str, tag: str, 
        author: Optional[str] = None, message: Optional[str] = None
        ) -> str:
        """Return The name of the committed image"""
        container = self.client.containers.get(container_name)
        image_name = f"{image_name}:{tag}"
        existing_images = self.client.images.list(name=image_name)
        if existing_images:
            raise DuplicateError(f"Image {image_name} already exists. Please use a different name or tag.")
        container.commit(
            repository=image_name, tag=tag, 
            author=author, message=message
            )
        self.logger.info(f"Container {container_name} committed to image {image_name}")
        return image_name

    def inspect_container(self, container_id: str) -> ContainerInfo:
        container = self.client.containers.get(container_id)
        raw_gpu_ids = container.attrs.get('HostConfig', {}).get('DeviceRequests')
        dev_ids = raw_gpu_ids[0].get('DeviceIDs')
        if dev_ids is None:
            gpu_ids = None
        else:
            gpu_ids = [int(id) for id in raw_gpu_ids[0].get('DeviceIDs')] if raw_gpu_ids is not None and len(raw_gpu_ids) > 0 else []
        
        network_settings = container.attrs.get('NetworkSettings', {})

        port_mappings_dict = {}
        for host_port, container_ports in network_settings.get('Ports', {}).items():
            if container_ports:
                for port in container_ports:
                    port_mappings_dict[port['HostPort']] = host_port.split('/')[0]
        
        networks = []
        for network_name, network_info in network_settings.get('Networks', {}).items():
            if network_info.get('NetworkID'):
                networks.append(network_name)

        container_info = ContainerInfo(
            container_id=container.id[:12] if container.id else None,
            name=container.name if container.name else container.id if container.id else "unknown",
            status=container.status,
            image=_get_image_name(container.image) if container.image else "unknown",
            port_mapping=[f"{host_port}:{container_port}" for host_port, container_port in port_mappings_dict.items()],
            gpu_ids=gpu_ids, 
            networks=networks,
            memory_limit=container.attrs['HostConfig']['Memory'] if container.attrs['HostConfig']['Memory'] else -1, 
            shm_size=container.attrs['HostConfig']['ShmSize'] if container.attrs['HostConfig']['ShmSize'] else -1, 
        )
        return container_info

    def inspect_container_size(self, container_id: str):
        import subprocess
        container = self.client.containers.get(container_id)
        cname = container.name
        cmd = r'docker ps -a --format="{{.Size}}" --size --filter=' + f'"name={cname}"'
        res = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE)
        res = res.stdout.decode().split()
        assert '(virtual' in res[1], "Error: cannot parse the size query result"
        total = res[0]
        virtual = res[2].replace('(virtual ', '').replace(')', '')
        def parse_size(size_str: str) -> int:
            """Parse size string like '1.2GB', '500MB', '2.5TB' into bytes."""
            size_str = size_str.strip().lower()
            if size_str[-1].isdigit():
                return int(size_str)
            if size_str[-1] == 'b' and size_str[-2].isdigit():
                return int(size_str[:-1])
            else:
                size_str = size_str[:-1]
                return parse_storage_size(size_str)
        return ContainerSize(parse_size(total), parse_size(virtual))

    def check_container(self, container_id: str):
        """ Check if the container exists and return the very basic information """
        try:
            container = self.client.containers.get(container_id)
        except docker.errors.NotFound:
            raise ContainerNotFoundError(f"Container {container_id} not found")
        if container is None: raise ContainerNotFoundError(f"Container {container_id} not found")
        return {
            "name": container.name,
            "status": container.status,
        }

    def list_docker_containers(self, filter_name: str, all: bool = True) -> list[str]:
        containers = self.client.containers.list(all=all, filters={"name": filter_name})
        return [container.name for container in containers]

    def list_docker_images(self):
        filters = None
        images = self.client.images.list(filters=filters)
        return [_get_image_name(image) for image in images]
    
    def inspect_docker_image(self, image_name: str) -> Optional[dict]:
        """
        Return the same as `docker inspect <image_name>`
        """
        try:
            image = self.client.images.get(image_name)
            return {
                "name": _get_image_name(image),
                "id": image.id,
                "tags": image.tags,
                "comment": image.attrs.get('Comment', 'N/A'),
                "size": image.attrs.get('Size', 'N/A'),
                "exposed_ports": image.attrs.get('Config', {}).get('ExposedPorts', 'N/A'),
                "created": image.attrs.get('Created', 'N/A'),
            }
        except docker.errors.NotFound:
            return None
    
    def delete_docker_image(self, image_name: str):
        """
        Delete a Docker image by name.
        # If the image is in use by any container, it will raise an error.
        """
        try:
            self.client.images.remove(image=image_name, force=True)
            self.logger.info(f"Image {image_name} deleted")
        except docker.errors.APIError as e:
            raise ValueError(f"Failed to delete image {image_name}: {e}")

    def get_docker_used_ports(self):
        containers = self.client.containers.list(all=True)
        used_ports = []
        for container in containers:
            port_dict = container.attrs['NetworkSettings']['Ports']
            for host_port, container_ports in port_dict.items():
                if container_ports:
                    for port in container_ports:
                        used_ports.append(int(port['HostPort']))
        return used_ports

    def exec_container_bash(self, container_name: str, command: str, timeout: int = 30) -> tuple[int, str]:
        self.check_container(container_name)
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

    def container_from_pid(self, host_pid: int) -> Optional[str]:
        """Return the container name if the process with given PID is running inside a Docker container, otherwise return None."""
        try:
            with open(f"/proc/{host_pid}/cgroup", "r") as f:
                cgroup_info = f.read()
        except FileNotFoundError:
            return None     # Not running inside Docker

        container_id = None
        for line in cgroup_info.splitlines():
            parts = line.split(':')
            if len(parts) == 3 and "docker" in parts[2]:
                # uses the format /docker/<container_id>
                container_id = parts[2].split('/')[-1]
                # some systems have a different format
                if container_id.startswith("docker-") and container_id.endswith(".scope"):
                    container_id = container_id[len("docker-"):-len(".scope")]
                break

        if not container_id:
            return None  # Not running inside Docker
        try:
            container = self.client.containers.get(container_id)
        except docker.errors.NotFound:
            return None
        return container.name


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

if __name__ == "__main__":
    # client = docker.from_env()
    controller = DockerController()
    config = ContainerConfig(
        image_name="exp:latest",
        container_name="limengxun-test1",
        volumes=[],
        port_mapping=[],
        gpu_ids=[0,1],
        memory_limit="8g", 
    )
    config.restart_policy = None
    controller.create_container(config)

    try:
        r = controller.inspect_container_size("limengxun-test1")
        print(r)
        r = controller.inspect_container("limengxun-test1")
        print(r)
        r = controller.inspect_container_size("limengxun-test1")
        print(r)
        

    finally:
        controller.container_action("limengxun-test1", ContainerAction.DELETE)