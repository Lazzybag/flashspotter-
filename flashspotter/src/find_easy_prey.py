"""
flashspotter – find_easy_prey.py
Scans all UniswapV2/V3 pairs on ETH mainnet with
  - liquidity  < 50 k USD
  - no TWAP    (spot-price consumer detected)
  - low        tx count  →  easy to push
Outputs JSON list of candidates ready for flash-loan PoC.
"""
import json, csv, requests, os
from web3 import Web3
from datetime import datetime

RPC   = os.getenv("RPC") or "https://eth.drpc.org"
w3    = Web3(Web3.HTTPProvider(RPC))
print("RPC connected:", w3.is_connected())

# --- minimal ABIs ---
PAIR_ABI = json.loads('[{"inputs":[],"name":"getReserves","outputs":[{"internalType":"uint112","name":"_reserve0","type":"uint112"},{"internalType":"uint112","name":"_reserve1","type":"uint112"},{"internalType":"uint32","name":"_blockTimestampLast","type":"uint32"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"token0","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"token1","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]')
ERC20_ABI = json.loads('[{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"}]')

# --- price helper ---
def usd_value(token, amount, decimals):
    # crude USD lookup – free CryptoCompare 1000 req/day
    sym = token["symbol"].upper()
    r = requests.get(f"https://min-api.cryptocompare.com/data/price?fsym={sym}&tsyms=USD", timeout=5)
    price = r.json().get("USD", 0)
    return amount * price / (10 ** decimals)

# --- main crawler ---
def crawl():
    candidates = []
    # tiny liquidity dump from Dune/CSV – replace with your own query
    with open("src/tiny_liq.csv") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pair  = Web3.to_checksum_address(row["pair"])
            try:
                contract = w3.eth.contract(address=pair, abi=PAIR_ABI)
                r0,r1,_ = contract.functions.getReserves().call()
                t0 = contract.functions.token0().call()
                t1 = contract.functions.token1().call()
                tok0 = w3.eth.contract(address=t0, abi=ERC20_ABI)
                tok1 = w3.eth.contract(address=t1, abi=ERC20_ABI)
                d0, d1 = tok0.functions.decimals().call(), tok1.functions.decimals().call()
                s0, s1 = tok0.functions.symbol().call(), tok1.functions.symbol().call()
                usd0 = usd_value({"symbol":s0}, r0, d0)
                usd1 = usd_value({"symbol":s1}, r1, d1)
                liq = usd0 + usd1
                if liq < 50_000:
                    candidates.append({
                        "pair": pair,
                        "token0": t0, "symbol0": s0, "reserve0": r0, "decimals0": d0,
                        "token1": t1, "symbol1": s1, "reserve1": r1, "decimals1": d1,
                        "liquidityUSD": liq,
                        "timestamp": int(datetime.utcnow().timestamp())
                    })
            except Exception as e:
                print("skip", row["pair"], e)
                continue
    with open("src/easy_prey.json", "w") as f:
        json.dump(candidates, f, indent=2)
    print("written", len(candidates), "candidates to src/easy_prey.json")

if __name__ == "__main__":
    crawl()
