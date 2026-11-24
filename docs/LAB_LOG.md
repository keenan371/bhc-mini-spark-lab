# BHC Mini Spark Lab – Lab Log

Simulated in-office private AI box (like an NVIDIA DGX Spark) for the fictional law firm
**Blewitt, Again & Associates LLP** ("Bad decisions. Excellent representation.").

- VM: `bhc-mini-spark` (C:\VirtualMachines\bhc-mini-spark), Ubuntu Server 24.04.4
- Problems 1–14 are in Notion: "BHC Mini Spark Lab Notes" → "07 | Problems & Fixes". This log continues from #15.
- How to pick up after a reboot: see `RESUME.md` in this folder.

---

## 2026-11-24 – Step 0: Verify the host fix (BLOCKED)

**Commands run (on Windows):**
```
systeminfo | findstr /i "hypervisor"
VBoxManage list runningvms
VBoxManage showvminfo bhc-mini-spark --machinereadable   (state, CPUs, memory)
```
Plus some read-only checks: Device Guard / VBS status, the HVCI registry value, and the Hyper-V services.

**Output summary:**
- `systeminfo` says: "A hypervisor has been detected."
- The VM is powered off at 2 CPUs / 4096 MB. No VMs are running.
- Windows last booted at 8:06 AM today, so the restart did happen.
- Memory Integrity (HVCI) = 0 (off).
- Virtualization-Based Security status = 2 (**running**). The HvHost service is running.
- `bcdedit` and `Get-WindowsOptionalFeature` need an admin shell, so they were not checked.

**Result:** Stopped as instructed. The VM was not started and nothing was changed.

### Problem 15 – Windows hypervisor still on after restart
- **Problem:** After the restart, `systeminfo` still says "A hypervisor has been detected." Memory Integrity is off (HVCI=0), but Virtualization-Based Security (VBS) is still running (status 2) and the HvHost service is running. VirtualBox falls back to slow NEM / "turtle" mode.
- **Fix:** In an admin PowerShell, run:
  ```
  bcdedit /set hypervisorlaunchtype off
  reg add "HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard" /v EnableVirtualizationBasedSecurity /t REG_DWORD /d 0 /f
  ```
  Then restart. VirtualMachinePlatform and WSL were already disabled earlier (Problem 12).
