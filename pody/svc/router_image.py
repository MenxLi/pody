from .app_base import *

from fastapi import Depends
from fastapi.routing import APIRouter

from ..eng.user import UserRecord
from ..eng.docker import DockerController
from ..eng.nparse import ImageFilter
from ..config import config

router_image = APIRouter(prefix="/image")

@router_image.get("/list")
@handle_exception
def list_images(_: UserRecord = Depends(require_permission("all"))):
    return list(ImageFilter(
        config = config(), 
        raw_images=DockerController().list_docker_images()
        ))