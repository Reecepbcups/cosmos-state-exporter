import json
import os
from typing import List


class Config:
    chains: List[dict] = []
    snapshot_storage_dir: str = ""


def load_config() -> Config:
    currPath = os.path.dirname(os.path.realpath(__file__))

    configFilePath = f"{currPath}/config.json"
    if not os.path.isfile(configFilePath):
        missing_err_panic("from this directory")

    with open(configFilePath) as f:
        c = json.load(f)

        if "chains" not in c:
            missing_err_panic("chains key.")

        chains: List[dict] = c["chains"]
        if len(chains) == 0:
            print("No chains found in config.json. Exiting...")
            exit()

        # validate snapshot_storage_dir
        if "snapshot_storage_dir" not in c:
            missing_err_panic("snapshot_storage_dir key.")

        storage_dir = c["snapshot_storage_dir"]

    cfg = Config()
    cfg.chains = chains
    cfg.snapshot_storage_dir = storage_dir
    return cfg


def missing_err_panic(missing: str):
    print(f"config.json is missing {missing}")
    print("Make sure to copy the example file.\nExiting...")
    exit()
