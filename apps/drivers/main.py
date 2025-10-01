import os, time, json, uuid

OUTBOX = os.getenv("QUEUE_OUTBOX", "/queue/outbox")
DRIVER_OUT = os.getenv("DRIVER_OUT", "/queue/driver_out")
POLL_MS = int(os.getenv("POLL_INTERVAL_MS", "500"))

os.makedirs(OUTBOX, exist_ok=True)
os.makedirs(DRIVER_OUT, exist_ok=True)

print(f"[drivers] up: outbox={OUTBOX} driver_out={DRIVER_OUT} interval={POLL_MS}ms", flush=True)

def process_invoke(path):
    try:
        with open(path, "r") as f:
            msg = json.load(f)
    except Exception as e:
        print(f"[drivers] read error {path}: {e}", flush=True)
        return

    # stub execution: echo
    result = {
        "id": msg.get("id") or str(uuid.uuid4()),
        "type": "result",
        "pipelineId": msg.get("pipelineId"),
        "status": "ok",
        "from": "drivers-stub",
        "triggerType": msg.get("triggerType"),
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
        "payload": {"note": "stub driver executed"},
    }
    out_path = os.path.join(DRIVER_OUT, f"{result['id']}.json")
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    # keep original invoke for audit

def scan_once():
    for name in os.listdir(OUTBOX):
        if not name.lower().endswith(".json"):
            continue
        path = os.path.join(OUTBOX, name)
        process_invoke(path)

if __name__ == "__main__":
    while True:
        scan_once()
        time.sleep(POLL_MS / 1000.0)
