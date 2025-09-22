#!/usr/bin/env python3
import os, json, csv, requests
from web3 import Web3

RPC = os.getenv("RPC") or "https://eth.drpc.org"
w3  = Web3(Web3.HTTPProvider(RPC))

V2_FACTORY = "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"
PAIR_ABI   = json.loads('[{"constant":true,"inputs":[],"name":"getReserves","outputs":[{"name":"_reserve0","type":"uint112"},{"name":"_reserve1","type":"uint112"},{"name":"_blockTimestampLast","type":"uint32"}],"type":"function"},{"constant":true,"inputs":[],"name":"token0","outputs":[{"name":"","type":"address"}],"type":"function"},{"constant":true,"inputs":[],"name":"token1","outputs":[{"name":"","type":"address"}],"type":"function"}]')
ERC20_ABI  = json.loads('[{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}]')

# ---------- robust USD price ----------
STABLE = {
    "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48": 1.0,  # USDC
    "0x6B175474E89094C44Da98b954EedeAC495271d0F": 1.0,  # DAI
    "0xdAC17F958D2ee523a2206206994597C13D831ec7": 1.0,  # USDT
}
ETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"

def usd_price_robust(addr):
    if addr in STABLE: return STABLE[addr]
    if addr == ETH: return 3000.0                       # fallback ETH price
    try:
        r = requests.get(
            f"https://api.coingecko.com/api/v3/simple/token_price/ethereum?contract_addresses={addr}&vs_currencies=usd",
            timeout=5,
        ).json()
        return float(r[list(r.keys())[0]]["usd"])
    except:
        return 0.0  # will skip if both sides zero


# ---------- lending pools (≥ 1000 USD cash) ----------
COMMON_LENDING = {  # same as before
    "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48": "0xBcca60bB61934080951369a648Fb03DF4F96263C",  # aUSDC
    "0x6B175474E89094C44Da98b954EedeAC495271d0F": "0x3Ed3B47Dd13EC9a98b44e6204A523E766B225811",  # aDAI
    "0xdAC17F958D2ee523a2206206994597C13D831ec7": "0x3Ed3B47Dd13EC9a98b44e6204A523E766B225811",  # aUSDT
}
LENDING_ABI = json.loads('[{"constant":true,"inputs":[],"name":"getCash","outputs":[{"name":"","type":"uint256"}],"type":"function"}]')


def lending_cash_usd(asset):
    pool = COMMON_LENDING.get(asset)
    if not pool:
        return None, 0
    try:
        c = w3.eth.contract(address=pool, abi=LENDING_ABI)
        cash = c.functions.getCash().call()
        dec = w3.eth.contract(address=asset, abi=ERC20_ABI).functions.decimals().call()
        usd = STABLE.get(asset, 0) or 1.0  # assume 1 if stable else fail-safe
        cash_usd = (cash / 10 ** dec) * usd
        return (pool, cash_usd) if cash_usd >= 1000 else (None, 0)
    except:
        return None, 0


# ---------- scan ----------
def main():
    factory = w3.eth.contract(
        address=V2_FACTORY,
        abi=[{"inputs":[],"name":"allPairsLength","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"","type":"uint256"}],"name":"allPairs","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}],
    )
    total = factory.functions.allPairsLength().call()
    rows = []
    for i in range(total - 1000, total):  # last 1000
        pair = factory.functions.allPairs(i).call()
        try:
            c = w3.eth.contract(address=pair, abi=PAIR_ABI)
            r0, r1, _ = c.functions.getReserves().call()
            t0 = c.functions.token0().call()
            t1 = c.functions.token1().call()
            d0 = w3.eth.contract(address=t0, abi=ERC20_ABI).functions.decimals().call()
            d1 = w3.eth.contract(address=t1, abi=ERC20_ABI).functions.decimals().call()
            p0 = usd_price_robust(t0)
            p1 = usd_price_robust(t1)
            usd_liq = (r0 / 10 ** d0) * p0 + (r1 / 10 ** d1) * p1
            if usd_liq > 40000 or usd_liq <= 0:
                continue
            victim0, cash0 = lending_cash_usd(t0)
            victim1, cash1 = lending_cash_usd(t1)
            if cash0 >= 1000:
                rows.append((pair, victim0))
            elif cash1 >= 1000:
                rows.append((pair, victim1))
            if len(rows) >= 8:
                break
        except:
            continue
    with open("src/tiny_liq.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pair", "victim"])
        for r in rows:
            w.writerow(r)
    print(f"Found {len(rows)} ≤40k USD pools with ≥1k lending cash")


if __name__ == "__main__":
    main()
