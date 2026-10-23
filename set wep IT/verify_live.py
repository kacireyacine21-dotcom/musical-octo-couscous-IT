import json
import urllib.request
import urllib.error

payload = json.dumps({"message": "مرحبا"}).encode("utf-8")
req = urllib.request.Request(
    "http://127.0.0.1:5000/api/chat",
    data=payload,
    headers={"Content-Type": "application/json"},
    method="POST",
)

try:
    with urllib.request.urlopen(req, timeout=60) as resp:
        print("STATUS", resp.status)
        print(resp.read().decode("utf-8"))
except Exception as exc:
    print(type(exc).__name__, exc)
    if isinstance(exc, urllib.error.HTTPError):
        print(exc.read().decode("utf-8", "ignore"))
