"""
Resource monitoring utilities (High-level docker and GPU process monitoring)
"""
import psutil, time, sqlite3, time
from typing import Iterator, Callable, Optional, Generic, TypeVar
import dataclasses
from ..config import DATA_HOME
from .user import UserDatabase
from .db import DatabaseAbstract
from .log import get_logger
from .gpu import GPUHandler, list_processes_on_gpus, GPUProcessInfo
from .docker import DockerController
from .errors import ProcessUnavailableError
from .nparse import split_name_component

@dataclasses.dataclass
class ProcessInfo:
    pid: int
    cmd: str
    cgroup: str
    uptime: float
    cputime: float      # CPU time in seconds
    memory_used: int    # in bytes

    def json(self):
        return dataclasses.asdict(self)

# https://man7.org/linux/man-pages/man5/proc_pid_stat.5.html
def query_process(pid: int) -> ProcessInfo:
    def _cgroup_from_pid(pid: int) -> str:
        with open(f"/proc/{pid}/cgroup") as f:
            return f.read()
    
    try:
        proc = psutil.Process(pid)
    except psutil.ZombieProcess as e:
        raise ProcessUnavailableError(f"Process {pid} is a zombie") from e
    except psutil.NoSuchProcess as e:
        raise ProcessUnavailableError(f"Process {pid} not found") from e
    
    cputimes = proc.cpu_times()
    return ProcessInfo(
        pid=pid,
        cmd=" ".join(proc.cmdline()),
        cgroup=_cgroup_from_pid(pid),
        uptime=time.time() - proc.create_time(),
        cputime=cputimes.user + cputimes.system, 
        memory_used=proc.memory_info().rss, 
    )

@dataclasses.dataclass
class ContainerProcessInfo:
    container_name: str
    cproc: ProcessInfo
    gproc: Optional[GPUProcessInfo] = None

    def json(self):
        return {
            "container_name": self.container_name,
            "cproc": self.cproc.json(),
            "gproc": self.gproc.json() if self.gproc else None,
        }

T = TypeVar('T')
V = TypeVar('V')
class ProcessIter(Generic[T]):

    @dataclasses.dataclass
    class FilterReturn(Generic[V]):
        is_valid: bool
        extra: Optional[V] = None
    
    ContainerProcessInfo = ContainerProcessInfo

    def __init__(self, 
        filter_fn: Callable[[ContainerProcessInfo], FilterReturn[T]] \
            = lambda _: ProcessIter.FilterReturn(is_valid=True), 
        docker_only: bool = True
        ):
        self.logger = get_logger("resmon")
        self.filter_fn = filter_fn
        self.docker_only = docker_only
        self.docker_con = DockerController()
        self.gpu_handler = GPUHandler()
    
    def all_process(self) -> Iterator[tuple[ContainerProcessInfo, T]]:
        for proc in psutil.process_iter(['pid']):
            try:
                pid = proc.info['pid']
                if not (name:=self.docker_con.container_from_pid(pid)):
                    if self.docker_only: continue
                    else: name = ""
                p = ContainerProcessInfo(
                    container_name = name,
                    cproc = query_process(pid),
                    gproc = None
                )
                filter_r = self.filter_fn(p)
                if filter_r.is_valid:
                    yield p, filter_r.extra     # type: ignore
            except ProcessUnavailableError as e:
                self.logger.warning(f"Process {pid} unavailable: {e}")
                continue
            except Exception as e:
                self.logger.error(f"Error querying process {pid} [{type(e)}]: {e}")
                continue
    
    def gpu_process(self, gpu_ids: Optional[list[int]] = None) -> Iterator[tuple[ContainerProcessInfo, T]]:
        if gpu_ids is None:
            gpu_ids = list(range(self.gpu_handler.device_count()))

        gpu_procs = list_processes_on_gpus(gpu_ids)
        for _, procs in gpu_procs.items():
            for proc in procs:
                try:
                    pid = proc.pid
                    if not (name := self.docker_con.container_from_pid(pid)):
                        if self.docker_only: continue
                        else: name = ""
                    cproc = query_process(pid)
                    p = ContainerProcessInfo(
                        container_name=name,
                        cproc=cproc,
                        gproc=proc
                    )
                    r = self.filter_fn(p)
                    if r.is_valid:
                        yield p, r.extra    # type: ignore
                except ProcessUnavailableError as e:
                    self.logger.warning(f"Process {pid} unavailable: {e}")
                    continue
                except Exception as e:
                    self.logger.error(f"Error querying process {pid} [{type(e)}]: {e}")
                    continue


