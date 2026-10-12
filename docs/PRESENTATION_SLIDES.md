# FHC ERPNext / Frappe Developer Practical Exam Presentation

**Candidate Technical Presentation & Live Demonstration**  
**Topic:** Training and Certification Management System (`fhc_training`)  
**Organization:** Federal Housing Corporation (FHC) — Information Technology / ERP Development  
**Duration:** 25 Minutes (15 min Slides + 10 min Live Demonstration)  

---

## Slide 1: Title & Overview
### Training and Certification Management System (`fhc_training`)
- **Candidate Position:** ERPNext / Frappe Developer
- **Organization:** Federal Housing Corporation (FHC)
- **Framework & Stack:** Frappe Framework v15, ERPNext v15, MariaDB 10.6, Redis 6, Ubuntu 22.04 LTS (WSL2)
- **Primary Goal:** Transition FHC from error-prone manual spreadsheets to a centralized, role-governed, automated training management and certification lifecycle within ERPNext.

> **Speaker Notes (1 min):**  
> *"Good morning members of the evaluation panel. Today, I am presenting the Training and Certification Management System built natively as a custom Frappe application for the Federal Housing Corporation. This solution automates the planning, approval, score capture, and certificate issuance lifecycle for FHC staff."*

---

## Slide 2: Problem Statement & Application Objectives
### The Business Challenge at FHC
1. **Disjointed Records:** Employee training records, attendance sheets, and certification validities were maintained in scattered spreadsheets.
2. **Scheduling Conflicts:** Trainers were frequently double-booked across concurrent sessions.
3. **Compliance Risks:** Expired certifications (e.g. Occupational Health & Safety) went unnoticed, risking safety audit compliance.
4. **Lack of Governance:** No standardized approval chain existed before training budgets and sessions were committed.

### Application Objectives
- **Centralized Registry:** Model Courses, Trainers, Sessions, and Certificates with strict relational integrity.
- **Automated Workflow:** Multi-state approval hierarchy ensuring departmental oversight.
- **Business Rule Enforcement:** Validation preventing trainer double-booking, past dates, duplicate participants, and invalid score entry.
- **Automated Expiry & Reporting:** Nightly background scheduler updating expiration statuses paired with dynamic management reports.

---

## Slide 3: DocType Architecture & Relationships
### Relational Data Model

```
 ┌───────────────────────┐             ┌───────────────────────┐
 │    Training Course    │             │        Trainer        │
 │     (CRS-.####)       │             │      (TRN-.####)      │
 └──────────┬────────────┘             └──────────┬────────────┘
            │ 1                                   │ 1
            │                                     │
            └───────────────┬─────────────────────┘
                            ▼ *
             ┌──────────────────────────────┐
             │       Training Session       │
             │       (TS-.YYYY.-.####)      │
             └──────────────┬───────────────┘
                            │ 1
                            │ (Child Table)
                            ▼ *
             ┌──────────────────────────────┐
             │     Training Participant     │
             │   (Attendance, Score, Pass)  │
             └──────────────┬───────────────┘
                            │ 1
                            ▼ 1
             ┌──────────────────────────────┐
             │        Certification         │
             │     (CERT-.YYYY.-.#####)     │
             └──────────────────────────────┘
```

### DocType Summary
1. **Training Course (Master):** Course title, category, duration hours, passing threshold (1–100%), validity in months.
2. **Trainer (Master):** Instructor credentials, status (`Active`/`Inactive`), and linked Frappe `User`.
3. **Training Session (Transaction):** Scheduled run with venue, dates, trainer, capacity limits, and workflow state.
4. **Training Participant (Child Table):** Embedded attendance, score calculation, pass/fail result, and certificate link.
5. **Certification (Transaction):** Issued credential with issue date, auto-calculated expiry date, and status (`Active`, `Expired`, `Revoked`).

---

## Slide 4: Business Process & Multi-State Workflow
### State Transition Diagram

