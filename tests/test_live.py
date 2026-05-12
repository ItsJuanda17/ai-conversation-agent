"""Live integration test: hits the real running server with real OpenAI calls."""
import requests, json, sys, time

BASE = "http://127.0.0.1:8000"
PASS = 0
FAIL = 0

def report(name, ok, detail=""):
    global PASS, FAIL
    status = "PASS" if ok else "FAIL"
    if ok:
        PASS += 1
    else:
        FAIL += 1
    print(f"  [{status}] {name}")
    if detail:
        print(f"         {detail}")

print("=" * 60)
print("LIVE INTEGRATION TESTS")
print("=" * 60)

# 1. Health
print("\n--- Test 1: GET /health ---")
try:
    r = requests.get(f"{BASE}/health", timeout=5)
    report("/health", r.status_code == 200 and r.json().get("status") == "ok",
           f"status={r.status_code} body={r.json()}")
except Exception as e:
    report("/health", False, str(e))

# 2. Emotions (calls OpenAI LLM)
print("\n--- Test 2: POST /analisis/emociones (LLM) ---")
try:
    r = requests.post(f"{BASE}/analisis/emociones",
                      json={"query": "reforma", "limit": 3}, timeout=60)
    data = r.json()
    ok = r.status_code == 200 and data.get("total_comments", 0) > 0
    report("/analisis/emociones", ok,
           f"status={r.status_code} total={data.get('total_comments')} "
           f"emotions={data.get('emotion_distribution')}")
    if data.get("comments"):
        c = data["comments"][0]
        print(f"         sample: emotion={c.get('emotion')} text={c.get('text','')[:80]}...")
except Exception as e:
    report("/analisis/emociones", False, str(e))

# 3. Thread summary (calls OpenAI LLM)
print("\n--- Test 3: POST /analisis/resumen (LLM) ---")
try:
    r = requests.post(f"{BASE}/analisis/resumen",
                      json={"thread_id": "tikapi_7520430294948793606", "limit": 5}, timeout=60)
    data = r.json()
    ok = r.status_code == 200 and "representative_messages" in data
    report("/analisis/resumen", ok,
           f"status={r.status_code} total_messages={data.get('total_messages')} "
           f"sentiments={data.get('sentiment_distribution')}")
    msgs = data.get("representative_messages", [])
    if msgs:
        print(f"         summary[0]: {msgs[0][:120]}...")
except Exception as e:
    report("/analisis/resumen", False, str(e))

# 4. Propagation (no LLM needed)
print("\n--- Test 4: POST /analisis/propagacion ---")
try:
    r = requests.post(f"{BASE}/analisis/propagacion",
                      json={"root_id": "106064209472141_767905085584441", "max_depth": 3}, timeout=30)
    data = r.json()
    ok = r.status_code == 200 and "metrics" in data
    report("/analisis/propagacion", ok,
           f"status={r.status_code} root_found={data.get('root_found')} "
           f"descendants={data.get('total_descendants')} "
           f"depth={data.get('max_depth_observed')}")
    m = data.get("metrics", {})
    if m:
        print(f"         metrics: reach={m.get('reach')} authors={m.get('unique_authors')} "
              f"replies/hr={m.get('average_replies_per_hour')}")
except Exception as e:
    report("/analisis/propagacion", False, str(e))

# 5. Validation errors
print("\n--- Test 5: Validation (422) ---")
try:
    r = requests.post(f"{BASE}/analisis/emociones", json={"limit": 5}, timeout=5)
    report("missing query -> 422", r.status_code == 422, f"status={r.status_code}")
except Exception as e:
    report("validation", False, str(e))

print("\n" + "=" * 60)
print(f"RESULTS: {PASS} passed, {FAIL} failed out of {PASS+FAIL} tests")
print("=" * 60)

sys.exit(1 if FAIL > 0 else 0)
