import random
from string import Template
from typing import Optional

from .app_base import *
import dataclasses
from fastapi import Depends
from fastapi.routing import APIRouter
from contextlib import suppress

from ..eng.nparse import eval_name_raise, get_user_pod_prefix

from ..config import config
from ..eng.errors import *
from ..eng.nparse import ImageFilter, check_name_part, ImageNameTran
from ..eng.utils import format_storage_size
from ..eng.user import UserRecord, QuotaDatabase
from ..eng.docker import ContainerAction, ContainerConfig, DockerController

router_pod = APIRouter(prefix="/pod")

@router_pod.post("/create")
@handle_exception
def create_pod(
    ins: str, image: str, 
    user: UserRecord = Depends(require_permission("all"))
    ):
    valid, reason = check_name_part(ins)
    if not valid:
        raise InvalidInputError(f"Invalid pod name: {reason}")

    image = ImageNameTran(config().commit_name)\
            .expand_if_user_commit(image)

    server_config = config()
    container_name = eval_name_raise(ins, user)

    c = DockerController()
    # first check if the container exists
    with suppress(ContainerNotFoundError):
        c.check_container(container_name)
        raise DuplicateError(f"Container {container_name} already exists")

    # check user quota
    user_quota = QuotaDatabase().check_quota(user.name, use_fallback=True)
    user_containers = c.list_docker_containers(get_user_pod_prefix(user.name))
    if user_quota.max_pods != -1 and user_quota.max_pods <= len(user_containers):
        raise PermissionError("Exceed max pod limit")

    # check image
    im_filter = ImageFilter(
        config = server_config, 
        raw_images=c.list_docker_images()
        )
    target_im_config = im_filter.query_config(image)
    if not target_im_config:
        raise InvalidInputError("Invalid image name, please check the available images")

    # hanlding port
    def to_individual_port(ports: list[int | tuple[int, int]]) -> list[int]:
        res = []
        for port in ports:
            if isinstance(port, tuple):
                res.extend(range(port[0], port[1]+1))
            else:
                res.append(port)
        return res

    used_port_list = c.get_docker_used_ports()
    available_port_list = list(set(to_individual_port(server_config.available_ports)) - set(used_port_list))

    target_ports = target_im_config.ports
    if len(target_ports) > len(available_port_list):
        raise PermissionError("No available port")
    
    random.shuffle(available_port_list)
    port_mapping = [f'{available_port_list[i]}:{target_ports[i]}' for i in range(len(target_ports))]

    # handling volume
    volume_mappings = [Template(mapping).substitute(username=user.name) for mapping in server_config.volume_mappings]

    def parse_gpuids(s: str) -> Optional[list[int]]:
        s = s.strip().lower()
        if s == '' or s == 'all': return None   # no limit, all gpus
        if s == 'none': return []               # no gpu
        return [int(i) for i in s.split(',') if i.isdigit()]
        
    # create container
    container_config = ContainerConfig(
        image_name=image,
        container_name=container_name,
        volumes=volume_mappings,
        port_mapping=port_mapping,
        network=server_config.network, 
        gpu_ids=parse_gpuids(user_quota.gpus),
        memory_limit=f'{user_quota.memory_limit}b' if user_quota.memory_limit > 0 else None,
        storage_size=f'{user_quota.storage_size}b' if user_quota.storage_size > 0 else None, 
        shm_size=f'{user_quota.shm_size}b' if user_quota.shm_size > 0 else None, 
    )
    log = c.create_container(container_config) 
    try: container_info = c.inspect_container(container_name)
    except Exception as e: container_info = None
    return {"log": log, "info": container_info}

@router_pod.post("/delete")
@handle_exception
def delete_pod(ins: str, user: UserRecord = Depends(require_permission("all"))):
    container_name = eval_name_raise(ins, user)
    c = DockerController()
    return {"log": c.container_action(container_name, ContainerAction.DELETE)}

