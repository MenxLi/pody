"""
Name parse for containers. 
This module provides functions to validate and manipulate container/image names.
"""
from __future__ import annotations
from typing import TypedDict, Optional, overload, Literal, TYPE_CHECKING

from .errors import *
from ..config import config, Config

if TYPE_CHECKING:
    from .user import UserRecord

def check_name_part(part: str, reserved_kw: list[str] = []) -> tuple[bool, str]:
    """
    Check if the name part is valid.
    Return a tuple of (valid: bool, reason: str)
    """
    if not 1 <= len(part) <= 20:
        return False, "Name part must be between 1 and 20 characters"
    if part in reserved_kw:
        return False, f"Name part '{part}' is reserved"
    if not part.isidentifier():
        return False, "Name part must be an identifier"
    if '-' in part or ':' in part:
        return False, "Name part cannot contain '-' or ':'"
    if part.startswith('_') or part.endswith('_'):
        return False, "Name part cannot start or end with '_'"
    return True, ""

class InsNameComponentX(TypedDict):
    prefix: Optional[str]
    username: Optional[str]
    instance: str
class InsNameComponentU(TypedDict):
    prefix: Optional[str]
    username: str
    instance: str
@overload
def split_name_component(ins_name: str, check: Literal[True] = True) -> Optional[InsNameComponentU]: ...
@overload
def split_name_component(ins_name: str, check: Literal[False]) -> Optional[InsNameComponentX]: ...
def split_name_component(ins_name: str, check:bool = True) -> Optional[InsNameComponentX|InsNameComponentU]:
    """
    Split the instance name into prefix, username and instance name, 
    - check: if True, the name should be:
        - 3 parts: prefix-username-instance, if prefix is set
        - 2 parts: username-instance, if prefix is not set
        This does not guarantee the validity of the username and instance name
    return None if the name is invalid
    """
    if not '-' in ins_name:
        if check:
            return None
        return {
            "prefix": None,
            "username": None,
            "instance": ins_name
        }
    ins_name_sp = ins_name.split('-')
    if len(ins_name_sp) == 2:
        if check and config().name_prefix:
            return None
        return {
            "prefix": None,
            "username": ins_name_sp[0],
            "instance": ins_name_sp[1]
        }
    if len(ins_name_sp) == 3:
        if check:
            if config().name_prefix and not ins_name_sp[0] == config().name_prefix:
                return None
            elif not config().name_prefix:
                return None
        return {
            "prefix": ins_name_sp[0],
            "username": ins_name_sp[1],
            "instance": ins_name_sp[2]
        }
    return None
    

def eval_name_raise(ins: str, user: UserRecord) -> str:
    """ 
    takes a instance name and return the full container name, 
    raise error if the name is invalid or the user does not have permission 
    """
    conf = config()
    res = split_name_component(ins, check=False)

    def fmt_name(username:str, instance:str):
        return f"{username}-{instance}" if not conf.name_prefix else f"{conf.name_prefix}-{username}-{instance}"

    if res is None:
        raise InvalidInputError(f"Invalid pod name: {ins}")
    if res["prefix"] is not None and not res["prefix"] == conf.name_prefix:
        raise InsufficientPermissionsError("Invalid pod name, please check prefix")
    if not user.is_admin:
        if res["username"] is not None and not res["username"] == user.name:
            raise InsufficientPermissionsError("Invalid pod name, please check the username")
        return fmt_name(user.name, res["instance"])

    else:
        # admin can query any user's container
        if res["username"] is None:
            return fmt_name(user.name, res["instance"])
        if res['prefix'] and not res['prefix'] == conf.name_prefix:
            raise InvalidInputError("Invalid pod name, please check prefix")
        return fmt_name(res["username"], res["instance"])

def get_user_pod_prefix(username: str):
    ins_prefix = config().name_prefix
    return f"{ins_prefix}-{username}-" if ins_prefix else f"{username}-"


class ImageFilter:
    def __init__(self, config: Config, raw_images: list[str], username: Optional[str] = None):
        self.raw_images = raw_images
        self.config = config
        self.image_configs = config.images
        self.username = username

    def query_config(self, q_image: str, allow_user_image = True) -> Optional[Config.ImageConfig]:
        """ Return the image config if the config name matches the query and the image is available """
        if not q_image in self.raw_images:
            return None
        
        for im_c in self.image_configs:
            if im_c.name == q_image or (not ':' in im_c.name and q_image.startswith(im_c.name + ':')):
                return im_c

        if allow_user_image and self.has_user_image(q_image):
            return Config.ImageConfig(
                name=q_image,
                ports=self.config.commit_image_ports,
            )

        return None
    
    def has_user_image(self, q_image: str) -> bool:
        return self.username and q_image in self.raw_images and \
            q_image == f"{self.config.commit_name}:{self.username}" or \
            q_image.startswith(f"{self.config.commit_name}:{self.username}-")

    def iter(self):
        """ 
        Iterate over valid image names, 
        filtering out those not in the config or not user images 
        """
        for image in self.raw_images:
            if self.query_config(image, allow_user_image=True):
                yield image

class ImageNameTran:
    def __init__(self, user_commit_name: str):
        self.prefix = user_commit_name

    def abbreviate_if_user_commit(self, image_full: str) -> str:
        """
        Abbreviate the image name if it is a user commit image.
        May raise an error if the image does not contain a tag.
        """
        assert ":" in image_full, "Image name must contain a tag"
        if image_full.startswith(self.prefix + ":"):
            return image_full[len(self.prefix) + 1:]
        return image_full

    def expand_if_user_commit(self, image_abbr: str) -> str:
        """ Expand the image name if it is a user commit image.  """
        if ":" in image_abbr: return image_abbr
        return f"{self.prefix}:{image_abbr}"