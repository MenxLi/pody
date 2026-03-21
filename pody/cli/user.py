import typer
import rich.console
from typing import Optional
from pody.eng.user import UserDatabase
from pody.eng.quota import QuotaDatabase
from ..eng.docker import ContainerAction, DockerController

app = typer.Typer(
    help = "Manage users in the system",
    no_args_is_help=True
    )

@app.command(no_args_is_help=True, help="Add user")
def add(
    username: str,
    password: str,
    admin: bool = False,
    ):
    db = UserDatabase()
    db.add_user(username, password, admin)

@app.command(no_args_is_help=True, help="Update user password or admin status")
def update(
    username: str, 
    password: Optional[str] = None,
    admin: Optional[bool] = None,
    ):
    UserDatabase().update_user(username, password=password, is_admin=admin)

@app.command(help="List users, optionally filter by username")
def list(
    usernames: Optional[list[str]] = typer.Argument(None),
    ):
    console = rich.console.Console()
    users = UserDatabase().list_users(usernames)
    for idx, user in enumerate(users):
        console.print(f"{idx+1}. {user}")

def __attempt_user_del(username: str, auto_proceed_on_failure: bool):
    try:
        UserDatabase().delete_user(username)
    except Exception as e:
        typer.echo(f"[Error] Failed to delete user: \n{e}.", err=True)

        if not auto_proceed_on_failure:
            typer.confirm("Would you still like to delete remaining resources?", abort=True)

@app.command(help="Delete user", no_args_is_help=True)
def delete(username: str):
    __attempt_user_del(username, auto_proceed_on_failure=False)
    QuotaDatabase().delete_quota(username)

@app.command(help="Delete user and all related containers", no_args_is_help=True)
def purge(
    username: str, 
    yes: bool= typer.Option(False, "--yes", "-y", help="Skip confirmation")
    ):
    if not yes:
        typer.confirm(f"Are you sure to purge user {username}?", abort=True)
    c = DockerController()

    __attempt_user_del(username, auto_proceed_on_failure=yes)
    QuotaDatabase().delete_quota(username)
    containers = c.list_docker_containers(filter_name=username + "-")
    for container in containers:
        c.container_action(container, ContainerAction.DELETE)
        print(f"Container [{container}] removed")