@router_pod.post("/restart")
@handle_exception
def restart_pod(ins: str, user: UserRecord = Depends(require_permission("all"))):
    container_name = eval_name_raise(ins, user)
    c = DockerController()
    return {"log": c.container_action(container_name, ContainerAction.RESTART)}

@router_pod.post("/stop")
@handle_exception
def stop_pod(ins: str, user: UserRecord = Depends(require_permission("all"))):
    container_name = eval_name_raise(ins, user)
    c = DockerController()
    return {"log": c.container_action(container_name, ContainerAction.STOP)}

@router_pod.post("/start")
@handle_exception
def start_pod(ins: str, user: UserRecord = Depends(require_permission("all"))):
    container_name = eval_name_raise(ins, user)
    c = DockerController()
    return {"log": c.container_action(container_name, ContainerAction.START)}

@router_pod.post("/commit")
@handle_exception
def commit_pod(
    ins: str, 
    tag: Optional[str] = None, 
    msg: Optional[str] = None,
    user: UserRecord = Depends(require_permission("all"))
    ):
    container_name = eval_name_raise(ins, user)
    cfg = config()
    c = DockerController()

    if tag: 
        valid, reason = check_name_part(tag)
        if not valid: raise InvalidInputError(f"Invalid tag name: {reason}")

    # check commit quota
    user_quota = QuotaDatabase().check_quota(user.name, use_fallback=True)
    if user_quota.commit_count != -1:
        im_filter = ImageFilter(
            config = cfg, 
            raw_images=c.list_docker_images(),
            username=user.name
        )
        n_user_commits = sum(im_filter.has_user_image(im) for im in im_filter.iter())
        if n_user_commits >= user_quota.commit_count:
            raise PermissionError(f"Exceed user commit limit ({user_quota.commit_count}), please delete some images first")

    # check size
    container_size = c.inspect_container_size(container_name)
    if container_size.total > user_quota.commit_size_limit:
        raise PermissionError(
            f"Container size {format_storage_size(container_size.total)} "
            f"exceeds user commit size limit ({format_storage_size(user_quota.commit_size_limit)})")
    
    commit_image_name = cfg.commit_name
    commit_tag_name = f"{user.name}" + (f"-{tag}" if tag else "")
    im_name = c.commit_container(container_name, commit_image_name, commit_tag_name, message=msg)
    return {"image_name": im_name, "log": f"Container {container_name} committed to image: {im_name}"}

@router_pod.get("/inspect")
@handle_exception
def inspect_pod(ins: str, user: UserRecord = Depends(require_permission("all"))):
    container_name = eval_name_raise(ins, user)
    c = DockerController()
    ins_name = container_name.split('-')[-1]
    return {
        "instance": ins_name,
        **dataclasses.asdict(c.inspect_container(container_name))
    }

@router_pod.get("/list")
@handle_exception
def list_pod(user: UserRecord = Depends(require_permission("all"))):
    c = DockerController()
    return [x.split('-')[-1] for x in c.list_docker_containers(get_user_pod_prefix(user.name))]

@router_pod.post("/exec")
@handle_exception
def exec_pod(
    ins: str, cmd: str, timeout: Optional[int] = None,
    user: UserRecord = Depends(require_permission("all"))
    ):
    container_name = eval_name_raise(ins, user)
    c = DockerController()
    if timeout is None:
        timeout = 30
    exit_code, log = c.exec_container_bash(container_name, cmd, timeout=timeout)
    return {"exit_code": exit_code, "log": log}

@router_pod.get("/info")
@deprecated_route("Use /pod/inspect instead, will be removed in 0.4.0")
def info_pod_old(ins: str):
    ...

# ====== admin only ======
@router_pod.get("/listall")
@handle_exception
def listall_pod(_: UserRecord = Depends(require_permission("admin"))):
    c = DockerController()
    return c.list_docker_containers("")
