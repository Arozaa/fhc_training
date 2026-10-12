# Functional & Automated Test Checklist and Results

**Application:** FHC Training (`fhc_training`)  
**Site:** `fhc.local` (Port 8000)  
**Evaluation Environment:** Ubuntu 22.04.5 LTS (WSL2), Python 3.10.12, MariaDB 10.6.23, Frappe v15.122.0, ERPNext v15.122.0  
**Execution Date:** 2026-10-11  
**Overall Status:** **25 / 25 PASSED (100% Pass Rate)**  

---

## 1. Executive Summary

| Category | Total Test Cases | Passed | Failed | Status |
|---|---|---|---|---|
| Master Data & Validation | 8 | 8 | 0 | **PASS** |
| Workflow & Business Logic | 7 | 7 | 0 | **PASS** |
| Certificate Lifecycle & Expiry | 4 | 4 | 0 | **PASS** |
| Reporting & Filters | 1 | 1 | 0 | **PASS** |
| RBAC & Permission Query Security | 3 | 3 | 0 | **PASS** |
| Automation & Background Scheduler | 1 | 1 | 0 | **PASS** |
| Full Automated Suite (`run-tests`) | 1 (18 subtests) | 1 | 0 | **PASS** |
| **Total** | **25** | **25** | **0** | **100%** |

---

## 2. Functional Test Matrix

| # | Scenario | Test Steps / Action | Expected Behavior | Result | Verification Notes / Evidence |
|---|---|---|---|---|---|
| 1 | Create course | Training Course → New, pass mark 70, validity 12 | Auto-named `CRS-.####` (e.g. `CRS-0001`), saved | **PASS** | Verified in DB: `CRS-0001` created with 70% passing score, 12 months validity. |
| 2 | Invalid pass mark | Set pass mark to 0 or 150 | Validation error blocks save | **PASS** | Blocked with `ValidationError`: Score must be between 1 and 100. |
| 3 | Create session | New session, future dates, 3 participants | Saved as `TS-2026-0001`, status Draft, totals = 3 | **PASS** | Verified: Draft created, `total_participants` automatically computed as 3. |
| 4 | End before start | Set End Date earlier than Start Date | Validation error blocks save | **PASS** | `frappe.throw(_("End Date cannot be before Start Date."))` triggered. |
| 5 | Start in past | Create new session with past start date | Validation error blocks save | **PASS** | `frappe.throw(_("Start Date cannot be in the past for a new session."))` triggered. |
| 6 | Participant limit | Set Max Participants = 2, add 3 rows | Client alert + server validation error | **PASS** | Client throws banner alert; server raises `ValidationError` on save. |
| 7 | Duplicate participant | Add same `participant_id` (e.g., `FHC-001`) twice | Validation error blocks duplicate row | **PASS** | Case-insensitive duplicate check triggers `ValidationError: Participant FHC-001 is listed more than once`. |
| 8 | Inactive course/trainer | Pick inactive course or inactive trainer | Filter prevents selection; backend blocks | **PASS** | Form filter filters out `is_active=0` and `status!="Active"`; backend throws error if forced. |
| 9 | Trainer double booking | Create overlapping session for same trainer when 1st is Approved | Overlap clash detected and blocked | **PASS** | Backend checks date overlap against blocking states (`Pending Approval`, `Approved`); throws clash warning. |
| 10 | Submit with no participants | Click "Submit for Approval" on empty table | Action blocked with error | **PASS** | `frappe.throw(_("Add at least one participant before submitting for approval."))` raised. |
| 11 | Workflow happy path | Officer submits → Manager approves | Workflow transition Draft → Pending Approval → Approved | **PASS** | Role-based workflow transitions execute seamlessly; state changes to `Approved`. |
| 12 | Reject / revise | Manager rejects → Officer revises | Transitions Pending Approval → Rejected → Draft | **PASS** | Manager triggers "Reject"; Officer sees "Revise" button returning session to `Draft`. |
| 13 | Scores & results | In Approved session: enter 80 / 40 / Absent | Auto-calculates Pass / Fail / blank; `passed_count = 1` | **PASS** | Dynamic calculation updates row result and recalculates `passed_count` on form change and save. |
| 14 | Complete too early | Trigger "Complete" before session End Date | Transition blocked | **PASS** | `frappe.throw(_("A session cannot be completed before its End Date."))` raised. |
| 15 | Complete session | When date reached, Trainer or Manager marks Complete | State transitions to `Completed` | **PASS** | Workflow action allowed for Trainer/Manager when end date is reached. |
| 16 | Issue certificates | Click "Issue Certificates" on Completed session | 1 certificate created; expiry = end date + validity | **PASS** | `issue_certificates()` creates `CERT-2026-00001`, stamps cert ID on participant row. |
| 17 | Issue idempotency | Click "Issue Certificates" again or recall method | No duplicate certificates created | **PASS** | Method checks uncertified passers; returns empty list if already issued. |
| 18 | Duplicate certificate | Manually insert certificate for same participant & session | Unique constraint validation blocks it | **PASS** | `Certification.validate_duplicate()` throws error if participant already holds active certificate for session. |
| 19 | Revoke certificate | Training Manager clicks "Revoke", enters reason | Status changed to `Revoked`, reason logged | **PASS** | Custom modal prompt records reason and sets `status = "Revoked"`. Re-revoking blocked. |
| 20 | Expiry Report | Open "Certification Expiry", filter Course/Status/Days | Filtered rows displayed with color badges | **PASS** | Script report runs accurately; computes `days_remaining`; filters by course, status, and threshold. |
| 21 | Trainer visibility | Log in as `trainer@fhc.test` | Trainer sees ONLY assigned sessions | **PASS** | Row-level permission query condition (`get_permission_query_conditions`) filters out all other trainers' sessions. |
| 22 | Officer restrictions | Log in as `officer@fhc.test` | Cannot Approve or Delete approved records | **PASS** | Officer role has no transition permission to `Approved`; workflow buttons restricted. |
| 23 | Manager rights | Log in as `manager@fhc.test` | Full Approve, Reject, Cancel, Revoke rights | **PASS** | Manager has elevated permissions across all states and certificate actions. |
| 24 | Daily scheduler | Run `fhc_training.tasks.mark_expired_certifications` | Past-expiry Active certificates become `Expired` | **PASS** | Tested via bench execute; correctly flips certificates past expiry date from `Active` to `Expired`. |
| 25 | Automated unit tests | `bench --site fhc.local run-tests --app fhc_training` | 18 unit tests execute and pass | **PASS** | `Ran 18 tests in 6.361s - OK` (All unit tests pass with zero failures or errors). |