```
 [ Draft ]
    │  (Action: "Submit for Approval" | Role: Training Officer)
    ▼
 [ Pending Approval ] ───────────┐ (Action: "Reject" | Role: Training Manager)
    │                             ▼
    │ (Action: "Approve"    [ Rejected ]
    │  Role: Training Mgr)        │ (Action: "Revise" | Role: Training Officer)
    ▼                             └──────► [ Draft ]
 [ Approved ] ──► [ Cancelled ] (Action: "Cancel Session" | Role: Training Manager)
    │
    │  (Action: "Complete" | Role: Trainer or Training Manager)
    │  *Condition: End Date reached & participants evaluated*
    ▼
 [ Completed ]
    │
    ▼ (Action Button: "Issue Certificates" | Role: Officer / Manager)
 [ Certificates Generated ] (Idempotent, calculates expiry)
```

### Key Workflow Controls
- Sessions in `Pending Approval` or `Approved` "lock" the trainer's calendar.
- Only when `Approved` can scores and attendance be recorded.
- A session cannot be moved to `Completed` before its scheduled end date.

---

## Slide 5: Role-Based Access Control (RBAC) & Row-Level Security
### Role Matrix

| Capability | Training Officer (`officer@fhc.test`) | Training Manager (`manager@fhc.test`) | Trainer (`trainer@fhc.test`) |
|---|:---:|:---:|:---:|
| Create / Edit Courses & Trainers | Yes | Yes | Read Only |
| Create Draft Sessions | Yes | Yes | No |
| Submit Session for Approval | Yes | Yes | No |
| Approve / Reject / Cancel Sessions | No | **Yes** | No |
| Enter Scores & Attendance | Yes | Yes | **Own Sessions Only** |
| Mark Session Completed | No | **Yes** | **Yes (Own Sessions)** |
| Issue Certificates | Yes | Yes | No |
| Revoke Certificates | No | **Yes (With Reason)** | No |

### Row-Level Data Isolation for Trainers
Implemented via Frappe hooks:
```python
# hooks.py
permission_query_conditions = {
    "Training Session": "fhc_training...get_permission_query_conditions",
}
has_permission = {
    "Training Session": "fhc_training...has_permission",
}
```
**Mechanism:** When a trainer logs in, the query conditions automatically filter `tabTraining Session.trainer IN (Trainer linked to current user)`, ensuring trainers cannot see or tamper with peer instructors' sessions.

---

## Slide 6: Core Server-Side Logic (Python)
### Key Business Rules Enforced in `training_session.py`
1. **Schedule Conflict Prevention:**
   ```python
   clash = frappe.get_all("Training Session", filters=[
       ["trainer", "=", self.trainer],
       ["name", "!=", self.name or ""],
       ["workflow_state", "in", ["Pending Approval", "Approved"]],
       ["start_date", "<=", self.end_date],
       ["end_date", ">=", self.start_date],
   ])
   if clash:
       frappe.throw(_("Trainer {0} is already booked in session {1}.").format(self.trainer, clash[0]))
   ```
2. **Automatic Result Derivation:**
   - Evaluates each participant row: if `attendance == "Present"` and `score >= passing_score`, set `result = "Pass"`; otherwise `"Fail"`.
3. **Idempotent Certificate Generation:**
   - Whitelisted method `issue_certificates(session_name)`: iterates over passing attendees, creates certificates, stores certificate name back on child table, preventing duplicate issues.

---

## Slide 7: Client-Side Form Experience (JavaScript)
### Dynamic UX Enhancements in `training_session.js` & `certification.js`
1. **Dynamic Field Queries:**
   - Filters out inactive courses (`is_active = 1`) and non-active trainers (`status = "Active"`) directly in dropdowns.
2. **Dashboard Metric Badges:**
   - Real-time badges for **Total Participants** (blue) and **Passed Count** (green).
   - In Certification form: Color badges for status (`Active` green, `Expired` red, `Revoked` gray), and **"Expires in X days"** warning (orange if $\le$ 30 days).
3. **Live Recalculation:**
   - When score or attendance changes in the participant child table, client-side JS instantly re-evaluates Pass/Fail and total counters without requiring a page refresh.
