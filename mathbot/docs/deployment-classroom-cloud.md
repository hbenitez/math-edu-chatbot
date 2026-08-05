# MathBot — "Classroom Cloud" Deployment Guide

**Local Client–Server deployment for schools with no Internet**

This guide explains how to run **MathBot** (both the text tutor `text.py` and the
visual/image tutor `visual.py`) on a teacher's laptop that acts as a local AI
server, so that students can use it from their phones over a local Wi‑Fi network
**without any Internet connection**.

---

## 1. Architecture overview

```
        ┌─────────────────────────────┐
        │   SERVER  (Teacher's PC)     │
        │   Windows 11 · i7 · 40 GB    │
        │                              │
        │   Ollama  ──►  llama3.2      │  ← does all the "thinking"
        │           └─►  qwen2.5vl:7b  │
        │                              │
        │   text.py    → port 7860     │  (Gradio web UI)
        │   visual.py  → port 7861     │  (Gradio web UI)
        └───────────────┬──────────────┘
                        │  Wi‑Fi (no Internet needed)
          ┌─────────────┴───────────────┐
          │   LOCAL NETWORK              │
          │   Phone hotspot OR TP‑Link   │
          │   e.g. 192.168.x.x           │
          └─────────────┬───────────────┘
                        │
     ┌──────────────────┼──────────────────┐
     │                  │                  │
┌────┴─────┐      ┌─────┴────┐       ┌─────┴────┐
│ Student  │      │ Student  │  ...  │ Student  │
│ Galaxy   │      │ phone    │       │ phone    │
│ A32      │      │ (Chrome) │       │ (Chrome) │
└──────────┘      └──────────┘       └──────────┘
   Opens http://192.168.x.x:7860  (text)
      or http://192.168.x.x:7861  (visual)
```

**Key idea:** the AI models never run on the student's phone. The phone only shows
a lightweight web page in the browser. All computation happens on the teacher's
laptop; only the question and the answer travel over Wi‑Fi.

**Hardware in this guide**

| Role | Device | Notes |
|------|--------|-------|
| Server | Laptop — Windows 11, Intel Core i7, 40 GB RAM | Plenty of RAM for both models |
| Network | Phone hotspot **or** a basic router (e.g. TP‑Link) | No Internet required |
| Client | Samsung Galaxy A32 (and similar low‑end phones) | Chrome or Firefox browser |

---

## 2. Prerequisites — do this ONCE, with Internet

> ⚠️ **Steps 2 and 3 require a working Internet connection** (to download the
> installers, the Python packages, and the AI models). Do all of this **before**
> going to the classroom. After the models are downloaded, MathBot runs **fully
> offline**.

Approximate download size: **~8.5 GB** (Ollama + Python + models). Make sure the
laptop has at least **15 GB free disk**.

### 2.1 Install Ollama (the AI engine)

1. Download **Ollama for Windows** from <https://ollama.com/download/windows>.
2. Run `OllamaSetup.exe` and accept the defaults. It installs as a background
   service that starts automatically with Windows.
3. Verify in a terminal (**PowerShell** or **Command Prompt**):

   ```powershell
   ollama --version
   ```

### 2.2 Download the two AI models

```powershell
ollama pull llama3.2         # ~2 GB  — used by text.py
ollama pull qwen2.5vl:7b     # ~6 GB  — used by visual.py (vision)
```

Confirm both are present:

```powershell
ollama list
```

You should see `llama3.2` and `qwen2.5vl:7b`.

### 2.3 Install Python

1. Download **Python 3.10 or newer** from <https://www.python.org/downloads/windows/>.
2. During installation, **tick "Add python.exe to PATH"**.
3. Verify:

   ```powershell
   python --version
   ```

### 2.4 Install MathBot and its Python dependencies

