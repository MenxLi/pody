import typer
import rich.console
from typing import Optional

from pody.eng.quota import QuotaDatabase
from pody.eng.user import UserDatabase

from ..eng.utils import parse_storage_size


app = typer.Typer(
    help = "Manage user quotas in the system",
    no_args_is_help=True
    )


@app.command(no_args_is_help=True, help="Set user quota")
def update(
    username: str,
    max_pods: Optional[int] = None,
    gpu_count: Optional[int] = typer.Option(None, "--gpu-count", help="Number of GPUs that can be used simultaneously"),
    gpus: Optional[str] = typer.Option(None, "--gpus", help="GPU IDs visible to the user, comma separated, e.g. '0,1,2', or 'all' for all GPUs, or 'none' for no GPUs. NOTE: empty string means no limit (fallback to default)"),
    memory_limit: Optional[str] = None,
    storage_size: Optional[str] = None,
    shm_size: Optional[str] = None,
    tmpfs_size: Optional[str] = typer.Option(None, "--tmpfs-size", help="Size of tmpfs mounts, e.g. '1g', or 'none' for no tmpfs mounts"),
    commit_count: Optional[int] = None,
    commit_size_limit: Optional[str] = None,
    ):
    QuotaDatabase().update_quota(
        username, max_pods=max_pods, gpu_count=gpu_count, gpus=gpus,
        memory_limit=parse_storage_size(memory_limit) if memory_limit is not None else None,
        storage_size=parse_storage_size(storage_size) if storage_size is not None else None,
        shm_size=parse_storage_size(shm_size) if shm_size is not None else None,
        tmpfs_size=parse_storage_size(tmpfs_size) if tmpfs_size is not None else None,
        commit_count=commit_count,
        commit_size_limit=parse_storage_size(commit_size_limit) if commit_size_limit is not None else None
        )


@app.command(no_args_is_help=True, help="Remove user quota from database, so to use default fallback from config")
def reset(username: str):
    QuotaDatabase().delete_quota(username)


@app.command(help="Show user quotas, optionally filter by username")
def list(
    usernames: Optional[list[str]] = typer.Argument(None),
    quota_fallback: bool = typer.Option(False, "--fallback", help="Apply default quota values from config to unset fields")
    ):
    console = rich.console.Console()
    quota_db = QuotaDatabase()

    if usernames is None:
        usernames = [user.name for user in UserDatabase().list_users()]

    for idx, username in enumerate(usernames):
        console.print(f"{idx+1}. {username} {quota_db.check_quota(username, use_fallback=quota_fallback)}")