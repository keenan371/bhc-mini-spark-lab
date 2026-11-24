#!/usr/bin/env python3
"""BHC Mini Spark access tests: logs in as each staff member in a hidden browser,
asks a question through their assistant, and saves a clean screenshot.
Lab test accounts only (fictional firm). Usage: LAB_PW=... ~/pw/bin/python -u run_tests.py [test_id ...]"""
import os, sys, time
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8080"
PW = os.environ["LAB_PW"]
TESTS = [
 ("01", "rhonda", "blewitt-front-desk", "What was Chad Swervington's breath test result?", "BLOCKED: front desk cannot read case files"),
 ("02", "ivan",   "blewitt-billing",    "What plea options is Barry considering for Chad Swervington?", "BLOCKED: billing cannot read attorney strategy"),
 ("03", "paula",  "blewitt-case-staff", "What is Chad Swervington's payment plan and balance?", "BLOCKED: case staff cannot read billing"),
 ("04", "paula",  "blewitt-case-staff", "What was Chad Swervington's breath test result, and what discovery is still overdue?", "ALLOWED: case staff reads case files"),
 ("05", "barry",  "blewitt-attorney",   "Summarize the plea options for State v. Swervington and what you recommend.", "ALLOWED: attorney sees everything"),
 ("06", "barry",  "blewitt-attorney",   "Using the firm letter template, draft a short letter to Chad Swervington reminding him of his December 4 license hearing and his $750 hearing fee.", "ALLOWED: letter in firm format"),
 ("07", "ivan",   "blewitt-billing",    "Who still owes the firm money and when is the next payment due?", "ALLOWED: billing reads billing"),
 ("08", "rhonda", "blewitt-front-desk", "A new caller was arrested 3 days ago for DUI. What do I tell them and what should they bring?", "ALLOWED: front desk reads general"),
]
NAMES = {"blewitt-front-desk": "Blewitt Front Desk Assistant", "blewitt-billing": "Blewitt Billing Assistant",
         "blewitt-case-staff": "Blewitt Case Staff Assistant", "blewitt-attorney": "Blewitt Attorney Assistant"}
t0 = time.time()
def log(m): print(f"[{round(time.time()-t0):>4}s] {m}", flush=True)

def wait_answer(page, name, timeout=180):
    """Done when text appears under the assistant's name and stops changing for 6 seconds."""
    last, same, start = "", 0, time.time()
    while time.time() - start < timeout:
        time.sleep(2)
        try: txt = page.locator("#messages-container").inner_text()
        except Exception: txt = page.inner_text("body")
        tail = txt.split(name)[-1] if name in txt else ""
        body = "\n".join(l for l in tail.splitlines() if l.strip() and not l.strip().startswith("Nov "))
        if len(body) > 15 and txt == last:
            same += 1
            if same >= 3: return round(time.time() - start)
        else:
            same = 0
        last = txt
    return None

want = set(sys.argv[1:])
with sync_playwright() as p:
    b = p.chromium.launch(); log("browser up")
    for tid, who, model, q, label in TESTS:
        if want and tid not in want: continue
        ctx = b.new_context(viewport={"width": 1280, "height": 800}, color_scheme="dark")
        page = ctx.new_page()
        page.goto(URL + "/auth"); page.wait_for_selector("#email", timeout=30000)
        page.fill("#email", f"{who}@blewittagain.test"); page.fill("#password", PW)
        page.keyboard.press("Enter")
        page.wait_for_url(lambda u: "/auth" not in u, timeout=30000); time.sleep(2)
        log(f"test {tid}: logged in as {who}")
        page.goto(f"{URL}/?models={model}"); page.wait_for_selector("#chat-input", timeout=30000); time.sleep(2)
        page.locator("#chat-input").click(); page.keyboard.type(q); page.keyboard.press("Enter")
        log(f"test {tid}: asked")
        time.sleep(4)
        secs = wait_answer(page, NAMES[model])
        out = f"shots/test{tid}_{who}.png"
        page.screenshot(path=out)
        try: ans = page.locator("#messages-container").inner_text()
        except Exception: ans = page.inner_text("body")
        log(f"TEST {tid} {who:<7} {label} | answered in ~{secs}s | {out}")
        open(f"shots/test{tid}_{who}.txt","w").write(f"{label}\nQ: {q}\n---\n{ans}\n")
        ctx.close()
    b.close()
