import json
import time
import urllib.request
import urllib.error
from statistics import mean

BASE_URL = "http://127.0.0.1:8000"


def request(method, path, body=None, raw_body=None, content_type="application/json"):
    url = BASE_URL + path

    data = None
    if raw_body is not None:
        data = raw_body.encode("utf-8")
    elif body is not None:
        data = json.dumps(body).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": content_type},
        method=method,
    )

    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            elapsed = time.time() - start
            text = resp.read().decode("utf-8")
            try:
                parsed = json.loads(text)
            except Exception:
                parsed = text
            return resp.status, parsed, elapsed
    except urllib.error.HTTPError as e:
        elapsed = time.time() - start
        text = e.read().decode("utf-8")
        try:
            parsed = json.loads(text)
        except Exception:
            parsed = text
        return e.code, parsed, elapsed
    except Exception as e:
        elapsed = time.time() - start
        return 0, {"error": str(e)}, elapsed


TESTS = [
    {
        "name": "Health endpoint",
        "method": "GET",
        "path": "/health",
        "body": None,
        "allowed_status": [200],
    },
    {
        "name": "Invalid JSON",
        "method": "POST",
        "path": "/analyze-ticket",
        "raw_body": "{ invalid json",
        "allowed_status": [400, 422],
    },
    {
        "name": "Missing ticket_id",
        "method": "POST",
        "path": "/analyze-ticket",
        "body": {"complaint": "Something wrong"},
        "allowed_status": [422],
    },
    {
        "name": "Missing complaint",
        "method": "POST",
        "path": "/analyze-ticket",
        "body": {"ticket_id": "BAD-001"},
        "allowed_status": [422],
    },
    {
        "name": "Empty complaint",
        "method": "POST",
        "path": "/analyze-ticket",
        "body": {"ticket_id": "BAD-002", "complaint": ""},
        "allowed_status": [422],
    },
    {
        "name": "Wrong language enum",
        "method": "POST",
        "path": "/analyze-ticket",
        "body": {
            "ticket_id": "BAD-003",
            "complaint": "Payment failed",
            "language": "spanish"
        },
        "allowed_status": [422],
    },
    {
        "name": "Wrong transaction enum",
        "method": "POST",
        "path": "/analyze-ticket",
        "body": {
            "ticket_id": "BAD-004",
            "complaint": "Payment failed 500 taka",
            "transaction_history": [
                {
                    "transaction_id": "TXN-BAD",
                    "timestamp": "2026-04-14T10:00:00Z",
                    "type": "unknown_type",
                    "amount": 500,
                    "counterparty": "MERCHANT-X",
                    "status": "completed"
                }
            ]
        },
        "allowed_status": [422],
    },
    {
        "name": "Amount as string",
        "method": "POST",
        "path": "/analyze-ticket",
        "body": {
            "ticket_id": "EDGE-001",
            "complaint": "Payment failed 500 taka",
            "transaction_history": [
                {
                    "transaction_id": "TXN-EDGE",
                    "timestamp": "2026-04-14T10:00:00Z",
                    "type": "payment",
                    "amount": "500",
                    "counterparty": "MERCHANT-X",
                    "status": "failed"
                }
            ]
        },
        "allowed_status": [200, 422],
    },
    {
        "name": "Large noisy complaint",
        "method": "POST",
        "path": "/analyze-ticket",
        "body": {
            "ticket_id": "EDGE-002",
            "complaint": "😡 " * 1000 + " payment failed 1200 taka balance deducted " + "!!! " * 1000,
            "language": "mixed",
            "transaction_history": [
                {
                    "transaction_id": "TXN-LARGE",
                    "timestamp": "2026-04-14T10:00:00Z",
                    "type": "payment",
                    "amount": 1200,
                    "counterparty": "MERCHANT-X",
                    "status": "failed"
                }
            ]
        },
        "allowed_status": [200],
    },
]


def main():
    print("=" * 90)
    print("QueueStorm Reliability + Malformed Input Test")
    print("=" * 90)

    failed = []
    latencies = []

    for test in TESTS:
        status, body, elapsed = request(
            test["method"],
            test["path"],
            body=test.get("body"),
            raw_body=test.get("raw_body"),
        )

        latencies.append(elapsed)

        print("-" * 90)
        print(test["name"])
        print(f"Status: {status}")
        print(f"Latency: {elapsed:.4f}s")

        if status in test["allowed_status"]:
            print("✅ Status acceptable")
        else:
            print(f"❌ Unexpected status. Allowed: {test['allowed_status']}")
            failed.append(test["name"])

        if status == 500:
            print("❌ 500 error detected")
            failed.append(test["name"])

        body_text = json.dumps(body, ensure_ascii=False) if not isinstance(body, str) else body

        forbidden_leaks = ["traceback", "api_key", "secret", "token", "password="]
        leaks = [x for x in forbidden_leaks if x.lower() in body_text.lower()]

        if leaks:
            print(f"❌ Possible sensitive/debug leak: {leaks}")
            failed.append(test["name"])
        else:
            print("✅ No obvious stack trace/secret leak")

    print("=" * 90)
    print("Rapid request latency test")
    print("=" * 90)

    valid_payload = {
        "ticket_id": "LOAD-001",
        "complaint": "I paid 850 taka but payment failed and balance deducted",
        "language": "en",
        "transaction_history": [
            {
                "transaction_id": "TXN-LOAD",
                "timestamp": "2026-04-14T10:00:00Z",
                "type": "payment",
                "amount": 850,
                "counterparty": "BILLER-X",
                "status": "failed"
            }
        ]
    }

    load_latencies = []
    load_failures = 0

    for i in range(30):
        payload = dict(valid_payload)
        payload["ticket_id"] = f"LOAD-{i:03d}"

        status, body, elapsed = request("POST", "/analyze-ticket", body=payload)
        load_latencies.append(elapsed)

        if status != 200:
            load_failures += 1

    print(f"Load requests: 30")
    print(f"Failures: {load_failures}")
    print(f"Avg latency: {mean(load_latencies):.4f}s")
    print(f"Max latency: {max(load_latencies):.4f}s")

    if load_failures > 0:
        failed.append("Rapid request failures")

    if max(load_latencies) > 5:
        print("⚠️ Max latency above 5s. Still under official 30s maybe, but should optimize.")
    else:
        print("✅ Latency excellent under 5s")

    print("=" * 90)
    if failed:
        print(f"❌ Failed reliability checks: {failed}")
    else:
        print("✅ All reliability checks passed!")
    print("=" * 90)


if __name__ == "__main__":
    main()
