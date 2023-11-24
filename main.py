from pathlib import Path

from dotenv import load_dotenv

from .resources import qt_resource_data
from .ui import MainWindow


def main():
    path = Path(__file__).parent / "settings" / ".env"
    load_dotenv(dotenv_path=path)
    global view
    view = MainWindow.show_window()
