"""Quick smoke test of all pages and API endpoints."""
import urllib.request, json, sys

BASE = "http://localhost:5000"
PASS = "\033[32m✓\033[0m"
FAIL = "\033[31m✗\033[0m"
errors = []

def check(label, url, method="GET", body=None, expect=(200,201)):
    try:
        data = json.dumps(body).encode() if body else None
        req  = urllib.request.Request(url, data=data,
               headers={"Content-Type":"application/json"}, method=method)
        with urllib.request.urlopen(req, timeout=5) as r:
            status = r.status
    except urllib.error.HTTPError as e:
        status = e.code
    except Exception as e:
        print(f"  {FAIL} {label}: {e}")
        errors.append(label); return

    ok = status in expect
    print(f"  {PASS if ok else FAIL} {label}: {status}")
    if not ok: errors.append(label)

print("\n── Pages ──────────────────────────────────")
check("Dashboard",    f"{BASE}/dashboard")
check("Quests",       f"{BASE}/quests")
check("Skills",       f"{BASE}/skills")
check("Achievements", f"{BASE}/achievements")
check("Modules",      f"{BASE}/modules")
check("Analytics",    f"{BASE}/analytics")
check("Career Hunter",f"{BASE}/modules/career_hunter")
check("Health",       f"{BASE}/health")

print("\n── Player API ──────────────────────────────")
check("GET player",        f"{BASE}/api/player/1")
check("GET stats",         f"{BASE}/api/player/1/stats")
check("GET skills",        f"{BASE}/api/player/1/skills")
check("GET achievements",  f"{BASE}/api/player/1/achievements")
check("GET notifications", f"{BASE}/api/player/1/notifications")
check("GET analytics",     f"{BASE}/api/player/1/analytics?days=7")
check("POST generate daily", f"{BASE}/api/player/1/quests/generate-daily", "POST", {})

print("\n── Quest API ───────────────────────────────")
check("GET quests",        f"{BASE}/api/quests?player_id=1")
check("GET daily quests",  f"{BASE}/api/quests/daily?player_id=1")

print("\n── Module API ──────────────────────────────")
check("GET modules",       f"{BASE}/api/modules?player_id=1")
check("GET career dashboard", f"{BASE}/api/modules/career_hunter/dashboard?player_id=1")

print("\n── Career API ──────────────────────────────")
check("GET jobs",          f"{BASE}/api/career/jobs?player_id=1")
check("GET applications",  f"{BASE}/api/career/applications?player_id=1")

print(f"\n{'─'*45}")
if errors:
    print(f"\033[31m{len(errors)} failures: {', '.join(errors)}\033[0m")
    sys.exit(1)
else:
    print(f"\033[32mAll checks passed!\033[0m")
