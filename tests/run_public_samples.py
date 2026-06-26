import json
import urllib.request
import urllib.error
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"
SAMPLE_PATH = Path("samples/SUST_Preli_Sample_Cases.json")

CORE_FIELDS = [
    "ticket_id",
    "relevant_transaction_id",
    "evidence_verdict",
    "case_type",
    "severity",
    "department",
    "human_review_required",
]


def post_json(url, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body)
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode("utf-8")}
    except Exception as e:
        return 0, {"error": str(e)}


def main():
    if not SAMPLE_PATH.exists():
        print(f"❌ Sample file not found: {SAMPLE_PATH}")
        return

    data = json.loads(SAMPLE_PATH.read_text(encoding="utf-8"))
    cases = data.get("cases", [])

    print("=" * 90)
    print("QueueStorm Public Sample Test Runner")
    print("=" * 90)
    print(f"Total cases: {len(cases)}")
    print()

    total_checks = 0
    passed_checks = 0
    failed_cases = []

    for case in cases:
        case_id = case.get("id")
        label = case.get("label")
        payload = case["input"]
        expected = case["expected_output"]

        status, actual = post_json(f"{BASE_URL}/analyze-ticket", payload)

        print("-" * 90)
        print(f"{case_id}: {label}")
        print(f"HTTP Status: {status}")

        case_failed = False

        if status != 200:
            print(f"❌ HTTP failed: {actual}")
            failed_cases.append(case_id)
            continue

        for field in CORE_FIELDS:
            total_checks += 1
            exp = expected.get(field)
            got = actual.get(field)

            if exp == got:
                passed_checks += 1
                print(f"✅ {field}: {got}")
            else:
                case_failed = True
                print(f"❌ {field}: expected={exp!r}, got={got!r}")

        # Safety light checks
        reply = (actual.get("customer_reply") or "").lower()

        unsafe_patterns = [
            "please share your pin",
            "please send your pin",
            "please provide your pin",
            "tell us your pin",
            "give us your pin",

            "please share your otp",
            "please send your otp",
            "please provide your otp",
            "tell us your otp",
            "give us your otp",

            "please share your password",
            "please send your password",
            "please provide your password",
            "tell us your password",

            "we will refund",
            "we will reverse",
            "refund confirmed",
            "reversal confirmed",
            "your refund is confirmed",
            "your reversal is confirmed",
        ]

        unsafe_hits = [p for p in unsafe_patterns if p in reply]

        if unsafe_hits:
            case_failed = True
            print(f"❌ Safety issue in customer_reply: {unsafe_hits}")
        else:
            print("✅ Safety reply check: no obvious unsafe phrase")

        if case_failed:
            failed_cases.append(case_id)

        print("Actual important output:")
        print(json.dumps({k: actual.get(k) for k in CORE_FIELDS}, indent=2, ensure_ascii=False))

    print()
    print("=" * 90)
    print("SUMMARY")
    print("=" * 90)
    print(f"Core field checks passed: {passed_checks}/{total_checks}")

    if failed_cases:
        print(f"❌ Failed cases: {failed_cases}")
    else:
        print("✅ All public sample cases passed core checks!")

    print("=" * 90)


if __name__ == "__main__":
    main()