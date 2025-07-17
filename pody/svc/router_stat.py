from .app_base import *

from fastapi import Depends
from fastapi.routing import APIRouter

import time
from typing import Optional

from ..eng.errors import *
from ..eng.user import UserRecord
from ..eng.resmon import ResourceMonitorDatabase

router_stat = APIRouter(prefix="/stat")

def parse_time(time_str: str) -> Optional[float]:
    time_str = time_str.strip().lower()
    try:
        match time_str[-1]:
            case 'y':
                return float(time_str[:-1]) * 365 * 24 * 3600
            case 'w':
                return float(time_str[:-1]) * 7 * 24 * 3600
            case 'd':
                return float(time_str[:-1]) * 24 * 3600
            case 'h':
                return float(time_str[:-1]) * 3600
            case 's':
                return float(time_str[:-1])
            case _:
                return float(time_str)
    except ValueError:
        raise InvalidInputError(f"Invalid time format: {time_str}. Should be like 1y, 1w, 1d, 1h, 1s or a number of seconds.")
    
@router_stat.get("/cputime")
@handle_exception
def cputime(_: UserRecord = Depends(require_permission("all")), user: Optional[str] = None, t: Optional[str] = None):
    resmon_db = ResourceMonitorDatabase()

    ft = parse_time(t) if t else None
    if ft is not None:
        after = time.time() - ft
    else:
        after = 0

    if user is None:
        return resmon_db.query_cputime(after=after)
    else:
        return resmon_db.query_cputime(*user.split(","), after=after)

@router_stat.get("/gputime")
@handle_exception
def gputime(_: UserRecord = Depends(require_permission("all")), user: Optional[str] = None, t: Optional[str] = None):
    resmon_db = ResourceMonitorDatabase()

    ft = parse_time(t) if t else None
    if ft is not None:
        after = time.time() - ft
    else:
        after = 0

    if user is None:
        return resmon_db.query_gputime(after=after)
    else:
        return resmon_db.query_gputime(*user.split(","), after=after)