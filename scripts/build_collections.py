#!/usr/bin/env python3
"""BHC: build document collections + one assistant per group in Open WebUI.
Reads collections.json. Uploads each folder's files into its collection, sets which
groups can read it, then creates one assistant per group with only that group's
collections attached. Safe to re-run (skips what exists).
Usage: OWUI_TOKEN=... python3 build_collections.py collections.json
"""
import json, os, sys, time, uuid, urllib.request

BASE = os.environ.get("OWUI_URL", "http://127.0.0.1:8080")
TOKEN = os.environ["OWUI_TOKEN"]
cfg = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "collections.json"))

def api(method, path, body=None, raw=None, ctype="application/json"):
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    req = urllib.request.Request(BASE + path, method=method, data=data,
          headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": ctype})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read() or "null")

def upload(path):
    b = uuid.uuid4().hex
    name = os.path.basename(path)
    body = (f"--{b}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{name}\"\r\n"
            f"Content-Type: text/plain\r\n\r\n").encode() + open(path, "rb").read() + f"\r\n--{b}--\r\n".encode()
    return api("POST", "/api/v1/files/?process=true", raw=body, ctype=f"multipart/form-data; boundary={b}")

def grants(group_names):
    return [{"principal_type": "group", "principal_id": groups[g], "permission": "read"} for g in group_names]

groups = {g["name"]: g["id"] for g in api("GET", "/api/v1/groups/")}
existing = api("GET", "/api/v1/knowledge/")
existing = existing.get("items", existing) if isinstance(existing, dict) else existing
kb = {k["name"]: k["id"] for k in existing}

for cname, c in cfg["collections"].items():
    have = set()
    if cname in kb:
        print(f"collection exists   {cname}")
        api("POST", f"/api/v1/knowledge/{kb[cname]}/access/update", {"access_grants": grants(c["read"])})
        fl = api("GET", f"/api/v1/knowledge/{kb[cname]}/files")
        fl = fl.get("items", fl) if isinstance(fl, dict) else fl
        have = {x.get("filename") or x.get("meta", {}).get("name") for x in fl}
    else:
        k = api("POST", "/api/v1/knowledge/create", {"name": cname, "description": f"Blewitt {cname} documents", "access_grants": grants(c["read"])})
        kb[cname] = k["id"]
        print(f"collection created  {cname}  (read: {', '.join(c['read'])})")
    for f in sorted(os.listdir(c["folder"])):
        if f in have: continue
        fobj = upload(os.path.join(c["folder"], f))
        for _ in range(60):
            st = api("GET", f"/api/v1/files/{fobj['id']}/process/status")
            if st.get("status") in ("completed", "failed"): break
            time.sleep(2)
        api("POST", f"/api/v1/knowledge/{kb[cname]}/file/add", {"file_id": fobj["id"]})
        print(f"    + {f}  [{st.get('status')}]")

models = {m["id"] for m in api("GET", "/api/v1/models/all")}
# Staff need read access to the engine behind their assistant; keep it hidden from their menu.
all_groups = sorted({a["group"] for a in cfg["assistants"].values()})
base = {"id": cfg["base_model"], "base_model_id": None, "name": cfg["base_model"],
        "meta": {"hidden": True, "description": "Engine behind the assistants (hidden from staff)"},
        "params": {}, "access_grants": grants(all_groups), "is_active": True}
if cfg["base_model"] in models:
    api("POST", f"/api/v1/models/model/update?id={cfg['base_model']}", base)
else:
    api("POST", "/api/v1/models/create", base)
print(f"engine  {cfg['base_model']}  hidden, usable by: {', '.join(all_groups)}")
for mid, a in cfg["assistants"].items():
    form = {"id": mid, "base_model_id": cfg["base_model"], "name": a["name"],
            "meta": {"description": f"{a['group']} assistant", "profile_image_url": "/static/favicon.png",
                     "knowledge": [{"type": "collection", "id": kb[n], "name": n} for n in a["knowledge"]]},
            "params": {"system": cfg["system_prompt"], "function_calling": "legacy", "num_ctx": 8192},
            "access_grants": grants([a["group"]]), "is_active": True}
    if mid in models:
        api("POST", f"/api/v1/models/model/update?id={mid}", form); print(f"assistant updated   {a['name']}")
    else:
        api("POST", "/api/v1/models/create", form); print(f"assistant created   {a['name']}")
    print(f"    group: {a['group']}  sees: {', '.join(a['knowledge'])}")
