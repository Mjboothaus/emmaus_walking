# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/00_core.ipynb (unless otherwise specified).

__all__ = ['in_notebook', 'ipython_info', 'get_project_root', 'get_project_root_alternate']

# Cell
from pathlib import Path
import sys
import os

# Cell

def in_notebook() -> bool:
    """
    Returns ``True`` if the module is running in IPython kernel,
    ``False`` if in IPython shell or other Python shell.
    """
    #return "ipykernel" in sys.modules
    try:
        __IPYTHON__
        return True
    except NameError:
        return False


# later I found out this:


def ipython_info():
    ip = False
    if "ipykernel" in sys.modules:
        ip = "notebook"
    elif "IPython" in sys.modules:
        ip = "terminal"
    return ip


# Cell
def get_project_root() -> Path:
    if not in_notebook():
        print("NOT in Jupyter notebook")
        return Path(__file__).parent.parent
    else:
        print("In Jupyter notebook")
        return Path.cwd().parent



# Cell
def get_project_root_alternate():
    if Path(os.getcwd()).parent.stem == 'emmaus_walking':
        return Path(os.getcwd()).parent
    else:
        return Path(os.getcwd())   # to handle use of CLI - i.e. streamlit run emmaus_walking/app.py (as opposed to in notebooks)

# Cell

print('Project root directory: ' + get_project_root().as_posix())