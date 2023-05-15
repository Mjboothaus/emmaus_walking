from pathlib import Path
import sys


def in_notebook() -> bool:
    """
    Returns ``True`` if the module is running in IPython kernel,
    ``False`` if in IPython shell or other Python shell.
    """
    return "ipykernel" in sys.modules


def ipython_info():
    ip = False
    if "ipykernel" in sys.modules:
        ip = "notebook"
    elif "IPython" in sys.modules:
        ip = "terminal"
    return ip


def get_project_root() -> Path:
    return Path.cwd().parent if in_notebook() else Path(__file__).parent
