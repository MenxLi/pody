import os
import pathlib

DATA_HOME = pathlib.Path(os.environ.get('PODY_HOME', os.path.expanduser('~/.pody')))