4. **Interactive Action Dialogs:**
   - One-click confirmation prompt for issuing certificates.
   - Modal prompt dialog requiring a mandatory text reason when revoking a certificate.

---

## Slide 8: Reporting & Background Automation
### 1. Script Report: "Certification Expiry"
- **Filters:** Course, Status (`Active`, `Expired`, `Revoked`), Expiring Within (e.g., 30, 60, 90 days).
- **Dynamic Calculation:** Calculates `days_remaining` using `date_diff(expiry_date, today())`.
- **Purpose:** Enables FHC HR and department heads to forecast training renewals before certifications lapse.

### 2. Automated Nightly Scheduler
- Registered in `hooks.py` under `scheduler_events["daily"]`.
- Executes `mark_expired_certifications()`:
  ```python
  def mark_expired_certifications():
      frappe.db.sql("""
          UPDATE `tabCertification`
          SET status = 'Expired'
          WHERE status = 'Active' AND expiry_date < %s
      """, (today(),))
  ```

---

## Slide 9: Testing Strategy & Verification Evidence
### Rigorous Quality Assurance Approach
- **18 Automated Unit Tests:**
  - Validates happy paths (creation, workflow, scoring, certificate generation).
  - Validates negative tests (past dates, end before start, participant limits, duplicate IDs, double booking).
  - Validates security boundary (trainer can only query own records).
- **Automated Test Results:**
  ```text
  Ran 18 tests in 6.361s — OK (Zero Failures)
  ```
- **25 Manual Functional Test Checklist Scenarios:**
  - 100% pass rate documented in `docs/TEST_CHECKLIST.md`.

---

## Slide 10: Reproducibility & Deployment (`hooks.py` Fixtures)
### Easy Deployment on Any Site
- Core system configuration stored as fixtures in `fhc_training/fixtures/`:
  - `role.json` (3 Custom Roles)
  - `workflow_state.json` (6 States)
  - `workflow_action_master.json` (6 Actions)
  - `workflow.json` (Training Session Approval Workflow)
- **Single-command deployment:**
  ```bash
  bench get-app fhc_training <repo>
  bench --site fhc.local install-app fhc_training
  bench --site fhc.local migrate
  ```
- **Zero manual configuration needed** on new sites.

---

## Slide 11: Challenges Encountered & Technical Solutions
1. **Challenge 1: Trainer Data Leakage in List Views**
   - *Problem:* Standard Frappe permissions allowed trainers to see all sessions in the list view.
   - *Solution:* Implemented `permission_query_conditions` hook to inject an SQL filter restricting list retrieval to `trainer.user == session.user`.
2. **Challenge 2: Overlapping Date Boundary Checks**
   - *Problem:* Basic date matching missed sessions starting on the same day an earlier session ended.
   - *Solution:* Implemented bidirectional interval intersection: `start_date <= other.end_date AND end_date >= other.start_date`.
3. **Challenge 3: Certificate Idempotency**
   - *Problem:* Repeated button clicks could create duplicate certificates for the same candidate.
   - *Solution:* Added database foreign key backlink on the participant child row and pre-checked `validate_duplicate()` at DocType level.

---

## Slide 12: Live Demonstration Roadmap (10 Minutes)
### Step-by-Step Business Process Walkthrough
1. **Step 1 (Setup):** Review Course & Trainer masters.
2. **Step 2 (Officer):** Log in as `officer@fhc.test` → Create Session → Add Participants → Submit for Approval.
3. **Step 3 (Manager):** Log in as `manager@fhc.test` → Review & Approve Session.
4. **Step 4 (Trainer):** Log in as `trainer@fhc.test` → Demonstrate row-level restriction → Record Attendance & Scores.
5. **Step 5 (Completion & Certification):** Complete Session → Click "Issue Certificates" → Verify generated certificates.
6. **Step 6 (Reporting):** Open "Certification Expiry" report with filters.
7. **Step 7 (Revocation):** Revoke a certificate with reason prompt.
8. **Step 8 (Q&A & Live Change):** Ready for evaluator questions and live technical modification.
