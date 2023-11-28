# flake8: noqa
"""
Reece Williams | Nov 2023 (private original from May 2021)

Usage: sudo python3 snapshot.py [service_name,service_name2,...]

Setup: README.md
"""

import os
import sys
from typing import List

from blockchain_service import Blockchain
from config import load_config
from export_utils import debug, sort_and_save_to_file

# load the config from the file
cfg = load_config()

# loaded from init() in main()
ALL_SERVICES: List[Blockchain] = []


def main():
    # require root, load in ALL_SERVICES from config file.
    init()

    # python3 snapshot.py gaia,juno,...
    to_run = ""
    if len(sys.argv) > 1:
        to_run = sys.argv[1].lower()

    print("Services to run:", to_run)

    for service in ALL_SERVICES:
        if to_run != "" and service.name.lower() not in to_run:
            continue

        print(f"Running {service.name} export logic...")

        current = service.get_block_height()

        # gets the next export height compared to current if there is no file created already (e.g. first snapshots)
        newRoundedHeight = current - (current % service.height_per_snapshot)
        last_export = service.get_last_export_height(newRoundedHeight)

        export_height = last_export + service.height_per_snapshot
        print(
            f"Service: {service.name}, Current height: {current}, last snapshot: {last_export}, next export is at: {export_height} (in {export_height-current} blocks)"
        )

        if current < export_height:
            print("No need to export yet")
            return

        fileLoc = service.export(
            export_height, service.requested_modules, service.export_pipe_symbol
        )  # stop, export, start, update last height

        # get size of the file fileLoc
        size = os.path.getsize(fileLoc)
        if size < 10:  # 10 bytes, we had an error with a file of 0 bytes before
            debug(f"File size is too small, not uploading: {size}. Retrying next time")
            os.remove(fileLoc)
            return

        # sort export in same dir with cosmos airdrop tool
        export_path = os.path.join(os.path.dirname(fileLoc), str(export_height))
        print("\nSorting snapshot and extracting balance & staking info")
        sort_and_save_to_file(
            fileLoc,
            export_path,  # /root/snapshots/juno/9999.tar.xz
            export_height,
            WANTED_SECTION=service.requested_modules,
        )

        # sudo apt install xz-utils
        cmd = f"cd {os.path.dirname(export_path)} && tar cfzv {export_height}.tar.xz {export_height}/"
        debug(cmd)
        res = os.system(cmd)

        # ensure export_path is not just a /
        if export_path != "/" and fileLoc != "/":
            os.system(
                f"rm -rf {export_path} {fileLoc}"
            )  # add fileLoc too delete the original snapshot
        else:
            debug(f"Not removing {export_path}, {fileLoc}")

        # check if there are more exports to be done (if we are behind)
        # Example: last exports was at 1_000_000, but current is 1_030_000. Since we export every 10k, we should export 1_010_000, 1_020_000, 1_030_000.
        # To do this, we need to call main() again
        if current - export_height > service.height_per_snapshot:
            debug(
                f"Current height is {current}, but we are exporting at {export_height}. We are behind, calling main() again"
            )
            main()


def init():
    if os.geteuid() != 0:
        print("Must run this command as sudo (ex: `sudo python3 snapshot.py`)")
        print(
            "Reason: sometimes the binary does not have permission to read from the home dir data/application.db/LOG file and fails."
        )
        print("Exiting...")
        return

    for chain in cfg.chains:
        b = Blockchain(
            service_name=chain["service_name"],
            home_dir=chain["home_dir"],
            binary_path=chain["binary_path"],
            rpc_addr=chain["rpc_addr"],
            requested_modules=chain["requested_modules"],
            height_per_snapshot=chain["height_per_snapshot"],
            export_pipe_symbol=chain["export_pipe_symbol"],
        )
        ALL_SERVICES.append(b)


if __name__ == "__main__":
    main()
