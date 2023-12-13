import pathlib
from PySide2.QtCore import QObject, QThread, Signal
import sys
from time import perf_counter
from subprocess import Popen, PIPE
from ..controller import core, Logger
from .pool_handler import PoolHandler


class MayaThreadWorker(QObject):
    operation_started = Signal()
    operation_ended = Signal()

    def __init__(self, command):
        super().__init__()
        self.running = False
        self.command = command

    def run(self):
        if self.running:
            return

        self.running = True
        self.operation_started.emit()

        if sys.platform == "darwin":
            with Popen(self.command, stdout=PIPE, stderr=PIPE) as process:
                # out, err = process.communicate()
                # Logger.info(out.decode())
                # Logger.info(err.decode())
                process.wait()
        elif sys.platform == "win32":
            with Popen(self.command) as process:
                # out, err = process.communicate()
                # Logger.info(out.decode())
                # Logger.info(err.decode())
                process.wait()

        self.running = False
        self.operation_ended.emit()

    def cancel(self):
        if self.running:
            self.running = False

    def shutdown(self):
        self.running = False

        current_thread = QThread.currentThread()
        if current_thread:
            current_thread.exit(0)


class HdrThreadWorker(QObject):
    operation_started = Signal()
    operation_ended = Signal()
    refresh_thumb = Signal(tuple)

    def __init__(self, pool_handler: PoolHandler, hdr_path, size):
        super().__init__()
        self.running = False
        self.pool_handler = pool_handler
        self.hdr_path = hdr_path
        self.size = size

    def run(self):
        if self.running:
            return
        self.running = True
        self.operation_started.emit()

        Logger.debug("starting hdr worker operation")
        start_time = perf_counter()
        assets = self.pool_handler.get_assets_and_thumbnails(self.hdr_path)

        for hdr_name, hdr_path, thumb, _ in assets:
            if thumb:
                continue

            thumbnail_path = (
                hdr_path.parent.parent
                / "Thumbnails"
                / f"{pathlib.Path(hdr_name).stem}.jpg"
            )

            core.create_sdr_preview(hdr_path, thumbnail_path, self.size)
            self.refresh_thumb.emit((hdr_path, thumbnail_path))

        Logger.debug(f"finished hdr worker operation {perf_counter()-start_time:.2f}s")
        self.running = False
        self.operation_ended.emit()

    def cancel(self):
        if self.running:
            self.running = False

    def shutdown(self):
        self.running = False

        current_thread = QThread.currentThread()
        if current_thread:
            current_thread.exit(0)
