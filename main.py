from . import resources  # noqa: F401
from .ui import MainWindow


def main():
    global view
    view = MainWindow.show_window()
