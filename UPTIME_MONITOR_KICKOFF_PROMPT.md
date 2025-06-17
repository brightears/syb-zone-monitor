
# Claude Code Prompt — Soundtrack Zone Uptime Monitor v2

## Objective
Build a lightweight Python service that watches **Soundtrack Your Brand** zones and fires an alarm when any zone is **offline ≥ 10 minutes**.  
Alarm order: **(1) mobile push**, **(2) email fallback**.

---

## Context & Resources
* **SYB API key** and developer account ready  
* **Docs**: ❏ _paste official SYB API docs link here_ ❏  
* **Target host**: existing Ubuntu 22.04 VPS (Nginx installed). Keep cost near-zero—avoid paid serverless unless clearly simpler  
* **Runtime**: Python 3.12  
* **Push provider**: Pushover (flexible; suggest better if any)  
* **Email**: SMTP (Gmail send-as or Mailgun—whichever is simplest)

---

## Functional Requirements
1. **Polling loop**  
   * Call SYB Zones/status endpoint every **60 s**  
2. **Offline logic**  
   * Track `offline_since` per zone; if duration ≥ 600 s, trigger `send_push()` → then `send_email()` if push succeeds or 60 s later (whichever first)  
3. **Notification payload**
   ```
   🌐 Zone "{{zone_name}}" offline since {{HH:MM}} (>{{minutes}} min)
   Dashboard: {{dashboard_url}}
   ```
4. **Configuration**  
   * `.env` for API keys, polling interval, zone list, Pushover+SMTP creds  
5. **Resilience**  
   * Exponential back-off on network/API errors (max 5 retries)  
6. **Logging & Metrics**  
   * JSON logs → stdout  
   * `/healthz` endpoint returns:
     ```json
     {"uptime":"...","zones":{ ... }}
     ```

---

## Non-Functional Requirements
* Minimal dependencies (`httpx`, `python-dotenv`, `pydantic`)  
* Idiomatic, type-annotated Python (PEP 8) with unit-tested timer logic  
* **Deployment**: provide **both**  
  * **Option A** – systemd service file (`monitor.service`) under `/opt/uptime-monitor`  
  * **Option B** – Dockerfile (alpine-slim) + `docker-compose.yml` behind current Nginx  
* README must show both paths

---

## Deliverables
```
.
├── main.py
├── notifier/
│   ├── __init__.py
│   ├── base.py
│   ├── pushover.py
│   └── email.py
├── config.example.env
├── requirements.txt
├── Dockerfile
├── docker-compose.yml      # optional
├── monitor.service         # systemd unit
├── tests/
│   └── test_timer.py
└── README.md
```

---

## Step-by-Step Plan for Claude
1. Confirm which SYB endpoint exposes per-zone online/offline status  
2. Draft a Mer-maid architecture diagram & class interfaces  
3. Scaffold repo; implement config loader (Pydantic)  
4. Code polling + offline-timer module; write unit test  
5. Implement `PushoverNotifier` (push) and `EmailNotifier` (SMTP); build fallback chain  
6. Add Dockerfile & systemd unit; document both deployments in README  
7. Output full file tree + key code snippets; list TODOs / assumptions

---

## Code Quality & Best Practices
* SOLID, modular; isolate I/O from business logic  
* Graceful shutdown on `SIGINT` / `SIGTERM`  
* Highlight SYB rate-limit considerations and how to tune polling safely

---

## Final Return Package (from Claude)
* Repo tree & full code (or GitHub gist)  
* “Next Steps” checklist

---

### Open Questions for Norbert
1. Does the VPS already have **Docker** installed, or should systemd be the default route?  
2. Any preferred log retention/rotation policy?  
3. Maximum acceptable polling interval if SYB imposes tighter rate limits?

(Answering these will help Claude fine-tune the implementation.)
