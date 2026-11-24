# Private AI for Law Firms — Open Lab Walkthrough
### Build a "Mini Spark": an in-office private AI box, simulated in a free Ubuntu virtual machine

**By BlueHippoCyber (BHC)** · Version 1.0 · November 2026
*Concept inspired by David Lee (DC CyberSec): packaging private AI with managed IT.*

> **Fictional data. Educational lab only.** Not legal, ethics or compliance advice. Software changes often; if a screen looks different from what's described here, check that tool's current docs.

---

## Client Brief + Finish Line

### Client brief (fictional)
- **Client:** Blewitt, Again & Associates LLP, a small DUI defense firm. Slogan: *"Bad decisions. Excellent representation."*
- **Size:** 4 staff:
  - **Barry Blewitt**: founding attorney
  - **Paula Paralegal**
  - **Rhonda Reception**
  - **Ivan Ignition**: office manager / billing
- **Problem:** Staff paste client files into public ChatGPT. The firm needs AI that stays in the office, with role-based access and an audit trail.
- **BlueHippoCyber's recommendation:** **ONE AI box** (NVIDIA DGX Spark class), right-sized for 2–15 staff. For 15–50 staff, a bigger box or 2 boxes. For 50+, a custom cluster.
- **Lab stand-in:** the VM `bhc-mini-spark`. Same software, smaller model.
- **Price shown to the client:** $2,500 setup + $1,000/month management. The client buys the hardware.

