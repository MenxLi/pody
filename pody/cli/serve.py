from pody.svc.app import start_server
import typer

def main():
    typer.run(start_server)