class ResourceMonitorDatabase(DatabaseAbstract):
    def __init__(self, in_memory: bool = False):
        self.user_db = UserDatabase()
        self.logger = get_logger("resmon")
        self.boot_id = str(psutil.boot_time())
        db_path = ":memory:" if in_memory else f"{DATA_HOME}/resmon.db"
        self._conn = sqlite3.connect(db_path)

        with self.transaction() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS resource_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    boot_id TEXT NOT NULL,
                    pid INTEGER NOT NULL,
                    start_time REAL NOT NULL,
                    username TEXT NOT NULL,
                    container_id TEXT NOT NULL,
                    cmd TEXT NOT NULL,
                    uptime REAL NOT NULL,
                    cputime REAL NOT NULL,
                    ngpus INTEGER NOT NULL
                )
            """)

    @property
    def conn(self) -> sqlite3.Connection:
        return self._conn
    
    def update(self, pinfo_iter: Iterator[ContainerProcessInfo]):

        with self.transaction() as cur:
            proc_gpu_count: dict[int, int] = {}
            for pinfo in pinfo_iter:
                name_sp = split_name_component(pinfo.container_name, check=True)
                if not name_sp:
                    # not a user process, skip
                    continue

                username = name_sp['username']
                user = self.user_db.get_user(username)
                if user.userid == 0:  
                    # user not found, skip
                    continue

                pid = pinfo.cproc.pid
                if pinfo.gproc:
                    proc_gpu_count[pid] = proc_gpu_count.get(pid, 0) + 1
                
                ngpus = proc_gpu_count.get(pid, 0)

                # remove old records for this process
                cur.execute("""
                    DELETE FROM resource_usage
                    WHERE boot_id = ? AND pid = ?
                """, (self.boot_id, pid))

                now_time = time.time()
                start_time = now_time - pinfo.cproc.uptime
                cur.execute("""
                    INSERT INTO resource_usage (boot_id, pid, start_time,
                    username, container_id, cmd, uptime, cputime, ngpus)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.boot_id,
                    pid,
                    start_time, 
                    username,
                    pinfo.container_name,
                    pinfo.cproc.cmd,
                    pinfo.cproc.uptime,
                    pinfo.cproc.cputime,
                    ngpus
                ))
    
    def query_cputime(self, *username: str, after: float = 0) -> dict[str, float]:
        if not username:
            username = [user.name for user in self.user_db.list_users() if user.userid != 0] # type: ignore
        with self.cursor() as cur:
            cur.execute("""
                SELECT username, SUM(cputime) FROM resource_usage
                WHERE start_time > ? AND cputime > 1 AND username IN ({})
                GROUP BY username
            """.format(','.join('?' for _ in username)), (after, *username))
            result = cur.fetchall()
            return {row[0]: row[1] for row in result}
    
    def query_gputime(self, *username: str, after: float = 0) -> dict[str, float]:
        if not username:
            username = [user.name for user in self.user_db.list_users() if user.userid != 0] # type: ignore
        with self.cursor() as cur:
            cur.execute("""
                SELECT username, SUM(ngpus * uptime) FROM resource_usage
                WHERE start_time > ? AND ngpus > 0 AND username IN ({})
                GROUP BY username
            """.format(','.join('?' for _ in username)), (after, *username))
            result = cur.fetchall()
            return {row[0]: row[1] for row in result}


if __name__ == "__main__":
    piter = ProcessIter()
    for proc, extra in piter.all_process():
        print(proc.json())

    resmon_db = ResourceMonitorDatabase(in_memory=True)
    resmon_db.update(map(lambda it: it[0], piter.all_process()))
    resmon_db.update(map(lambda it: it[0], piter.gpu_process()))
    print(resmon_db.query_cputime())
    print(resmon_db.query_gputime())