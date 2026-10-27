"""
traffic/generate_traffic.py - Generate synthetic load on the Flask app.

Usage:
    python traffic/generate_traffic.py          # 100 requests, all features
    python traffic/generate_traffic.py --n 500  # 500 requests

Purpose:
    Populates Prometheus/Grafana graphs so that the dashboard shows
    meaningful data during the lab demonstration.
"""

import argparse
import random
import time
import requests

# ── Iris sample pools (one per class) ─────────────────────────────────────────
SETOSA_SAMPLES = [
    {"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2},
    {"sepal_length": 4.9, "sepal_width": 3.0, "petal_length": 1.4, "petal_width": 0.2},
    {"sepal_length": 4.7, "sepal_width": 3.2, "petal_length": 1.3, "petal_width": 0.2},
    {"sepal_length": 5.0, "sepal_width": 3.6, "petal_length": 1.4, "petal_width": 0.3},
]

VERSICOLOR_SAMPLES = [
    {"sepal_length": 7.0, "sepal_width": 3.2, "petal_length": 4.7, "petal_width": 1.4},
    {"sepal_length": 6.4, "sepal_width": 3.2, "petal_length": 4.5, "petal_width": 1.5},
    {"sepal_length": 6.9, "sepal_width": 3.1, "petal_length": 4.9, "petal_width": 1.5},
    {"sepal_length": 5.5, "sepal_width": 2.3, "petal_length": 4.0, "petal_width": 1.3},
]

VIRGINICA_SAMPLES = [
    {"sepal_length": 6.3, "sepal_width": 3.3, "petal_length": 6.0, "petal_width": 2.5},
    {"sepal_length": 5.8, "sepal_width": 2.7, "petal_length": 5.1, "petal_width": 1.9},
    {"sepal_length": 7.1, "sepal_width": 3.0, "petal_length": 5.9, "petal_width": 2.1},
    {"sepal_length": 6.5, "sepal_width": 3.0, "petal_length": 5.8, "petal_width": 2.2},
]

ALL_SAMPLES = SETOSA_SAMPLES + VERSICOLOR_SAMPLES + VIRGINICA_SAMPLES

# Occasionally send a bad request to generate error metrics
BAD_REQUEST = {"sepal_length": "bad", "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}


def send_requests(base_url: str, n: int, delay: float) -> None:
    """
    Send n POST requests to /predict and print a summary.

    Args:
        base_url : base URL of the app, e.g. http://localhost:5000
        n        : total number of requests to send
        delay    : seconds to wait between requests
    """
    ok_count = error_count = 0
    class_counts: dict = {}

    print(f"Sending {n} requests to {base_url}/predict …")

    for i in range(1, n + 1):
        # Every 10th request is intentionally malformed → generates error metrics
        if i % 10 == 0:
            payload = BAD_REQUEST
        else:
            payload = random.choice(ALL_SAMPLES)

        try:
            resp = requests.post(
                f"{base_url}/predict",
                json=payload,
                timeout=5,
            )
            if resp.status_code == 200:
                cls = resp.json().get("class_name", "unknown")
                class_counts[cls] = class_counts.get(cls, 0) + 1
                ok_count += 1
            else:
                error_count += 1
        except requests.exceptions.RequestException as exc:
            print(f"  Request {i} failed: {exc}")
            error_count += 1

        if i % 20 == 0:
            print(f"  Progress: {i}/{n}  ok={ok_count}  errors={error_count}")

        time.sleep(delay)

    print("\n── Summary ────────────────────────────")
    print(f"  Total    : {n}")
    print(f"  OK       : {ok_count}")
    print(f"  Errors   : {error_count}")
    print(f"  By class : {class_counts}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Traffic generator for Iris Predictor")
    parser.add_argument("--url",   default="http://localhost:5000", help="Base URL of the app")
    parser.add_argument("--n",     type=int, default=100,           help="Number of requests")
    parser.add_argument("--delay", type=float, default=0.05,        help="Delay between requests (s)")
    args = parser.parse_args()

    send_requests(args.url, args.n, args.delay)


if __name__ == "__main__":
    main()
