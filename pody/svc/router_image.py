from .app_base import *

from fastapi import Depends
from fastapi.routing import APIRouter

from ..eng.errors import *
from ..eng.user import UserRecord
from ..eng.docker import DockerController
from ..eng.nparse import ImageFilter
from ..config import config

router_image = APIRouter(prefix="/image")

@router_image.get("/list")
@handle_exception
def list_images(user: UserRecord = Depends(require_permission("all"))):
    return ImageFilter(
        config = config(), 
        raw_images=DockerController().list_docker_images(), 
        username = user.name
        ).list()

@router_image.post("/delete")
@handle_exception
def delete_image(image: str, user: UserRecord = Depends(require_permission("all"))):
    c = DockerController()
    im_list = c.list_docker_images()
    if not image in im_list:
        raise InvalidInputError("Image not found, please check the available images")

    im_filter = ImageFilter(
        config = config(), 
        raw_images = im_list,
        username=user.name
    )
    if not im_filter.is_user_image(image):
        raise PermissionError("Can only delete user commit images")
    
    c.delete_docker_image(image)
    return {"log": "Image {} deleted".format(image)}