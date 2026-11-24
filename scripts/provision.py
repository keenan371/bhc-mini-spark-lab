#!/usr/bin/env python3
"""BHC staff provisioner for Open WebUI (like a Microsoft 365 bulk import).
Reads staff.csv (name,email,role,group), creates any missing users and groups,
and puts each person in their group. Safe to re-run: it skips what already exists.
Usage:  OWUI_TOKEN=... START_PASSWORD=... python3 provision.py staff.csv
"""
import csv, json, os, sys, urllib.request

BASE = os.environ.get("OWUI_URL", "http://127.0.0.1:8080")
TOKEN = os.environ["OWUI_TOKEN"]
START_PW = os.environ.get("START_PASSWORD")

def api(method, path, body=None):
    req = urllib.request.Request(BASE + path, method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read() or "null")

rows = list(csv.DictReader(open(sys.argv[1] if len(sys.argv) > 1 else "staff.csv")))

# Users
users, page = {}, 1
while True:
    batch = api("GET", f"/api/v1/users/?page={page}")["users"]
    if not batch: break
    users.update({u["email"].lower(): u["id"] for u in batch}); page += 1
for r in rows:
    e = r["email"].lower()
    if e in users:
        print(f"user  exists   {e}")
    elif not START_PW:
        print(f"user  MISSING  {e} (set START_PASSWORD to create)")
    else:
        u = api("POST", "/api/v1/auths/add", {"name": r["name"], "email": e,
                 "password": START_PW, "role": r.get("role") or "user"})
        users[e] = u["id"]; print(f"user  created  {e}")

# Groups + membership
groups = {g["name"]: g["id"] for g in api("GET", "/api/v1/groups/")}
for gname in sorted({r["group"] for r in rows}):
    if gname not in groups:
        groups[gname] = api("POST", "/api/v1/groups/create",
                            {"name": gname, "description": ""})["id"]
        print(f"group created  {gname}")
    else:
        print(f"group exists   {gname}")
    ids = [users[r["email"].lower()] for r in rows
           if r["group"] == gname and r["email"].lower() in users]
    api("POST", f"/api/v1/groups/id/{groups[gname]}/users/add", {"user_ids": ids})
    print(f"      members  {gname}: {len(ids)} added")

# Proof
print("\nCHECK")
for g in api("GET", "/api/v1/groups/"):
    m = api("GET", f"/api/v1/groups/id/{g['id']}/members")
    names = [x.get("name") for x in (m.get("items") or m.get("users") or [])] if isinstance(m, dict) else m
    print(f"  {g['name']:<14} {names}")
