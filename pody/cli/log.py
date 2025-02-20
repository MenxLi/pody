
from typer import Typer
from typing import Optional
import rich
import logging
import sqlite3
from pody.eng.log import eval_logline

def levelstr2int(levelstr: str) -> int:
    import sys
    if sys.version_info < (3, 11):
        return logging.getLevelName(levelstr.upper())
    else:
        return logging.getLevelNamesMapping()[levelstr.upper()]

app = Typer(no_args_is_help=True)
console = rich.console.Console()

@app.command(
    help = "Show log records, optionally filter by log level, if log level is specified, only show records with severity greater than or equal to the specified log level",
    no_args_is_help=True
)
def show(
    db_file: str, 
    level: Optional[str] = None, 
    offset: int = 0,
    limit: int = 1000
    ):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    if level is None:
        cursor.execute("SELECT * FROM log ORDER BY created DESC LIMIT ? OFFSET ?", (limit, offset))
    else:
        level_int = levelstr2int(level)
        cursor.execute("SELECT * FROM log WHERE level >= ? ORDER BY created DESC LIMIT ? OFFSET ?", (level_int, limit, offset))
    levelname_color = {
        'DEBUG': 'blue',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'bold red', 
        'FATAL': 'bold red'
    }
    for row in cursor.fetchall():
        log = eval_logline(row)
        console.print(f"{log.created} [{levelname_color[log.levelname]}][{log.levelname}] [default]{log.message}")
    conn.close()

@app.command(
    help="Delete old log records, keep the latest [keep] records, optionally filter by log level, if log level is specified, only delete records with the specified log level",
    no_args_is_help=True
)
def shrink(db_file: str, keep: int  = 1000, level: Optional[str] = None):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    if level is None:
        cursor.execute("DELETE FROM log WHERE id NOT IN (SELECT id FROM log ORDER BY created DESC LIMIT ?)", (keep,))
    else:
        cursor.execute("DELETE FROM log WHERE levelname = ? and id NOT IN (SELECT id FROM log WHERE levelname = ? ORDER BY created DESC LIMIT ?)", (level.upper(), level.upper(), keep))
    conn.commit()
    conn.execute("VACUUM")
    conn.close()