# flake8: noqa
import os
import time
from typing import List

import requests
from config import load_config
from export_utils import current_dir, debug, timer_func

last_snapshots_dir = os.path.join(current_dir, "last_snapshots")
os.makedirs(last_snapshots_dir, exist_ok=True)

cfg = load_config()
os.makedirs(cfg.snapshot_storage_dir, exist_ok=True)


def _rpc_direct_query_height(rpc_addr) -> int:
    try:
        v = requests.get(f"{rpc_addr}/abci_info")
        if v.status_code != 200:
            debug("Error getting abci_info")
            return -1
        return int(v.json()["result"]["response"]["last_block_height"])
    except Exception as e:
        debug(str(e))
        return -1


class Blockchain:
    def __init__(
        self,
        service_name: str,
        home_dir="/root/.juno",
        binary_path="/root/go/bin/junod",
        rpc_addr="http://localhost:26657",
        requested_modules: List[str] = [],
        height_per_snapshot: int = 20_000,
        export_pipe_symbol: str = ">",
    ):
        """
        Input the service name without .service.
        Ensure binary_path is chmod +x'ed or 777'ed
        """
        self.name = service_name  # same for sub_dir in the snapshots folder
        self.home_dir = home_dir
        self.bin = binary_path

        self.requested_modules = requested_modules
        self.height_per_snapshot = height_per_snapshot
        self.export_pipe_symbol = export_pipe_symbol

        if rpc_addr.endswith("/"):
            rpc_addr = rpc_addr[:-1]
        self.rpc_addr = rpc_addr

        self.block_height = -1

    # Service
    def stop(self):
        debug(f"\n\nStopping {self.name} service...")
        os.popen(f"sudo systemctl stop {self.name}")

    def start(self):
        debug(f"Starting {self.name} service...")
        os.popen(f"sudo systemctl start {self.name}")

    def status(self):
        return os.popen(f"sudo systemctl status {self.name}").read()

    def get_block_height(self) -> int:
        """Cached version of _rpc_direct_query_height(). Stars the node to query it if it is down."""
        if self.block_height != -1:
            return (
                self.block_height
            )  # last version if we need to export multiple as we iterate

        self.block_height = _rpc_direct_query_height(self.rpc_addr)
        if self.block_height == -1:
            debug(f"Service {self.name} was down, retrying in 30 seconds...")
            self.start()
            time.sleep(30)
            self.block_height = _rpc_direct_query_height(self.rpc_addr)

        return self.block_height

    # where export_symbol is either > (SDK v46/47 chains) or 1> for SDK v45 chains
    @timer_func
    def _actual_export_logic(
        self, export_height: int, MODULES: list[str], export_symbol: str
    ) -> str:
        file = f"{cfg.snapshot_storage_dir}/{self.name}/export_{export_height}.json"
        os.makedirs(os.path.dirname(file), exist_ok=True)

        cmd = f"sudo {self.bin} export --height {export_height} --home {self.home_dir} {export_symbol} {file}"
        if len(MODULES) > 0:  # SDK v46+ specific support
            cmd += f" --modules-to-export {','.join(MODULES)}"

        debug(cmd)
        os.system(cmd)

        # find the first { in the file. Remove any content before that
        with open(file, "r") as f:
            contents = f.read()
            start = contents.find("{")
            contents = contents[start:]
        with open(file, "w") as f:
            f.write(contents)

        debug(f"Node export completed for {file}")
        return file

    def export(self, export_height: int, MODULES: list[str], export_symbol: str) -> str:
        self.stop()
        time.sleep(10)
        debug(self.status())

        debug("Doing export now...")
        fileLoc = self._actual_export_logic(export_height, MODULES, export_symbol)

        time.sleep(10)
        self.start()
        self.update_last_export_height(
            export_height
        )  # save these to their own dir? so we can run multiple chains at once?
        return fileLoc

    # nextNewRoundedHeight = current - (current % HEIGHT_PER_SNAPSHOT) so that way
    # the new file is the next actual height to be exported
    def get_last_export_height(self, nextNewRoundedHeight: int) -> int:
        last_snapshot = 0
        filepath = f"{last_snapshots_dir}/{self.name}.txt"

        if not os.path.exists(filepath):
            with open(filepath, "w") as f:
                f.write(f"{nextNewRoundedHeight}")

        with open(filepath, "r") as f:
            last_snapshot = int(f.read())

        return last_snapshot

    def update_last_export_height(self, new_height: str | int) -> None:
        with open(last_snapshots_dir + f"/{self.name}.txt", "w") as f:
            f.write(f"{new_height}")
