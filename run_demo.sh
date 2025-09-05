#!/usr/bin/env bash
set -euo pipefail
API="http://localhost:8000/ask"
OUT="demo_results.jsonl"
echo "[]">$OUT.tmp || true
examples=(
  "What is 2+2?"
  "Solve x^2 - 5x + 6 = 0"
  "Differentiate sin(x^2) with respect to x"
  "Integrate x^3 dx from 0 to 2"
)

echo "Running demo queries and saving to $OUT"
for q in "${examples[@]}"; do
  echo "Query: $q"
  resp=$(curl -sS -X POST "$API" -H "Content-Type: application/json" -d "{\"question\":\"$q\"}")
  echo "$(jq -c --arg q "$q" --argjson r "$resp" '{"question":$q,"response":$r}')"
  echo "{\"question\":\"$q\",\"response\":$resp}" >> $OUT
done
echo "Results written to $OUT"
