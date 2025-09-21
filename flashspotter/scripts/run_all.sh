#!/usr/bin/env bash
set -e
echo "1️⃣  Fetching live sub-50k pairs…"
python3 src/fetch_live_sub50k.py
echo "2️⃣  Scanning reserves & USD value…"
python3 src/find_easy_prey.py
echo "3️⃣  Detecting spot-price consumers…"
python3 src/price_oracle_detector.py
echo "✅  final_targets.json ready – open poc/ next"