1. Copy the `mathbot` project folder onto the laptop (e.g. `C:\mathbot`).
2. Open PowerShell in that folder and create a virtual environment:

   ```powershell
   cd C:\mathbot
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   > If PowerShell blocks the activation script, run once:
   > `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` and try again.

3. Install the required packages (includes the extras `visual.py` needs):

   ```powershell
   pip install "gradio>=6.11.0" "langchain>=0.2.0" "langchain-ollama>=0.1.0" ollama pillow
   ```

> ✅ At the end of Section 2 everything needed is on the laptop. From here on, **no
> Internet is required**.

---

## 3. Set up the local network (No Internet)

You only need the devices to "see each other" — an Internet uplink is **not**
required. Choose **one** of the two options.

### Option A — Basic router (recommended, most reliable)

1. Power on a basic router (e.g. a generic **TP‑Link**). It does **not** need to be
   connected to any Internet line.
2. Connect the **teacher's laptop** to that router's Wi‑Fi (or by Ethernet cable).
3. Have the **students' phones** join the **same** Wi‑Fi network.

*Why recommended:* routers rarely isolate clients from each other, so phones can
always reach the laptop.

### Option B — Teacher's phone hotspot

1. On the teacher's phone, turn on **Mobile Hotspot** (Settings → Connections →
   Mobile Hotspot and Tethering). Mobile data can stay **off** — it is not needed.
2. Connect the **laptop** to that hotspot.
3. Have **students' phones** join the same hotspot.

> ⚠️ Some phone hotspots enable "client isolation", which prevents phones from
> reaching the laptop. If students get "can't connect", prefer **Option A**.

### 3.1 Find the laptop's local IP address

On the laptop, in PowerShell:

```powershell
ipconfig
```

Look for the active adapter (the Wi‑Fi one connected to the router/hotspot) and
note **IPv4 Address**, e.g. `192.168.1.5`. Students will type this address.

> 📌 Common ranges: router → `192.168.0.x` or `192.168.1.x`; phone hotspot →
> often `192.168.43.x`. Write the exact number on the whiteboard.

### 3.2 Allow MathBot through Windows Firewall (do once)

Windows blocks incoming connections by default, so phones can't reach the laptop
until you open the ports.

1. Make sure the classroom network is set to **Private**: Settings → Network &
   Internet → Wi‑Fi → click the network → **Network profile type: Private**.
2. Open the two MathBot ports. In **PowerShell run as Administrator**:

   ```powershell
   New-NetFirewallRule -DisplayName "MathBot Text"   -Direction Inbound -Protocol TCP -LocalPort 7860 -Action Allow -Profile Private
   New-NetFirewallRule -DisplayName "MathBot Visual" -Direction Inbound -Protocol TCP -LocalPort 7861 -Action Allow -Profile Private
   ```

   *(Alternatively, when you first launch a script, Windows shows a "Windows
   Defender Firewall" popup — click **Allow access** and tick **Private
   networks**.)*

---

## 4. Run MathBot on the server

The two apps must run on **different ports** because each one, by default, uses
`7860`. We keep `text.py` on **7860** and put `visual.py` on **7861**.

Open **two** PowerShell windows, activate the environment in each
(`.\.venv\Scripts\Activate.ps1`), then:

### Terminal 1 — Text tutor (`text.py`)

```powershell
python text.py
```

Serves the text tutor at `http://<laptop-ip>:7860`.

### Terminal 2 — Visual tutor (`visual.py`)

Override the port with an environment variable (no need to edit the file):

```powershell
$env:GRADIO_SERVER_PORT = "7861"
python visual.py
```

Serves the image tutor at `http://<laptop-ip>:7861`.

> If you only need one of the two tutors, just run that single script — it will
> use `7860` and you can skip the port override.

**How do I know it worked?** Each terminal prints:

```
* Running on local URL:  http://0.0.0.0:7860
```

> ℹ️ These scripts intentionally do **not** use Gradio's `share=True`. That feature
> needs the Internet; here everything is served over the local network, so it is
> not used.

### 4.1 Keep the laptop awake

