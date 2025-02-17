import time
import docker
import multiprocessing as mp
from ..eng.user import UserDatabase
from ..eng.gpu import GPUHandler
from ..eng.docker import exec_container_bash
from ..eng.log import get_logger
from .router_host import gpu_status_impl

def leave_info(container_name, info: str, level: str = "info"):
    assert "'" not in info, "Single quote is not allowed in info"
    curr_time_str = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
    logdir = "/log/pody"
    fname = f"{curr_time_str}.{level}.log"
    exec_container_bash(container_name, f"mkdir -p {logdir} && echo '{info}' > {logdir}/{fname}")

def task_check_gpu_usage():
    logger = get_logger('daemon')
    client = docker.from_env()
    user_db = UserDatabase()

    gpu_processes = gpu_status_impl(client, list(range(GPUHandler().device_count())))
    user_proc_count: dict[str, int] = {}
    user_procs: dict[str, list[dict[str, str]]] = {}
    for i, ps in gpu_processes.items():
        this_gpu_users = set()
        for p in ps:
            pod_name: str = p['pod']
            if not pod_name:    # skip host process
                continue
            username = pod_name.split('-')[0]
            this_gpu_users.add(username)
            user_procs[username] = user_procs.get(username, []) + [p]
        for user in this_gpu_users:
            user_proc_count[user] = user_proc_count.get(user, 0) + 1
    
    for username, proc_count in user_proc_count.items():
        user = user_db.get_user(username)
        if user.userid == 0:    # skip task not related to this database
            continue
        max_gpu_count = user_db.check_user_quota(username).gpu_count
        if max_gpu_count >= 0 and proc_count > max_gpu_count:
            # kill container from this user (the one with the shortest uptime)
            # not process because we may not have permission to kill process...
            user_procs[username].sort(key=lambda x: x['uptime'])
            p = user_procs[username][0]
            pod_name = p['pod']
            pid = int(p['pid'])
            cmd = p['cmd']
            leave_info(pod_name, f"Killed container with pid-{pid} ({cmd}) due to GPU quota exceeded.", "critical")
            client.containers.get(pod_name).stop()
            logger.info(f"Killed container {pod_name} with pid-{pid} ({cmd}) due to GPU quota exceeded.")

def daemon_worker():
    logger = get_logger('daemon')
    while True:
        try:
            task_check_gpu_usage()
        except Exception as e:
            if isinstance(e, KeyboardInterrupt): raise
            logger.exception("Daemon task failed: " + str(e))
        time.sleep(60)  # check every minute

def start_daemon() -> mp.Process:
    p = mp.Process(target=daemon_worker)
    p.start()
    return p