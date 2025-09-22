#!/usr/bin/env python3
"""
Chain scanner menu  –  Kimi @ flashspotter
1 = Polygon  |  2 = BSC  |  3 = Arbitrum
Same ABI, same logic, just pick a number.
"""
import json, csv, requests, os
from web3 import Web3

CHAINS = {
    "1": {
        "name": "Polygon",
        "rpc": "https://polygon-rpc.com",
        "factory": "0x5757371414417B8c6caAd45BaeF941Abc7d3aBEF",  # QuickSwap
        "usdc": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
        "dai": "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",
        "weth": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
        "flash_fee": 0.0,  # Balancer
    },
    "2": {
        "name": "BSC",
        "rpc": "https://bsc-dataseed.binance.org",
        "factory": "0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73",  # PancakeSwap
        "usdc": "0x8AC76a51cc950d9822D68b83fE1Ad62B1Fc5818d",  # USDC (BEP-20)
        "dai": "0x1AF3F329e8BE154074D8769D1FFa4eE058B1DBc3",   # DAI (BEP-20)
        "weth": "0x2170Ed0880ac9A755fd29B2688956BD959F933F8",  # ETH (BEP-20)
        "flash_fee": 0.0005,  # Venus 0.05 %
    },
    "3": {
        "name": "Arbitrum",
        "rpc": "https://arb1.arbitrum.io/rpc",
        "factory": "0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac",  # SushiSwap
        "usdc": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",
        "dai": "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",
        "weth": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
        "flash_fee": 0.0,  # Balancer
    },
}

PAIR_ABI = json.loads('[{"constant":true,"inputs":[],"name":"getReserves","outputs":[{"name":"_reserve0","type":"uint112"},{"name":"_reserve1","type":"uint112"},{"name":"_blockTimestampLast","type":"uint32"}],"type":"function"},{"constant":true,"inputs":[],"name":"token0","outputs":[{"name":"","type":"address"}],"type":"function"},{"constant":true,"inputs":[],"name":"token1","outputs":[{"name":"","type":"address"}],"type":"function"}]')
ERC20_ABI = json.loads('[{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}]')


def usd_price(chain, addr):
    stable = {chain["usdc"]: 1.0, chain["dai"]: 1.0}
    if addr in stable:
        return stable[addr]
    if addr == chain["weth"]:
        return 3000.0  # fallback ETH
    try:
        platform = {"Polygon": "polygon", "BSC": "binance-smart-chain", "Arbitrum": "arbitrum-one"}[chain["name"]]
        r = requests.get(
            f"https://api.coingecko.com/api/v3/simple/token_price/{platform}?contract_addresses={addr}&vs_currencies=usd",
            timeout=5,
        ).json()
        return float(r[list(r.keys())[0]]["usd"])
    except:
        return 0.0


def scan(chain):
    print(f"Scanning {chain['name']} …")
    w3 = Web3(Web3.HTTPProvider(chain["rpc"]))
    if not w3.is_connected():
        print("RPC dead"); return
    factory = w3.eth.contract(
        address=chain["factory"],
        abi=[{"inputs":[],"name":"allPairsLength","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"","type":"uint256"}],"name":"allPairs","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}],
    )
    total = factory.functions.allPairsLength().call()
    rows = []
    for i in range(total - 400, total):  # newest 400
        pair = factory.functions.allPairs(i).call()
        try:
            c = w3.eth.contract(address=pair, abi=PAIR_ABI)
            r0, r1, _ = c.functions.getReserves().call()
            t0 = c.functions.token0().call()
            t1 = c.functions.token1().call()
            d0 = w3.eth.contract(address=t0, abi=ERC20_ABI).functions.decimals().call()
            d1 = w3.eth.contract(address=t1, abi=ERC20_ABI).functions.decimals().call()
            p0, p1 = usd_price(chain, t0), usd_price(chain, t1)
            usd_liq = (r0 / 10 ** d0) * p0 + (r1 / 10 ** d1) * p1
            if usd_liq <= 40000 and usd_liq > 0:
                rows.append(pair)
                if len(rows) >= 6:
                    break
        except:
            continue
    with open("src/tiny_liq.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pair"])
        for p in rows:
            w.writerow([p])
    print(f"{chain['name']} done: {len(rows)} pools ≤40k USD")
    print(f"Flash-fee on this chain ≈ {chain['flash_fee'] * 100} %")


def menu():
    print("\n=== Chain Scanner Menu ===")
    print("1  Polygon  (0 % flash-fee, ~$0.05 gas)")
    print("2  BSC       (0.05 % flash-fee, ~$0.10 gas)")
    print("3  Arbitrum  (0 % flash-fee, ~$0.50 gas)")
    choice = input("Pick 1-3 (or q to quit): ").strip()
    if choice in CHAINS:
        scan(CHAINS[choice])
    elif choice.lower() == "q":
        exit()
    else:
        print("Bad choice, try again.")


if __name__ == "__main__":
    while True:
        menu()
