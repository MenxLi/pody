import typer
from typing import Optional
from pody.eng.user import UserDatabase

app = typer.Typer()

@app.command()
def add(
    username: str,
    password: str,
    admin: bool = False,
    max_pods: int = 1
    ):
    db = UserDatabase()
    db.add_user(username, password, admin, max_pods)

@app.command()
def delete(username: str):
    db = UserDatabase()
    db.delete_user(username)

@app.command()
def update(
    username: str, 
    password: Optional[str] = None,
    admin: Optional[bool] = None,
    max_pods: Optional[int] = None
    ):
    db = UserDatabase()
    db.update_user(username, password=password, is_admin=admin, max_pods=max_pods)