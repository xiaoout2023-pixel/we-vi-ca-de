import subprocess
import time
import os
import sys
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MitmProxyManager:
    def __init__(self, port=8080, addon_path=None):
        self.port = port
        self.addon_path = addon_path
        self.process = None

    def start(self):
        logger.info(f"Starting mitmdump on port {self.port}")
        cmd = [
            sys.executable, "-m", "mitmproxy.tools.dump",
            "--listen-port", str(self.port),
            "--set", "flow_detail=0",
            "--set", "connection_strategy=lazy",
            "--set", "ssl_insecure=true",
        ]
        if self.addon_path:
            cmd.extend(["-s", self.addon_path])
        cmd.append("--quiet")

        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"

        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            cwd=os.getcwd()
        )
        time.sleep(2)

        if self.process.poll() is not None:
            stderr = self.process.stderr.read().decode('utf-8', errors='ignore')
            raise Exception(f"mitmdump failed to start: {stderr}")

        logger.info("mitmdump started successfully")

    def stop(self):
        if self.process:
            logger.info("Stopping mitmdump")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            logger.info("mitmdump stopped")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        return False
