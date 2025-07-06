import os, subprocess
from pathlib import Path

import typer

app = typer.Typer(no_args_is_help=True)

@app.command()
def show_home() -> None:
    """
    Show the current Pody home directory.
    This is where Pody stores its data and configuration files.
    """
    pody_home = os.environ.get("PODY_HOME", str(Path.home() / ".pody"))
    print(f"{pody_home}")

@app.command()
def systemd_unit(port = 8799) -> None:
    """
    Generate a systemd unit file for the Pody service to start on boot.

    This will generate a systemd service that runs `pody-serve` on startup and prints the unit file content to stdout. 
    Should put the output to global systemd unit directory, e.g. 

    > [this_command] | sudo tee /etc/systemd/system/pody.service

    and enable it with:  \n
    > systemctl daemon-reload && systemctl enable pody.service && systemctl start pody.service
    """
    CMD = "pody-serve"

    def run_command(cmd: str) -> str:
        """
        Run a shell command and return its output.
        Raises an error if the command fails.
        """
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            check=True, 
            shell=True
        )
        return result.stdout.strip()

    cmd_path = run_command(f"which {CMD}")
    if not cmd_path:
        typer.echo(f"Error: Command '{CMD}' not found in PATH.", err=True)
        raise typer.Exit(code=1)
    
    username = run_command("whoami")
    if not username:
        typer.echo("Error: Unable to determine the current user.", err=True)
        raise typer.Exit(code=1)

    env = dict(os.environ)
    enviroment = "".join(f"{key}={value}" for key, value in env.items() if key.startswith("PODY_"))

    # Build ExecStart command
    exec_start = f"{cmd_path} --port {port}"

    # Generate unit file content
    unit_content = f"""\
[Unit]
Description=Run pody-serve on port {port} at boot
After=network.target

[Service]
Type=simple
User={username}
Environment="{enviroment}"
ExecStart={exec_start}
WorkingDirectory={Path.home()}
Restart=on-failure
RestartSec=10s

[Install]
WantedBy=multi-user.target
"""
    print(unit_content)