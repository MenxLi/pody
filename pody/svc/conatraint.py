from pody.config import config
from pody.eng.user import UserRecord
from pody.eng.errors import *
from typing import TypedDict, Optional, overload, Literal

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
    

def eval_name_raise(ins: str, user: UserRecord):
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
