# DepoSafe - 6-Minute Grand Finale Live Demonstration Script
## AICTE Regulation Bureau &bull; Smart India Hackathon Grand Finale

> [!IMPORTANT]
> **Advisory Language Requirement**: Avoid binary fraud labels or claiming definitive verification without caveats. Use statutory phrasing: *"available checks passed"*, *"not confirmed"*, and *"review priority score"*. Explain that the system is an advisory copilot for regulatory officers, backed by an append-only SHA-256 hash-chained audit ledger.

---

### 1. Minute-by-Minute Demonstration Matrix

| Time Window | Screen / Portal | Exact Click Path | Spoken Script (What to Say) | Judging Criterion Proven |
|---|---|---|---|---|
| **0:00 - 0:45** (45s) | **Master Dashboard** | 1. Open [http://localhost:3000](http://localhost:3000)<br/>2. Point to KPI metric cards<br/>3. Switch language toggle (EN &harr; HI) | *"Respected Jury, Indian technical education requires thousands of colleges to maintain Fixed Deposits with AICTE as security. Verifying these across hundreds of banks currently causes massive delays, risks of altered instruments, and cover lapses. DepoSafe is an AI-assisted, human-in-the-loop regulatory platform designed for zero black-box trust and full auditability."* | **Problem Context, Scale & Gov-Tech Accessibility (Bilingual)** |
| **0:45 - 2:00** (75s) | **Verification Workspace (Hero Case)** | 1. Click **Verification Workspace**<br/>2. Open Hero Case: `BNB-DEL-HERO-1000` (FDR #1)<br/>3. Toggle **B-Boxes: ON**<br/>4. Toggle **ELA Heatmap**<br/>5. Inspect **Document Forensics Tab** | *"Here is our Hero Case from National Institute of Technology & Science. Notice the split-pane workspace. On the left is the raw scan with layout-aware bounding boxes. The system flags that this instrument was created with Adobe Photoshop in its PDF metadata. Clicking 'ELA Forensics' renders a false-color Error Level Analysis compression heatmap showing non-uniform pixel artifacts around the maturity date and amount."* | **Document AI, Layout Extraction & Digital Forensics (ELA / Metadata)** |
| **2:00 - 3:00** (60s) | **Dual-Truth Provenance & Cross-Reconciliation** | 1. Click **4-Source Provenance Tab**<br/>2. Click **Cross-Doc Reconciliation Tab** | *"Notice our 4-level provenance matrix: Submitted (Blue), AI Extracted (Purple), Bank Confirmed (Green), and Officer Verified (Amber). Cross-document reconciliation compares the FDR Certificate against the Bank Confirmation Letter. Look at this critical discrepancy: the certificate claims maturity in 2032, but the official bank letter states 2026. The Review Priority Score adjusts to High (80/100), presenting explicit evidence rather than an unexplainable verdict."* | **Zero Black-Box Transparency & Cross-Document Reconciliation** |
| **3:00 - 3:45** (45s) | **Core Banking Adapter & Circuit Breaker** | 1. Click **Officer Actions**<br/>2. Click **Query Bank CBS Adapter** (or trigger Timeout/Downtime) | *"We now query the bank's core system through our BankVerificationAdapter. The simulated CBS responds with statutory wording: 'available checks passed' and an HMAC-SHA256 digital signature, watermarked as a simulation. If the bank gateway times out or encounters downtime, our circuit breaker trips to OPEN and gracefully routes the case to human officer manual review."* | **Bank Integration Architecture & Gateway Resilience** |
| **3:45 - 4:30** (45s) | **Demo Clock & Maturity Radar** | 1. Look at Header Demo Clock<br/>2. Click **+90 Days** advance<br/>3. Navigate to **Maturity & Renewal Radar** | *"Fixed deposits mature silently unless tracked proactively. We advance our controllable Demo Clock by 90 days. Instantly, our Maturity Radar updates: 36 cases escalate from T-90 to T-15 and Overdue queues. Our Zero-Gap Regulatory Guard immediately flags 31 colleges with cover lapses between expired deposits and successors."* | **Controllable Demo Clock & Proactive Lifecycle Automation** |
| **4:30 - 5:15** (45s) | **Four-Eyes Role Gate & Release Order** | 1. In header, switch role to `VERIFICATION_OFFICER`<br/>2. Try to authorize release &rarr; **403 Forbidden**<br/>3. Switch role to `COMPETENT_AUTHORITY`<br/>4. Open **Release & Refund Governance**<br/>5. Click **Authorize Official Release** | *"Security deposits cannot be released casually. When logged in as a Verification Officer, attempting to approve release is strictly blocked by RBAC with HTTP 403 Forbidden. Only the Member Secretary—the Competent Authority—can authorize release orders. When approved with order reference `AICTE/REL/2026/088`, the predecessor instrument becomes non-destructively SUPERSEDED."* | **RBAC, Four-Eyes Principle & Statutory Governance** |
| **5:15 - 6:00** (45s) | **Audit Chain & Evidence Pack** | 1. Navigate to **Audit Ledger** tab<br/>2. Click **Verify Hash Chain Integrity**<br/>3. Open FDR Passport &rarr; Click **Download Evidence Pack** | *"Every state transition, officer override, and bank response is appended to a cryptographic SHA-256 hash-chain: H_n = SHA256(H_n-1 || event_n). Clicking 'Verify Ledger' performs a mathematical traversal proving zero tampering. Finally, with one click, we generate the official statutory PDF Evidence Pack ready for court or vigilance scrutiny. DepoSafe gives AICTE complete regulatory integrity."* | **Cryptographic Tamper-Evidence & Statutory Audit Dossier** |

---

### 2. Live Demo Failure Plan & Resilience Protocols

In high-stakes live hackathon demonstrations, external environments or local state can occasionally fail. Use this triage checklist:

#### Scenario A: Local Database Inconsistent or Dirty State
* **Symptom**: Modified records, non-standard dates, or previously completed hero case.
* **Immediate Recovery Command** (takes under 4 seconds):
  ```bash
  ./scripts/demo_reset.sh
  ```
* **Explanation**: Resets SQLite database, reseeds the exact 80 institutions and 164 FDRs from `data/synthetic/ground_truth.json`, and resets the Demo Clock to `2026-11-29`.

#### Scenario B: Bank CBS Gateway Times Out / Throws 503
* **Symptom**: Red alert banner indicating `Simulated Bank Core Gateway Timeout` or `Circuit Breaker OPEN`.
* **Spoken Pitch Pivot (Turn it into a win)**:
  > *"Notice what just happened: In the real world, banking APIs experience downtime and rate-limits. Rather than crashing, DepoSafe's Verification Orchestrator tripped our Circuit Breaker to prevent cascading failures, marked the source as `SOURCE_UNAVAILABLE`, and automatically routed this instrument to the officer's manual scrutiny queue. The system is designed to be resilient by default."*
* **Officer Action**: Open **Record Manual Verification**, enter Branch Visit reference `OFF-NWRO-2026-VERIF-441`, and verify with human provenance.

#### Scenario C: Laptop Network / Browser Display Glitch
* **Backup Checklist**:
  1. Have pre-recorded 2-minute high-definition video walkthrough (`docs/assets/demo_backup_video.mp4`) queued in full screen.
  2. Maintain a printed physical copy of `docs/assets/contact_sheet.png` and the generated PDF Evidence Pack.
  3. Run terminal-based demo fallback:
     ```bash
     PYTHONPATH=. backend/venv/bin/python3 scripts/demo_runner.py
     ```
     This executes all 10 capabilities end-to-end directly in the terminal in 30 seconds.
