"""
Sends each payload in sample_feedback_payloads.json to the running backend's
/feedback/ endpoint and prints the response.

Usage:
    python -m scripts.test_feedback
    python -m scripts.test_feedback --base-url http://127.0.0.1:8000
"""

import json
import argparse
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
PAYLOADS_FILE = ROOT / "scripts" / "sample_feedback_payloads.json"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    with open(PAYLOADS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    for case in data["test_cases"]:
        print(f"\n--- {case['description']} ---")
        print("Payload:", json.dumps(case["payload"]))

        try:
            response = requests.post(
                f"{args.base_url}/feedback/",
                json=case["payload"],
                timeout=10,
            )
            print("Status:", response.status_code)
            print("Response:", response.json())
        except requests.RequestException as exc:
            print("Request failed:", exc)


if __name__ == "__main__":
    main()
