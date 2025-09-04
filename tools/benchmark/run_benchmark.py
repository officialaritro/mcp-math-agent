import json
import requests
from tqdm import tqdm
import os

API = os.getenv("API_URL", "http://localhost:8000/ask")
BENCH_FILE = os.getenv("BENCH_FILE", "tools/benchmark/bench.json")

def run():
    bench = json.load(open(BENCH_FILE))
    correct = 0
    abstain = 0
    results = []
    for item in tqdm(bench):
        q = item["question"]
        expected = item.get("answer", "")
        r = requests.post(API, json={"question": q}, timeout=30)
        if r.status_code != 200:
            res = {"question": q, "status": "error"}
            results.append(res)
            continue
        body = r.json()
        ans = body.get("answer","").strip().lower()
        ok = expected.lower() in ans if expected else None
        if ok is True:
            correct += 1
        elif ans == "" or "cannot find reliable" in ans.lower():
            abstain += 1
        results.append({"question": q, "answer": ans, "ok": ok})
    total = len(bench)
    print("Total:", total, "Correct:", correct, "Abstain:", abstain, "Acc:", correct/total if total else 0)

if __name__ == "__main__":
    run()
