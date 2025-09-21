#!/usr/bin/env python3
"""
price_oracle_detector.py
For every candidate pair, quickly decides whether ANY external contract
reads getReserves()/slot0() directly (i.e. uses spot price).
Outputs the same JSON list but adds:
  "spot_consumer": "0xabc...|None"
"""
import json, requests, time, os
from web3 import Web3

RPC = os.getenv("RPC") or "https://eth.drpc.org"
w3  = Web3(Web3.HTTPProvider(RPC))

# simple heuristic: look for getReserves() or slot0() calls in the last 10k txs
ABI_GETRES = [{"name":"getReserves","type":"function","inputs":[],"outputs":[{"type":"uint112"},{"type":"uint112"},{"type":"uint32"}]}]
ABI_SLOT0  = [{"name":"slot0","type":"function","inputs":[],"outputs":[{"type":"uint160"},{"type":"int24"},{"type":"uint16"},{"type":"uint16"},{"type":"uint16"},{"type":"uint8"},{"type":"bool"}]}]

def has_spot_consumer(pair, is_v3=False):
    abi = ABI_SLOT0 if is_v3 else ABI_GETRES
    c   = w3.eth.contract(address=pair, abi=abi)
    # last 10k txs – free Etherscan API (rate-limit 5/sec)
    api = f"https://api.etherscan.io/api?module=account&action=txlist&address={pair}&startblock=0&endblock=99999999&page=1&offset=100&sort=desc&apikey=YourApiKeyToken"
    r   = requests.get(api, timeout=10).json()
    if r["status"] != "1":
        return None
    txs = r["result"][:100]          # newest 100
    for tx in txs:
        if tx["input"].startswith("0x0902f1ac"):   # getReserves selector
            to = tx["to"]
            if to != pair.lower():                 # external caller
                return to
        if tx["input"].startswith("0x3850c7bd"):   # slot0 selector
            to = tx["to"]
            if to != pair.lower():
                return to
    return None

def main():
    with open("src/easy_prey.json") as f:
        pairs = json.load(f)
    for p in pairs:
        consumer = has_spot_consumer(p["pair"])
        p["spot_consumer"] = consumer
        print(p["pair"], "->", consumer)
        time.sleep(0.2)
    with open("src/final_targets.json", "w") as f:
        json.dump([p for p in pairs if p["spot_consumer"]], f, indent=2)
    print("final_targets.json ready – only pools with external spot-price consumers.")

if __name__ == "__main__":
    main()
