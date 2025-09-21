# FlashSpotter
Find Uniswap V2/V3 pools <$50k liquidity that expose `getReserves()`/`slot0()` to external contracts – perfect for flash-loan price-push PoCs.

## Quick start (Codespace)
1. Duplicate `scripts/env.example` → `.env` and add your RPC key.
2. `pip install -r requirements.txt`
3. `bash scripts/run_all.sh`  
   → produces `src/final_targets.json` with the easiest prey.
4. `cd poc && brownie run test_poc.py` to see a live exploit demo.

## Repo map
src/                 – on-chain scanners  
poc/contracts/       – FlashManipulator.sol template  
poc/test/            – Brownie PoC runner  
scripts/             – one-click pipeline