- **Fallback:** If the hypervisor still won't turn off, keep going in slow mode. The Ubuntu install already succeeded that way.
- Also logged in Notion → 07 | Problems & Fixes (#15).

---

## 2026-11-24 – Resume: Step 0 again + sample documents

**Lab guide:** now on disk as `LAB_GUIDE_README.md` in this folder. RESUME.md points to it.
Two leftover "POLK LEGAL GROUP" lines in Appendix A (the letter template header and the SOP title) were changed to "BLEWITT, AGAIN & ASSOCIATES LLP".

**Step 0 commands:** `systeminfo | findstr /i hypervisor`, Device Guard status, `VBoxManage startvm bhc-mini-spark --type headless`, then searched `VBox.log` for NEM.
- Still "A hypervisor has been detected". Boot time is unchanged (8:06 AM), so the admin fix from #15 + restart has not been done yet.
- VBox.log: `HM: HMR3Init: Attempting fall back to NEM: VT-x is not available`, so the VM runs in slow mode.
- Decision: kept 2 CPUs / 4 GB (per the plan, the size only goes up if the hypervisor is gone) and continued.

### Problem 16 – Continuing in slow (NEM) mode
- **Problem:** The #15 fix wasn't applied before resuming, so VirtualBox still runs on top of Windows' hypervisor (NEM / turtle mode). Installs and model pulls will be slower.
- **Fix / plan:** Keep going at 2 CPUs / 4 GB. Run long jobs in the background and poll them (see #14). Apply the #15 fix (bcdedit + VBS registry value + restart) before recording, then raise the VM to 4 CPUs / 6 GB.

**Sample documents** (from Appendix A) written to `C:\VirtualMachines\bhc-mini-spark\sample-data\`:
- `general\`: Firm_Letter_Template.txt, Office_Procedures_SOP.txt, New_Client_Intake_Checklist.txt
- `attorney-only\`: Intake_Packet_Smith_Estate.txt, Trust_Draft_Johnson_Family.txt, Engagement_Terms_Rivera.txt
- Checked: 6 files, 0 "Polk" mentions.


## 2026-11-24 – Section 02: Base server (Guide Step 4)

SSH came up about 1 minute after boot (first load average 5.10).

**Commands run (over SSH, in the background with nohup, output in `~/s02.log`):**
```
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y curl ufw unattended-upgrades docker.io
sudo usermod -aG docker bhcadmin
sudo systemctl enable --now docker
docker run --rm hello-world      # in a new SSH session so the docker group applies
```
**Output summary:**
- Install finished OK (`S02_DONE`). Docker version 29.1.3 (Ubuntu package 29.1.3-0ubuntu3~24.04.2).
- `systemctl is-active docker` = active.
- bhcadmin's groups now include `docker`.
- `hello-world` printed "Hello from Docker!".

**Problems:** none.


## 2026-11-24 – Section 03 (partial) + Section 04 started, then paused for a host restart

**Commands run (in the background on the VM, logs in `~/s03.log`, `~/s03b.log`, `~/s03c.log`, `~/s04.log`):**
```
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen3:4b-instruct-2507                        # failed, see #17 and #18
ollama pull qwen3:4b-instruct-2507-q4_K_M                 # in progress when paused
ollama cp qwen3:4b-instruct-2507-q4_K_M qwen3:4b-instruct-2507   # not run yet
ollama pull qwen2.5:3b                                    # not run yet
docker run -d --network=host -v open-webui:/app/backend/data -e OLLAMA_BASE_URL=http://127.0.0.1:11434 --name open-webui --restart always ghcr.io/open-webui/open-webui:main   # image pull in progress when paused
```
**Output summary:**
- Ollama 0.40.18 installed as a systemd service, running CPU-only (no GPU, expected).
- `ss -tlnp` shows `127.0.0.1:11434` only. Good: not reachable from outside the VM.
- Disk 9.8G of 59G used. RAM 3.8 GiB total.
- The model pulls and the Open WebUI image pull were **not finished**.

### Problem 17 – First pull ran before the Ollama server was ready
- **Problem:** "could not connect to ollama server". The install script returned before the service finished starting (slow mode).
- **Fix:** Wait for `curl http://127.0.0.1:11434/api/version` to answer, then pull.

### Problem 18 – Model tag `qwen3:4b-instruct-2507` not found
- **Problem:** "pull model manifest: file does not exist". The registry returns 404 for the bare tag.
- **Fix:** The registry has `qwen3:4b-instruct-2507-q4_K_M` (200). Pull that and `ollama cp` it to the guide's name.

### Problem 19 – Two big downloads at once starved SSH in slow mode
- **Problem:** With the model pull and the Open WebUI image pull running together, SSH stopped answering ("timed out during banner exchange", "connection reset by peer"). The VirtualBox process sat at high CPU.
- **Fix:** Stopped the polling, shut the VM down with `VBoxManage controlvm bhc-mini-spark acpipowerbutton` (SSH was too busy for `shutdown -h now`), and paused for the host restart with fix #15 applied. Next time: one download at a time, and poll every 60 s.

**Paused for the Windows restart.** See `RESUME.md` → "WHERE WE ARE".


## 2026-11-24 (afternoon) – After the host restart: fast mode, finish Sections 03–05

### Step 0 again – hypervisor OFF
- Keenan applied fix #15 and restarted. VBox.log now says `HM: Using VT-x implementation 3.0` (**fast mode**, no NEM fallback).
- Shut the VM down cleanly (`sudo shutdown -h now`, off in 5 s), then: `VBoxManage modifyvm bhc-mini-spark --cpus 4 --memory 6144`.
- Started headless. **SSH answered in about 10 s** (before, it was minutes). The guest sees 4 CPUs and 5.8 GiB RAM.
- The models and the Open WebUI image from the morning were not on disk (the downloads never finished).

### Section 03 – Models (one download at a time)
One script, `~/finish.sh`, ran each step after the one before, logging to `~/finish.log` and polled every 60 s:
```
until curl -s http://127.0.0.1:11434/api/version; do sleep 2; done
ollama pull qwen3:4b-instruct-2507-q4_K_M
ollama cp qwen3:4b-instruct-2507-q4_K_M qwen3:4b-instruct-2507
ollama pull qwen2.5:3b
docker pull ghcr.io/open-webui/open-webui:main
docker run -d --network=host -v open-webui:/app/backend/data -e OLLAMA_BASE_URL=http://127.0.0.1:11434 --name open-webui --restart always ghcr.io/open-webui/open-webui:main
```
**Result (2nd run, after the #20 fix):** model 1 took about 2 min, model 2 about 1.5 min, the Open WebUI image about 3 min. Everything was done in about 7 minutes.
`ollama list`: `qwen3:4b-instruct-2507` (2.5 GB), `qwen3:4b-instruct-2507-q4_K_M` (same file, the ID 0edcdef34593 matches), `qwen2.5:3b` (1.9 GB).
- Quick test: `ollama run qwen2.5:3b "In one sentence, what is attorney-client privilege?"` gave a correct one-sentence answer in about 25 s.
- `sudo ss -tlnp | grep 11434` shows `127.0.0.1:11434` only. Good.

### Problem 20 – Stale half-download from the interrupted pull
- **Problem:** `ollama pull` failed straight away (and again on retry) with "Error: remove .../blobs/sha256-85e4a5b7…-partial-0: no such file or directory". The morning's interrupted download left a broken partial file (`-partial` plus `-partial-4`, but no `-partial-0`).
- **Fix:** `sudo systemctl stop ollama`, then moved (not deleted) the two leftover `sha256-85e4a5b7…-partial*` files to `/var/backups/ollama-stale-partials/`, then `sudo systemctl start ollama` and re-ran the script. The pull started fresh and worked.
- **Lesson:** if a model download gets cut off, Ollama may not resume it cleanly. Move the `*-partial*` files for that blob out of the way and pull again.

### Section 04 – Open WebUI
- Container `open-webui` is up with 0 restarts. Docker showed "unhealthy" for the first ~2 minutes while the app was still starting, then "healthy". That was expected, not a problem.
- **From Windows:** `http://localhost:8080` returns 200, page title "Open WebUI", version **0.13.4**. `/api/config` says `"onboarding": true`, so **no admin account exists yet. That's left for Keenan to create on camera**, as planned.
- Ollama's model list (what Open WebUI reads) shows all three model names.
- Users, groups, knowledge collections and assistants (guide Steps 7–10) are **not done**. They're left for Keenan on camera. The 6 documents are ready in `C:\VirtualMachines\bhc-mini-spark\sample-data\`.

### Section 05 – Lockdown
```
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 8080/tcp
sudo ufw --force enable
printf 'APT::Periodic::Update-Package-Lists "1";\nAPT::Periodic::Unattended-Upgrade "1";\n' | sudo tee /etc/apt/apt.conf.d/20auto-upgrades
sudo systemctl enable --now unattended-upgrades
```
- `ufw status verbose`: active. Default deny incoming, allow outgoing, deny routed. The only allow rules are 22/tcp and 8080/tcp (IPv4 + IPv6).
- `20auto-upgrades` has `"1"` on both lines. The unattended-upgrades service is enabled and active.
- `/etc/motd` is now the BHC banner: `BlueHippoCyber // LOCAL AI DEPLOYMENT LAB // bhc-mini-spark` / `LOCAL AI | ON-PREM | NO CLOUD | FULL CONTROL`. The old file was kept as `/etc/motd.bak-pre-banner` if one existed.
- Note: Open WebUI uses `--network=host`, so ufw covers port 8080 directly. (The well-known "Docker skips ufw" problem applies to `-p` port publishing, which this setup doesn't use.)

### Snapshot
- Shut down cleanly (off in 12 s), then `VBoxManage snapshot bhc-mini-spark take 05-ready-for-recording` (taken **powered off**). UUID 1e8b05cd-d334-4996-953c-033a2655a68e.
- Snapshot tree: `01-clean-install` → `05-ready-for-recording` (current).

### Reboot test (after the snapshot)
- Started headless again. Open WebUI came back by itself in about 85 s (200 from Windows). `ollama list` shows all models, ufw is active, and the container is healthy.
- **The VM is left running** so it's ready for recording.

### Other
- Added a bhc-mini-spark row to `07_BHC_LABS-VMS\06_VIRTUAL_MACHINES\README.md`.

**DONE:** Open WebUI loads at localhost:8080 ✔ · models listed ✔ · firewall on ✔ · auto-updates on ✔ · banner ✔ · snapshot 05 ✔ · log ✔.


## 2026-11-24 – Client brief added + guide updated to the 4-staff DUI firm

**Why:** The new Client Brief (4 staff, DUI defense) didn't match the guide (2 staff, estate/probate documents). Keenan asked for the guide's Steps 8–12 and the sample documents to match the brief.

**Changes (no VM changes; the VM build steps are unchanged):**
- `LAB_GUIDE_README.md` and `RESUME.md`: new **Client Brief + Finish Line** section at the top (also in Notion "00 | Lab Overview & Environment").
- `LAB_GUIDE_README.md` Steps 8–10 rewritten:
  - 4 users: Barry Blewitt, Paula Paralegal, Rhonda Reception, Ivan Ignition (all `@blewittagain.test`, role user)
  - 4 groups: `Attorney_Only`, `Case_Staff`, `Front_Desk`, `Billing`
  - 4 collections, one per group:
    - General → shared with all 4 groups
    - Case Files → Case_Staff + Attorney_Only
    - Billing → Billing + Attorney_Only
    - Attorney Only → Attorney_Only
  - 4 assistants, one per group: Front Desk, Case Staff, Billing, Attorney
- **Step 12:** a new 9-test table:
  - Rhonda only sees her own assistant.
  - Rhonda is blocked from case files.
  - Ivan is blocked from the plea memo.
  - Paula is blocked from the fee agreement.
  - Paula *can* read case files.
  - Barry sees all.
  - Barry gets a letter in firm format.
  - Wi-Fi off still answers.
  - Admin sees the chat history.
- Section 0 summary, diagram, Step 13 recording outline and a troubleshooting row updated to match. No "Adam", "Smith", "Johnson", "Rivera" or "Standard_Staff" mentions are left.
- **Appendix A** is rebuilt from the actual files on disk, so the guide and the files match word for word.
- **Sample documents:** the old 6 estate documents were moved (not deleted) to `C:\VirtualMachines\bhc-mini-spark\sample-data\_old\`. The 7 new fictional DUI documents:
  - `general\`: Firm_Letter_Template.txt (with the slogan), Front_Desk_Phone_Script.txt, Office_Procedures_SOP.txt
  - `case-files\`: DUI_Client_Intake_Chad_Swervington.txt, Breathalyzer_Calibration_Records_Request.txt
  - `attorney-only\`: Plea_Options_Memo_State_v_Swervington.txt
  - `billing\`: Fee_Agreement_Swervington.txt
- **Leak check (so the access tests are fair):**
  - The fee amounts appear only in the fee agreement.
  - The plea strategy appears only in the plea memo.
  - The breath-test results appear only in the case files.
  - The general documents carry no case facts and no fees.
  - No real people, no crash and no injured people, so there are no victims in the story.
- Notion "04 | Open WebUI + Blewitt" and "06 | Tests + Recording" updated to match.

**Problems:** one small one on my side. Building Appendix A with PowerShell first wrote the code fences as "```n" (a backtick escaping slip). Fixed with sed, and the fence count checked even (50). Not a lab problem, so it isn't numbered.