So the server doesn't sleep mid‑class: Settings → System → Power → **Screen and
sleep** → set **"When plugged in, put my device to sleep after"** to **Never**.

---

## 5. Connect from a student's phone (Samsung Galaxy A32)

1. Make sure the phone is connected to the **same** Wi‑Fi (router or hotspot) as
   the laptop.
2. Open **Chrome** (or Firefox).
3. In the address bar type the laptop's address **and port**, for example:

   - Text tutor:   `http://192.168.1.5:7860`
   - Visual tutor: `http://192.168.1.5:7861`

   *(Replace `192.168.1.5` with the actual IP from step 3.1.)*

4. The MathBot web interface loads. The student types a math problem (text tutor)
   or uploads/takes a photo of the exercise (visual tutor), and MathBot replies
   with **guiding questions** (Socratic method) — it helps the student reason to
   the answer instead of just giving it.

> 💡 Tip: create a **home‑screen shortcut** on each phone (Chrome menu → "Add to
> Home screen") so students tap an icon instead of typing the address every day.

---

## 6. Daily startup checklist (quick reference)

Once everything is installed, a normal class only needs:

1. ☐ Turn on the router / phone hotspot.
2. ☐ Connect the laptop to that Wi‑Fi.
3. ☐ Confirm the laptop's IP with `ipconfig` (write it on the board).
4. ☐ Open PowerShell → `cd C:\mathbot` → `.\.venv\Scripts\Activate.ps1`.
5. ☐ `python text.py`  (Terminal 1).
6. ☐ `$env:GRADIO_SERVER_PORT="7861"; python visual.py`  (Terminal 2, optional).
7. ☐ Students open `http://<ip>:7860` (and `:7861`) in Chrome.

To stop a server, press **Ctrl + C** in its terminal.

---

## 7. Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Phone browser says "can't connect / site not reachable" | Firewall blocking, or wrong IP | Re‑check `ipconfig`; confirm the firewall rules in §3.2; ensure phone is on the same Wi‑Fi |
| Works on the laptop's own browser but not on phones | Phone is on a different network, or hotspot "client isolation" | Reconnect the phone to the same Wi‑Fi; switch to a router (Option A) |
| `Cannot find empty port ... 7860` when starting the 2nd app | Both apps trying to use 7860 | Set `$env:GRADIO_SERVER_PORT="7861"` before `python visual.py` |
| Visual tutor shows "Error … Verifica que Ollama esté corriendo" | Ollama service not running, or model missing | Run `ollama list`; if empty, `ollama pull qwen2.5vl:7b`; restart the laptop so the Ollama service starts |
| Answers are very slow | First request loads the model into RAM | The first question per model is slow (~20–30 s); later ones are faster. 40 GB RAM easily holds both models |
| The IP changed the next day | Router/hotspot gave a new address (DHCP) | Re‑run `ipconfig` each session, or set a static IP / DHCP reservation for the laptop |
| PowerShell won't run `Activate.ps1` | Execution policy | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |

---

## 8. Notes and limits

- **Concurrent students:** Ollama processes requests roughly one at a time, so with
  many phones asking simultaneously there will be a queue. For a typical class this
  is fine; answers just arrive a few seconds apart. The i7 + 40 GB laptop is well
  suited to this workload.
- **Models used:**
  - `text.py` → `llama3.2` (Socratic text tutoring).
  - `visual.py` → `qwen2.5vl:7b` (reads a photo of the exercise, then guides).
  - The description mentions "Gemma 3n / Gemma 2B" as example engines — those also
    run under Ollama (`ollama pull gemma2:2b`), and you could switch to them by
    changing the model name at the top of `text.py`. This guide uses the models the
    scripts already ship with.
- **Privacy:** because nothing leaves the local network, no student data is sent to
  the Internet.
- **Security:** anyone on the local Wi‑Fi can open the page. Keep the router/hotspot
  password protected and share it only with the class.
```