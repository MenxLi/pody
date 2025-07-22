from .app_base import *

from fastapi import Depends
from fastapi.routing import APIRouter

from ..eng.errors import *
from ..eng.user import UserRecord
from ..eng.docker import DockerController
from ..eng.nparse import ImageFilter, ImageNameTran
from ..config import config

router_image = APIRouter(prefix="/image")

@router_image.get("/list")
@handle_exception
def list_images(user: UserRecord = Depends(require_permission("all"))):
    tran = ImageNameTran(config().commit_name)
    it =map(
            tran.abbreviate_if_user_commit,
            ImageFilter(
                config = config(), 
                raw_images=DockerController().list_docker_images(), 
                username = user.name
            ).iter()
        )
    return list(it)

@router_image.post("/delete")
@handle_exception
def delete_image(image: str, user: UserRecord = Depends(require_permission("all"))):
    image = ImageNameTran(config().commit_name)\
            .expand_if_user_commit(image)
    c = DockerController()
    im_list = c.list_docker_images()
    if not image in im_list:
        raise InvalidInputError("Image not found, please check the available images")

    im_filter = ImageFilter(
        config = config(), 
        raw_images = im_list,
        username=user.name
    )
    if not im_filter.has_user_image(image):
        raise PermissionError("Can only delete user commit images")
    
    c.delete_docker_image(image)
    return {"log": "Image {} deleted".format(image)}

@router_image.post("/inspect")
@handle_exception
def inspect_image(image: str, user: UserRecord = Depends(require_permission("all"))):
    image = ImageNameTran(config().commit_name)\
            .expand_if_user_commit(image)
    c = DockerController()
    im_list = c.list_docker_images()
    if not image in im_list:
        raise InvalidInputError("Image not found, please check the available images")

    im_filter = ImageFilter(
        config = config(), 
        raw_images = im_list,
        username=user.name
    )
    if im_filter.query_config(image) or im_filter.has_user_image(image):
        return c.inspect_docker_image(image)
    else:
        raise PermissionError("Invalid image name, please check the available images")
    