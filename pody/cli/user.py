import typer
import rich
from typing import Optional
from pody.eng.user import UserDatabase, QuotaDatabase
from ..eng.utils import parse_storage_size
from ..eng.docker import ContainerAction, DockerController

app = typer.Typer(
    help = "Manage users in the system",
    no_args_is_help=True
    )

@app.command()
def add(
    username: str,
    password: str,
    admin: bool = False,
    ):
    db = UserDatabase()
    db.add_user(username, password, admin)

@app.command()
def update(
    username: str, 
    password: Optional[str] = None,
    admin: Optional[bool] = None,
    ):
    UserDatabase().update_user(username, password=password, is_admin=admin)

@app.command(help="List users, optionally filter by username")
def list(usernames: Optional[list[str]] = typer.Argument(None)):
    console = rich.console.Console()
    users = UserDatabase().list_users(usernames)
    qdb = QuotaDatabase()
    for idx, user in enumerate(users):
        console.print(f"{idx+1}. {user} {qdb.check_quota(user.name, use_fallback=False)}")

@app.command()
def update_quota(
    username: str, 
    max_pods: Optional[int] = None,
    gpu_count: Optional[int] = None,
    memory_limit: Optional[str] = None, 
    storage_size: Optional[str] = None, 
    shm_size: Optional[str] = None
    ):
    QuotaDatabase().update_quota(
        username, max_pods=max_pods, gpu_count=gpu_count, 
        memory_limit=parse_storage_size(memory_limit) if not memory_limit is None else None, 
        storage_size=parse_storage_size(storage_size) if not storage_size is None else None, 
        shm_size=parse_storage_size(shm_size) if not shm_size is None else None
        )

@app.command(help="Delete user")
def delete(username: str):
    UserDatabase().delete_user(username)
    QuotaDatabase().delete_quota(username)

@app.command(help="Delete user and all related containers")
def purge(
    username: str, 
    yes: bool= typer.Option(False, "--yes", "-y", help="Skip confirmation")
    ):
    if not yes:
        typer.confirm(f"Are you sure to purge user {username}?", abort=True)
    c = DockerController()
    UserDatabase().delete_user(username)
    QuotaDatabase().delete_quota(username)
    containers = c.list_docker_containers(filter_name=username + "-")
    for container in containers:
        c.container_action(container, ContainerAction.DELETE)
        print(f"Container [{container}] removed")