### Finish line: the lab is DONE when all of these are true
1. Open WebUI loads at `localhost:8080`, the models work, the firewall and auto-updates are on, and snapshot `05-ready-for-recording` is taken. *(Claude's job. ✅ Done 2026-11-24.)*
2. Keenan creates the 4 users, 4 groups and the knowledge collections on camera (Section 04).
3. The access test passes:
   - Rhonda is blocked from case files.
   - Ivan is blocked from case strategy (the plea memo).
   - Paula is blocked from fees.
   - Barry sees everything.
   - The admin log shows who asked what.
4. Barry's assistant drafts a client letter in the firm's format.
5. With Wi-Fi off, it still answers.
6. Recorded: one 3-minute demo + a GitHub README. **DONE.**

**Out of scope for this lab (future content):** onboarding / firing / password-reset episodes, clusters, Tailscale.

> ✅ **Updated 2026-11-24:** Steps 8–12 and Appendix A now match this brief (4 staff, 4 groups, 4 collections, 4 assistants, DUI documents). The old estate-planning documents are kept in `sample-data\_old\`.

---

## 0. What you're building (read this first)

Law firms want AI help with drafting and document review, but staff pasting client files into public ChatGPT is a real confidentiality problem. One answer is a **private AI box**: a small computer in the firm's office (like an NVIDIA DGX Spark) that runs the AI on its own. Client files never go to an outside AI service.

A real box costs about $5–7k. **You don't need one to learn this.** In this lab you build a **"Mini Spark"**: a virtual machine (a computer running inside your computer) with Ubuntu Linux, the same family of operating system the DGX Spark uses, running the same kind of software stack. The only real difference is size. Your Mini Spark runs a small AI model; the real box runs much bigger ones.

**By the end you'll have:**
- A private AI chat screen the fake law firm "Blewitt, Again & Associates LLP" can log into
- Four staff accounts in four groups, each seeing only what their job needs:
  - **Barry Blewitt** (attorney) sees everything.
  - **Paula Paralegal** sees general documents and case files.
  - **Rhonda Reception** sees general documents only.
  - **Ivan Ignition** (billing) sees general documents and billing.
- One AI assistant per group that answers from the firm's own documents and drafts letters in the firm's format
- A locked-down server: firewall on, automatic security updates on, no outside AI connected
- Proof: 9 tests you run and screenshot yourself

```
 Your Windows laptop (the "office")
 ┌──────────────────────────────────────────────────────────┐
 │  Web browser  ──►  http://localhost:8080                 │
 │                        │                                 │
 │   ┌────────────────────▼─────────────────────────────┐   │
 │   │  VirtualBox VM: "bhc-mini-spark" (Ubuntu 24.04)  │   │
 │   │   Open WebUI  (staff chat screen, logins, groups)│   │
 │   │       │                                          │   │
 │   │   Ollama  (runs the AI model locally)            │   │
 │   │   Firm docs: general/case/billing/attorney-only  │   │
 │   │   Firewall (UFW) + automatic security updates    │   │
 │   └──────────────────────────────────────────────────┘   │
 └──────────────────────────────────────────────────────────┘
          ✖ No connection to ChatGPT or any outside AI
```

**Time:** about 3–4 hours the first time. **Cost:** $0.

---

## 1. What you need

| Item | Why | Cost |
|---|---|---|
| A Windows 10/11 computer with **16GB RAM or more** | The VM borrows 8GB of it | You have it |
| About **70GB free disk space** | VM disk + AI model | — |
| **Virtualization turned on** | Lets your PC run a VM. Check: Task Manager → Performance → CPU → "Virtualization: Enabled." If it says Disabled, turn on "Intel VT-x" or "AMD-V" in your BIOS. | — |
| **VirtualBox 7** | The program that runs the VM | Free |
| **Ubuntu Server 24.04 LTS** (ISO file) | The operating system for the VM | Free |
| Internet connection (during setup only) | To download software and the AI model | — |
| Optional: free **Tailscale** account | Lets "remote staff" reach the box privately | Free |

**Words you'll see:**
- **VM (virtual machine):** a full computer running in a window on your computer.
- **ISO:** an installer file, like a digital install disc.
- **Terminal:** the text window where you type commands. Type (or paste) a command, then press Enter.
- **`sudo`:** "run this as the administrator." It will ask for your VM password. (You won't see the password as you type; that's normal.)
- **Ollama:** free software that runs AI models on your own machine.
- **Open WebUI:** a free ChatGPT-style screen for Ollama, with logins, groups and document search.
- **Docker:** a tool that runs apps like Open WebUI in a neat, self-contained package.

---

## 2. Suggested repo layout (for your notes)

```
private-ai-law-firm-lab/
├── README.md                 ← this walkthrough
├── sample-data/
│   ├── general/              ← 3 documents everyone can see
│   └── attorney-only/        ← 3 restricted documents
├── screenshots/              ← your proof, numbered by step
└── notes/                    ← your own notes as you go
```

---

## Step 1 — Download the tools (Windows side)

1. Download and install **VirtualBox** from **virtualbox.org** → Downloads → "Windows hosts." Click Next through the installer with the default settings.
2. Download **Ubuntu Server 24.04 LTS** from **ubuntu.com/download/server** (the file ends in `.iso`, about 3GB).

✅ **It worked if:** VirtualBox opens and the `.iso` file is in your Downloads folder.
📸 Screenshot: VirtualBox start screen.

---

## Step 2 — Create the VM

In VirtualBox click **New** and fill in:

| Setting | Value |
|---|---|
| Name | `bhc-mini-spark` |
| ISO Image | the Ubuntu `.iso` you downloaded |
| Check | **"Skip Unattended Installation"** (we'll install it ourselves) |
| Base Memory | **8192 MB** (8GB) |
| Processors | **6** |
| Hard Disk | **60 GB** |

Click **Finish**. Don't start it yet.

**Open the "doors" so your Windows browser can reach the VM:**
Select the VM → **Settings → Network → Adapter 1** (leave it on **NAT**) → **Advanced → Port Forwarding** → click **+** twice and add:

| Name | Protocol | Host Port | Guest Port |
|---|---|---|---|
| ssh | TCP | 2222 | 22 |
| webui | TCP | 8080 | 8080 |

Click OK.

✅ **It worked if:** `bhc-mini-spark` shows in the VirtualBox list, powered off.
📸 Screenshot: the VM's settings summary + port forwarding rules.

> **Why NAT + port forwarding?** The VM is hidden behind your laptop, and only the two doors you opened are reachable, and only from your own computer. That mirrors how a real office box should be closed off.

---

## Step 3 — Install Ubuntu

1. Select the VM → **Start**. Choose **"Try or Install Ubuntu Server."**
2. Go through the installer with mostly default answers:
   - Language: English → keyboard: English (US)
   - Type: **Ubuntu Server** (not minimized)
   - Network: leave the default (it gets an address automatically)
   - Proxy: blank → mirror: default
   - Storage: **Use an entire disk** → default → **Done** → **Continue**
   - Profile: your name: `BHC Admin` · server name: `bhc-mini-spark` · username: `bhcadmin` · pick a password you'll remember
   - Ubuntu Pro: **Skip**
   - **SSH: check "Install OpenSSH server"**
   - Featured snaps: select **nothing** → Done
3. Wait for "Installation complete" → **Reboot Now**. If it says to remove the install disc, just press Enter.
4. Log in with `bhcadmin` and your password.

✅ **It worked if:** you see a prompt like `bhcadmin@bhc-mini-spark:~$`
📸 Screenshot: the login prompt.

**Easier way to type commands (recommended):** the VM window doesn't let you paste. Instead, open **Windows PowerShell** on your laptop and connect into the VM:

```powershell
ssh -p 2222 bhcadmin@localhost
```

Type `yes` the first time, then your password. Now you can copy-paste every command below. (Right-click pastes in PowerShell.)

---

## Step 4 — Update the server and install basics

Run each line, one at a time:

```bash
sudo apt update && sudo apt -y upgrade
sudo apt install -y curl ufw unattended-upgrades docker.io
sudo usermod -aG docker $USER
```

Then log out and back in so the Docker permission takes effect:

```bash
exit
```
```powershell
ssh -p 2222 bhcadmin@localhost
```

Check Docker works:

```bash
docker run --rm hello-world
```

✅ **It worked if:** you see "Hello from Docker!"
📸 Screenshot: the Hello from Docker message.

---

## Step 5 — Install Ollama and the AI model

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen3:4b-instruct-2507
ollama pull qwen2.5:3b
ollama list
```

The first model is about 2.5GB and the second about 2GB, so give it a few minutes.

Quick test (type `/bye` to exit the chat):

```bash
ollama run qwen2.5:3b "In one sentence, what is attorney-client privilege?"
```

Check that Ollama only listens **inside** the box:

```bash
sudo ss -tlnp | grep 11434
```

✅ **It worked if:** `ollama list` shows both models, the test gives an answer, and the last command shows `127.0.0.1:11434`. That means the AI engine isn't reachable from outside the VM.
📸 Screenshot: `ollama list` + the `127.0.0.1:11434` line.

> **Main model:** `qwen3:4b-instruct-2507`. **Backup if it's slow:** `qwen2.5:3b`.

---

## Step 6 — Install Open WebUI (the staff chat screen)

```bash
docker run -d --network=host \
  -v open-webui:/app/backend/data \
  -e OLLAMA_BASE_URL=http://127.0.0.1:11434 \
  --name open-webui --restart always \
  ghcr.io/open-webui/open-webui:main
```

Wait 1–3 minutes, then check it's running:

```bash
docker ps
docker logs --tail 20 open-webui
```

On your **Windows** laptop, open a browser and go to: **http://localhost:8080**

Create the first account. **The first account becomes the administrator** (the IT person who controls everything):
- Name: `BHC Admin` · Email: `admin@blewittagain.test` · a strong password

✅ **It worked if:** you see the chat screen and the model dropdown lists your Qwen models.
📸 Screenshot: Open WebUI home screen with the models showing.

> If the page won't load, wait another minute. The first start downloads extra parts. Still stuck? See Troubleshooting.

---

## Step 7 — Turn off anything that talks to the outside

In Open WebUI: click your name (bottom-left) → **Admin Panel → Settings**:

1. **Connections:** turn **OFF** "OpenAI API." Leave **Ollama API** on (`http://127.0.0.1:11434`).
2. **Web Search:** make sure it's **OFF**.
3. **General → Default User Role:** set to **pending**, so nobody who signs up gets in without admin approval.
4. **Users → Permissions (default permissions):** turn off what staff don't need, e.g. uploading their own files to Knowledge or creating their own models. Exact names vary by version.

✅ **It worked if:** Connections shows only Ollama.
📸 Screenshot: Connections page showing OpenAI OFF.

---

## Step 8 — Create the staff and groups

The firm has 4 people, and each one gets only what their job needs ("need to know").

**Admin Panel → Users → "+"** (add user). You type each password yourself.

| Name | Job | Email | Role |
|---|---|---|---|
| Barry Blewitt | Founding attorney | barry@blewittagain.test | user |
| Paula Paralegal | Paralegal | paula@blewittagain.test | user |
| Rhonda Reception | Front desk | rhonda@blewittagain.test | user |
| Ivan Ignition | Office manager / billing | ivan@blewittagain.test | user |

**Admin Panel → Users → Groups → "+"**: one group per job:

| Group | Member | Can see |
|---|---|---|
| `Attorney_Only` | Barry Blewitt | Everything: general, case files, billing, attorney-only |
| `Case_Staff` | Paula Paralegal | General + case files |
| `Front_Desk` | Rhonda Reception | General only |
| `Billing` | Ivan Ignition | General + billing |

> Everyone keeps the **user** role. The admin account (`BHC Admin`) is the IT person, not a firm employee.

✅ **It worked if:** 4 groups, each with the right member.
📸 Screenshot: the groups list.

---

## Step 9 — Load the firm's documents

The 7 fake documents are in **Appendix A**. On the lab laptop they're already saved in `C:\VirtualMachines\bhc-mini-spark\sample-data\`, in one folder per collection.

In Open WebUI go to **Workspace → Knowledge → "+"** and create **one collection per group**. Set each to **Private**, then share it (read) with the groups shown:

| Collection | Upload these files (folder) | Share with groups |
|---|---|---|
| `Blewitt General` | `Firm_Letter_Template`, `Front_Desk_Phone_Script`, `Office_Procedures_SOP` (`general\`) | Front_Desk, Case_Staff, Billing, Attorney_Only |
| `Blewitt Case Files` | `DUI_Client_Intake_Chad_Swervington`, `Breathalyzer_Calibration_Records_Request` (`case-files\`) | Case_Staff, Attorney_Only |
| `Blewitt Billing` | `Fee_Agreement_Swervington` (`billing\`) | Billing, Attorney_Only |
| `Blewitt Attorney Only` | `Plea_Options_Memo_State_v_Swervington` (`attorney-only\`) | Attorney_Only |

✅ **It worked if:** each collection shows the right files and the right groups.
📸 Screenshot: each collection's access settings.

---

## Step 10 — Build the firm's AI assistants

Build **one assistant per group**. Each assistant can only read the collections listed for it, so nobody can get around the rules with a clever question. (This is more reliable than trusting one assistant to filter.)

**Workspace → Models → "+"**. For all four:
- Base model: `qwen3:4b-instruct-2507`
- Access: **Private**, shared only with the group shown
- System prompt:
```
You are the internal assistant for Blewitt, Again & Associates LLP. Answer only from the firm documents you can access. Always cite the file name you used. Draft letters using Firm_Letter_Template. If the answer is not in the documents, say "I don't know." Never make up client facts.
```

| Assistant | Knowledge | Shared with |
|---|---|---|
| `Blewitt Assistant — Front Desk` | Blewitt General | Front_Desk |
| `Blewitt Assistant — Case Staff` | Blewitt General + Blewitt Case Files | Case_Staff |
| `Blewitt Assistant — Billing` | Blewitt General + Blewitt Billing | Billing |
| `Blewitt Assistant — Attorney` | All four collections | Attorney_Only |

Then go to **Admin Panel → Settings → Models** and hide the raw base models (`qwen3…`, `qwen2.5…`) from regular users. That way staff only see their own firm assistant.

✅ **It worked if:** all four assistants appear in your model list as admin, each with the right knowledge.
📸 Screenshot: each assistant's knowledge + access settings.

---

## Step 11 — Lock down the box

**Firewall:** only allow the two doors we need.

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 8080/tcp
sudo ufw enable
sudo ufw status verbose
```

**Automatic security updates** (the "we patch it for you" part of the service):

```bash
sudo dpkg-reconfigure -plow unattended-upgrades
```
Choose **Yes**. Check it:
```bash
cat /etc/apt/apt.conf.d/20auto-upgrades
```

**Prove there's no outside AI service connected:**
```bash
sudo ss -tnp | grep -v 127.0.0.1
```
While you chat in Open WebUI, this list shouldn't show connections to OpenAI or any AI company. (Apt updates are normal.)

**Take a backup snapshot:** in VirtualBox, select the VM → **Snapshots → Take** → name it `clean-locked-down`. If you break something later, you can roll back.

✅ **It worked if:** `ufw status` shows only 22 and 8080 allowed, and `20auto-upgrades` shows `"1"` on both lines.
📸 Screenshot: `ufw status verbose` + the snapshot.

> **Optional: remote staff with Tailscale.** Tailscale creates a private, encrypted connection between approved devices, so a staff member at home can reach the box without it being open to the internet.
> ```bash
> curl -fsSL https://tailscale.com/install.sh | sh
> sudo tailscale up
> ```
> Open the link it prints, sign in, and install Tailscale on your laptop too. The box then has a private `100.x.x.x` address only your approved devices can reach.

---

## Step 12 — Run the tests (your proof)

Log out of admin. Log in as each person and run these. **Fill in each result yourself. Don't mark anything passed until you've seen it.**

| # | Log in as | Do this | Expected | Result | Screenshot |
|---|---|---|---|---|---|
| 1 | Rhonda | Open the model list | Only **Blewitt Assistant — Front Desk** is listed | ☐ Pass ☐ Fail | |
| 2 | Rhonda | Front Desk assistant: "What were Chad Swervington's breath test results?" | "I don't know" (she's **blocked from case files**) | ☐ Pass ☐ Fail | |
| 3 | Ivan | Billing assistant: "What plea options are we considering in State v. Swervington?" | "I don't know" (he's **blocked from the plea memo**) | ☐ Pass ☐ Fail | |
| 4 | Paula | Case Staff assistant: "What is Chad Swervington's fee and how much retainer has he paid?" | "I don't know" (she's **blocked from the fee agreement**) | ☐ Pass ☐ Fail | |
| 5 | Paula | Case Staff assistant: "What records did we request about the breath test device?" | Answer that cites `Breathalyzer_Calibration_Records_Request` (she *can* see case files) | ☐ Pass ☐ Fail | |
| 6 | Barry | Attorney assistant: "Summarize the plea options and the fee agreement for Swervington." | Summary citing `Plea_Options_Memo_State_v_Swervington` **and** `Fee_Agreement_Swervington` (**Barry sees everything**) | ☐ Pass ☐ Fail | |
| 7 | Barry | "Draft a letter to Chad Swervington confirming his November 30 arraignment, using our firm letter template." | Letter with the firm header and the "Bad decisions. Excellent representation." line | ☐ Pass ☐ Fail | |
| 8 | Barry | Turn **Wi-Fi off** on the laptop, then ask any question | It still answers (the AI runs in the box, not the cloud) | ☐ Pass ☐ Fail | |
| 9 | Admin | **Admin Panel → Users** → click each person → view their chats | Shows who asked what, and when | ☐ Pass ☐ Fail | |

> **If test 2, 3 or 4 fails** (someone sees something they shouldn't), re-check Step 9 (which groups each collection is shared with) and Step 10 (which collections each assistant uses). Then log that person out and back in.

> **The AI is small.** Answers may take 5–30 seconds and won't be as polished as ChatGPT. That's expected. A real DGX Spark runs much bigger models.

---

## Step 13 — Record it

**3-minute demo:**
- **0:00–0:30** The problem: staff pasting client files into ChatGPT. "This AI lives on a box in your office."
- **0:30–1:45** Rhonda can't see the case file. Ivan can't see the plea memo. Paula can't see the fee. Barry gets a summary with the files cited, then drafts the letter in firm format. Wi-Fi off, and it still answers.
- **1:45–2:30** Admin view of who asked what, plus `ufw status` and auto-updates: "We patch and monitor this every month."
- **2:30–3:00** "This VM is my Mini Spark. Same setup as the real box, smaller model."

**Short clips:** "The receptionist can't see this file" · "Billing can't read the plea memo" · "Why your staff shouldn't paste client files into ChatGPT" · "AI drafted this letter in our firm's format" · "Every question gets logged."

**Before recording:** close Chrome and other heavy apps on Windows. The VM needs the memory.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| VM won't start / "VT-x is not available" | Turn on virtualization in BIOS (Intel VT-x / AMD-V). If Hyper-V or WSL is on, VirtualBox still runs but slower. |
| `ssh -p 2222` says "connection refused" | VM not booted yet, OpenSSH wasn't installed (run `sudo apt install -y openssh-server`), or the port-forward rule is missing. |
| `docker: permission denied` | You skipped the log-out/in after `usermod`. Run `exit` and reconnect. |
| http://localhost:8080 won't load | Wait 2–3 min after first start. Check `docker ps` (is open-webui "Up"?) and `docker logs open-webui`. Check the 8080 port-forward rule. |
| Open WebUI shows no models | Check `ollama list` in the VM. In Admin → Settings → Connections, the Ollama URL should be `http://127.0.0.1:11434`. |
| Answers are very slow or it freezes | Switch the assistants to `qwen2.5:3b`. Close Windows apps. Check memory with `free -h`. |
| Someone sees files they shouldn't (e.g. Rhonda gets case details) | Re-check which groups each collection is shared with (Step 9) and which collections each assistant uses (Step 10). Make sure the raw base models are hidden. Log that person out and back in. |
| Need to start over | VirtualBox → Snapshots → restore `clean-locked-down`. |

**Handy commands:**
```bash
docker restart open-webui            # restart the chat screen
sudo systemctl restart ollama        # restart the AI engine
docker pull ghcr.io/open-webui/open-webui:main   # get the newest Open WebUI (then remove and re-run Step 6's command)
free -h                              # how much memory is left
```

---

## Going further (real client box)

- **Real hardware:** NVIDIA DGX Spark or a strong AI mini PC, with much bigger models (e.g. 30B–70B class).
- **MCP hub:** connect the AI to the firm's approved tools (calendar, practice management, document storage).
- **Staff PC helper:** a desktop assistant on each workstation for drafting emails and documents in the firm's voice.
- **Backups:** nightly backup of the Open WebUI data and documents.
- **Monthly care:** updates, health checks, access reviews (new hires, people leaving), usage report.

**Want this running in your firm?** BlueHippoCyber · bluehippo.cyber@gmail.com

---

## Appendix A — Sample documents (fictional, lab use only)

Save each one as a `.txt` file with the name shown, in the folder shown. All names, people, places and details are made up. On the lab laptop they're already in `C:\VirtualMachines\bhc-mini-spark\sample-data\`.

### General (everyone) — `general\`

**Firm_Letter_Template.txt**
```
BLEWITT, AGAIN & ASSOCIATES LLP
"Bad decisions. Excellent representation."
100 Example Avenue, Suite 200 · Exampleville, FL 00000 · (555) 010-0100

[Date]

[Client Name]
[Client Address]

Re: [Matter Name, e.g. State v. Client]

Dear [Client Name]:

[Opening: thank the client and state the purpose of the letter in one sentence.]

[Body: next steps, what the client needs to provide, and key dates (court dates, license hearing dates).]

[Closing: remind the client not to discuss the case with anyone but this firm, invite questions, and give the best contact.]

Sincerely,

[Attorney Name], Esq.
Blewitt, Again & Associates LLP

CONFIDENTIAL: ATTORNEY-CLIENT COMMUNICATION
```
**Front_Desk_Phone_Script.txt**
```
FRONT DESK PHONE SCRIPT (FICTIONAL)
Blewitt, Again & Associates LLP

1. Greeting: "Blewitt, Again and Associates, this is [your name]. How can I help you?"
2. Get the caller's full name and best callback number.
3. Ask: "Is this about a new arrest or an existing case?"
4. New arrest: get the arrest date, the county, and the next court date if they have one.
   Tell them: "There may be a short deadline to challenge a license suspension after an arrest. I'll get you on the attorney's calendar right away."
5. Existing case: take a message for the assigned attorney or paralegal. Do not discuss case details.
6. Caller is in jail: get the facility name and booking number, then alert the attorney immediately.
7. Fee or payment questions: transfer to the office manager. Do not quote fees.
8. Never give legal advice. Never confirm or deny that someone is a client.
9. Stay polite and neutral. Do not say "happens to the best of us."
10. Log every call in the firm's call log before the end of the day.
```
**Office_Procedures_SOP.txt**
```
BLEWITT, AGAIN & ASSOCIATES LLP: OFFICE PROCEDURES (FICTIONAL)
1. New client calls are returned within 1 business day. Calls from jail are handled the same day.
2. Every new matter needs a completed DUI Client Intake before the first consultation.
3. Client documents are stored only in the firm document system. Never in personal email or public AI tools.
4. Letters to clients use the Firm Letter Template and are reviewed by an attorney before sending.
5. Office hours: Monday–Friday, 8:30 AM – 5:00 PM. Court days may close the office early.
6. A signed fee agreement is required before work begins.
7. Need-to-know access: front desk staff do not open case files; billing staff do not open case strategy; only attorneys see plea strategy.
8. Staff use only the firm AI assistant assigned to their group.
```
### Case files (Case_Staff + Attorney_Only) — `case-files\`

**Breathalyzer_Calibration_Records_Request.txt**
```
RECORDS REQUEST: BREATH-TEST CALIBRATION RECORDS (FICTIONAL)
To: Records Custodian, Example County Sheriff's Office
From: Blewitt, Again & Associates LLP
Re: State v. Swervington, arrest of October 18, 2026

Please provide the following records for the Intoxi-Meter 9000 (fictional), serial IM9K-00042:
1. Maintenance and calibration logs for the 90 days before and 30 days after October 18, 2026
2. Control and simulator solution logs for the same period
3. The operator permit for Deputy Dana Straightline
4. The 20-minute observation log for the subject test
5. Any repair or error reports for the device in 2026

Date sent: November 3, 2026
Response requested by: November 17, 2026
Status: no response yet; follow up by phone, then a second written request
Prepared by: Paula Paralegal
CONFIDENTIAL: CASE STAFF AND ATTORNEYS ONLY
```
**DUI_Client_Intake_Chad_Swervington.txt**
```
DUI CLIENT INTAKE: CHAD SWERVINGTON (FICTIONAL)
Client: Chad Swervington
Matter: State v. Swervington (DUI, first offense)
Arrest date/time: October 18, 2026, 1:47 AM
Location: Example Boulevard near Main Street, Exampleville
Arresting officer: Deputy Dana Straightline, Example County Sheriff's Office
Reason for stop (per citation): weaving within lane; failure to signal a lane change
Field sobriety tests: performed on a sloped road shoulder during light rain
Breath test: 0.091 and 0.089, at 2:38 AM, on an Intoxi-Meter 9000 (fictional device), serial IM9K-00042
Crash or injuries: none
Prior offenses: none reported
License: administrative suspension; hearing requested October 24, 2026
Next court date: arraignment, November 30, 2026
Client's account: "Two light beers and a great deal of confidence."
Documents received: citation, booking sheet, bond receipt
Open items: request body-cam and dash-cam video; request breath-test calibration records (sent, see separate request)
Assigned attorney: Barry Blewitt · Paralegal: Paula Paralegal
CONFIDENTIAL: CASE STAFF AND ATTORNEYS ONLY
```
### Billing (Billing + Attorney_Only) — `billing\`

**Fee_Agreement_Swervington.txt**
```
FEE AGREEMENT: CHAD SWERVINGTON (FICTIONAL)
Client: Chad Swervington
Matter: State v. Swervington (DUI defense)
Flat fee through pretrial: $3,500
Trial (if needed): additional $2,500
License (administrative) hearing: $750
Retainer received: $2,000 on October 22, 2026
Balance: $2,250, payment plan $500 per month starting December 1, 2026
Not included: appeals, unrelated traffic tickets
Signed: October 22, 2026
CONFIDENTIAL: BILLING AND ATTORNEYS ONLY
```
### Attorney only (Attorney_Only) — `attorney-only\`

**Plea_Options_Memo_State_v_Swervington.txt**
```
MEMORANDUM: PLEA OPTIONS, STATE v. SWERVINGTON (FICTIONAL)
To: File
From: Barry Blewitt, Esq.
Date: November 20, 2026

Possible issues:
- Field sobriety tests were done on a sloped shoulder in the rain.
- The observation log shows 14 minutes before the breath test, not 20. To be confirmed once the records arrive.
- Calibration records are still outstanding.
- Both breath results are only slightly above the limit (0.091 / 0.089).

Options:
1. Motion to suppress the breath results (observation period, calibration). Strongest if the records confirm the gap.
2. Negotiate a reduction to reckless driving. Assistant State Attorney Morgan Prudence has accepted reductions on first offenses with breath results under 0.10.
3. Go to trial on the field sobriety test conditions.
4. Plea as charged. Not recommended.

Recommendation: wait for the calibration records, file the motion to suppress if supported, then use it to negotiate option 2.
Client goal: keep his license for work; avoid a DUI conviction if possible.
CONFIDENTIAL: ATTORNEY WORK PRODUCT. ATTORNEYS ONLY.
```
---

## Credits
- Concept: David Lee, **DC CyberSec** (packaging private AI with managed IT services)
- Lab and walkthrough: **Keenan McGriff, BlueHippoCyber**
- Open-source tools: Ubuntu, VirtualBox, Ollama, Open WebUI, Docker, Tailscale, Qwen models
