# flake8: noqa
# modified to run logic in here as well
# https://github.com/Reecepbcups/airdrop-tools/blob/main/export-sort/utils.py

import json
import os
import time

import ijson

current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
exports_folder = os.path.join(parent_dir, "_EXPORTS")

sections = {
    # locations within the genesis file for ijson, every section MUST end with .item to grab the values
    "app_state": "app_state",
    "staked_amounts": "app_state.staking.delegations.item",
    "account_balances": "app_state.bank.balances.item",
    "total_supply": "app_state.bank.supply.item",
    # useful to get like, a validator bonded status. Is a list
    "validators_info": "app_state.staking.validators.item",
}


# Module Keys (names example)
# ['auth', 'authz', 'bank', 'capability', 'crisis',
# 'distribution', 'evidence', 'feegrant', 'feeibc', 'feeshare',
# 'genutil', 'globalfee', 'gov', 'ibc', 'ibchooks', 'interchainaccounts',
# 'intertx', 'mint', 'oracle', 'packetfowardmiddleware', 'params',
# 'slashing', 'staking', 'tokenfactory', 'transfer', 'upgrade', 'vesting', 'wasm']
def sort_and_save_to_file(
    snapshotJSONLoc, output_dir, export_height, WANTED_SECTION=["bank", "staking"]
):
    v = get_keys(snapshotJSONLoc, debug=False)
    for idx, obj in v:
        state_key = obj[0]

        # SDK v45 chains require [] for modules to export. Only bank and staking then
        if len(WANTED_SECTION) == 0:
            WANTED_SECTION = ["bank", "staking"]

        if state_key not in WANTED_SECTION:
            print(f"skipping {state_key}...")
            continue

        print(f"{idx}: {state_key}")

        file_path = os.path.join(output_dir, f"{export_height}_{state_key}.json")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as f:
            json.dump(obj[1], f, indent=1)


def stream_section(fileName, key, debug=False):
    """
    Given a fileName and a json key location,
    it will stream the jso objects in that section
    and yield them as:
    -> index, object
    """
    if key not in sections:
        print(f"{key} not in sections")
        return

    key = sections[key]

    with open(fileName, "rb") as input_file:
        parser = ijson.items(input_file, key)
        for idx, obj in enumerate(parser):
            if debug:
                print(f"stream_section: {idx}: {obj}")
            yield idx, obj


def get_keys(file_path, debug=False):
    """
    Streams the state_export.json's Key Value pairs
    """
    with open(file_path, "rb") as input_file:
        parser = ijson.kvitems(input_file, sections["app_state"])
        for idx, obj in enumerate(parser):
            if debug:
                print(f"stream_section: {idx}: {obj}")
            yield idx, obj


def debug(*line):
    print(*line)
    current_time = time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime())
    with open(current_dir + "/debug.log", "a") as f:
        f.write(f"{current_time} {' '.join(line)}\n")


def timer_func(func):
    def wrap_func(*args, **kwargs):
        t1 = time.time()
        result = func(*args, **kwargs)
        t2 = time.time()
        debug(f"Function {func.__name__!r} executed in {(t2-t1):.4f}s")
        return result

    return wrap_func


# print(get_export_file_location("test.txt"))
