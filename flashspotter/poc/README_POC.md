# Flash-Loan PoC runner

## One-command demo (inside Codespace)
1. Make sure `src/final_targets.json` exists (run `bash scripts/run_all.sh` first).
2. `cd poc`
3. `brownie run test_poc.py --network mainnet-fork`

You will see:
- FlashManipulator deployed
- 10 k tokenA dumped into chosen pool
- Victim contract queried at skewed price
- Profit left in contract (tokenB)

## Customize
Edit `test_poc.py`:
- Change `targets[0]` to another index
- Replace `borrow_calldata` with any victim function that uses spot reserves
