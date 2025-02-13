import typer
import rich
from typing import Optional
from pody.eng.user import UserDatabase

app = typer.Typer()

@app.command()
def add(
    username: str,
    password: str,
    admin: bool = False,
    ):
    db = UserDatabase()
    db.add_user(username, password, admin)

@app.command()
def delete(username: str):
    db = UserDatabase()
    db.delete_user(username)

@app.command()
def update(
    username: str, 
    password: Optional[str] = None,
    admin: Optional[bool] = None,
    ):
    db = UserDatabase()
    db.update_user(username, password=password, is_admin=admin)

@app.command(help="List users, optionally filter by username")
def info(usernames: Optional[list[str]] = typer.Argument(None)):
    console = rich.console.Console()
    db = UserDatabase()
    users = db.list_users(usernames)
    for idx, user in enumerate(users):
        console.print(f"{idx+1}. {user} {db.check_user_quota(user.name)}")

@app.command()
def update_quota(
    username: str, 
    max_pods: Optional[int] = None,
    gpu_count: Optional[int] = None,
    memory_limit: Optional[str] = None
    ):
    db = UserDatabase()
    db.update_user_quota(username, max_pods=max_pods, gpu_count=gpu_count, memory_limit=memory_limit)