---

## 3. Automated Unit Test Execution Details

Automated tests are located in:
1. `fhc_training/fhc_training/doctype/training_session/test_training_session.py` (13 test cases)
2. `fhc_training/fhc_training/doctype/certification/test_certification.py` (5 test cases)

### Execution Output:
```text
$ bench --site fhc.local run-tests --app fhc_training
test_duplicate_certificate_blocked (fhc_training.fhc_training.doctype.certification.test_certification.TestCertification) ... ok
test_expiry_before_issue_blocked (fhc_training.fhc_training.doctype.certification.test_certification.TestCertification) ... ok
test_expiry_calculated_from_course_validity (fhc_training.fhc_training.doctype.certification.test_certification.TestCertification) ... ok
test_revoke_requires_reason_and_sets_status (fhc_training.fhc_training.doctype.certification.test_certification.TestCertification) ... ok
test_scheduler_marks_expired (fhc_training.fhc_training.doctype.certification.test_certification.TestCertification) ... ok
test_cannot_complete_before_end_date (fhc_training.fhc_training.doctype.training_session.test_training_session.TestTrainingSession) ... ok
test_create_valid_session (fhc_training.fhc_training.doctype.training_session.test_training_session.TestTrainingSession) ... ok
test_duplicate_participant_fails (fhc_training.fhc_training.doctype.training_session.test_training_session.TestTrainingSession) ... ok
test_end_before_start_fails (fhc_training.fhc_training.doctype.training_session.test_training_session.TestTrainingSession) ... ok
test_inactive_course_fails (fhc_training.fhc_training.doctype.training_session.test_training_session.TestTrainingSession) ... ok
test_inactive_trainer_fails (fhc_training.fhc_training.doctype.training_session.test_training_session.TestTrainingSession) ... ok
test_past_start_date_fails (fhc_training.fhc_training.doctype.training_session.test_training_session.TestTrainingSession) ... ok
test_results_and_certificate_issue (fhc_training.fhc_training.doctype.training_session.test_training_session.TestTrainingSession) ... ok
test_staff_has_no_row_filter (fhc_training.fhc_training.doctype.training_session.test_training_session.TestTrainingSession) ... ok
test_submit_for_approval_needs_participants (fhc_training.fhc_training.doctype.training_session.test_training_session.TestTrainingSession) ... ok
test_too_many_participants_fails (fhc_training.fhc_training.doctype.training_session.test_training_session.TestTrainingSession) ... ok
test_trainer_double_booking_fails (fhc_training.fhc_training.doctype.training_session.test_training_session.TestTrainingSession) ... ok
test_trainer_sees_only_own_sessions (fhc_training.fhc_training.doctype.training_session.test_training_session.TestTrainingSession) ... ok

----------------------------------------------------------------------
Ran 18 tests in 6.361s

OK
```

---

## 4. Role-Based Access Control (RBAC) Verification

| User | Email | Assigned Role | Access Scope |
|---|---|---|---|
| **Training Officer** | `officer@fhc.test` | Training Officer | Can create and edit Training Courses, Trainers, and draft Sessions. Can submit sessions for approval. Cannot approve sessions. |
| **Training Manager** | `manager@fhc.test` | Training Manager | Can approve, reject, or cancel sessions. Can complete sessions. Can revoke certifications. |
| **Trainer** | `trainer@fhc.test` | Trainer | Can view only sessions where `trainer == Trainer One`. Can record scores and mark attendance. Cannot see other trainers' sessions. |

### Row-Level Security Code Verification:
The query restriction is implemented in `hooks.py`:
```python
permission_query_conditions = {
    "Training Session": "fhc_training.fhc_training.doctype.training_session.training_session.get_permission_query_conditions",
}
has_permission = {
    "Training Session": "fhc_training.fhc_training.doctype.training_session.training_session.has_permission",
}
```
When `trainer@fhc.test` executes `frappe.get_list("Training Session")`, the query automatically appends:
```sql
`tabTraining Session`.`trainer` IN ('TRN-0001')
```
Ensuring data isolation between instructors.
