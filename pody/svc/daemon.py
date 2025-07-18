import time
import typing 
import docker
import multiprocessing as mp
from contextlib import contextmanager
from ..eng.user import UserDatabase, QuotaDatabase
from ..eng.gpu import GPUHandler
from ..eng.docker import DockerController
from ..eng.resmon import ProcessIter, ContainerProcessInfo, ResourceMonitorDatabase
from ..eng.log import get_logger
from ..eng.nparse import split_name_component

def leave_info(container_name, info: str, level: str = "info"):
    assert "'" not in info, "Single quote is not allowed in info"
    curr_time_str = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
    logdir = "/log/pody"
    fname = f"{curr_time_str}.{level}.log"
    DockerController().exec_container_bash(container_name, f"mkdir -p {logdir} && echo '{info}' > {logdir}/{fname}")

def task_check_gpu_usage():
    logger = get_logger('daemon')
    client = docker.from_env()
    user_db = UserDatabase()
    quota_db = QuotaDatabase()

    user_proc_count: dict[str, int] = {}
    user_procs: dict[str, list[ContainerProcessInfo]] = {}

    def is_user_process(p: ContainerProcessInfo):
        name_sp = split_name_component(p.container_name, check=True)
        username = name_sp['username'] if name_sp else ""
        user = user_db.get_user(username)
        return ProcessIter.FilterReturn(
            is_valid=name_sp is not None and user.userid != 0,
            extra=user
        )
    mon = ProcessIter(filter_fn=is_user_process)

    for i in range(GPUHandler().device_count()):
        this_gpu_users = set()
        for p, user in mon.gpu_process([i]):
            pod_name: str = p.container_name
            username = user.name
            this_gpu_users.add(username)
            user_procs[username] = user_procs.get(username, []) + [p]
        for user in this_gpu_users:
            user_proc_count[user] = user_proc_count.get(user, 0) + 1
    
    for username, proc_count in user_proc_count.items():
        max_gpu_count = quota_db.check_quota(username, use_fallback=True).gpu_count
        if max_gpu_count >= 0 and proc_count > max_gpu_count:
            # kill container from this user (the one with the shortest uptime)
            # not process because we may not have permission to kill process...
            user_procs[username].sort(key=lambda x: x.cproc.uptime)
            proc_info = user_procs[username][0]
            pod_name = proc_info.container_name
            pid = int(proc_info.cproc.pid)
            cmd = proc_info.cproc.cmd
            leave_info(pod_name, f"Killed container with pid-{pid} ({cmd}) due to GPU quota exceeded.", "critical")
            client.containers.get(pod_name).stop()
            logger.info(f"Killed container {pod_name} with pid-{pid} ({cmd}) due to GPU quota exceeded.")

def task_record_resource_usage():
    """
    Record resource usage of all containers.
    This is a daemon task that runs periodically.
    """
    logger = get_logger('daemon')
    mon = ProcessIter()
    resmon_db = ResourceMonitorDatabase()
    
    try:
        resmon_db.update(map(lambda it: it[0], mon.all_process()))
        resmon_db.update(map(lambda it: it[0], mon.gpu_process()))
    except Exception as e:
        logger.error(f"Error recording resource usage: {e}")

def create_daemon_worker(fn: typing.Callable, interval, delay=0, args = (), kwargs = {}):
    def daemon_worker():
        time.sleep(delay)
        while True:
            try:
                fn(*args, **kwargs)
                get_logger('daemon.exec').debug(f"Daemon worker [{fn.__name__}] executed")
            except Exception as e:
                if isinstance(e, KeyboardInterrupt): raise
                get_logger('daemon.err').exception(f"Error in daemon worker [{fn.__name__}]: {e}")
            time.sleep(interval)
    return mp.Process(target=daemon_worker)

@contextmanager
def daemon_context():
    ps = [
        create_daemon_worker(task_check_gpu_usage, 60),
        create_daemon_worker(task_record_resource_usage, 60, delay=5)
    ]
    for p in ps: p.start()
    try:
        yield
    finally:
        for p in ps: p.terminate()
        for p in ps: p.join()