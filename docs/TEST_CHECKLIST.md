# Functional Test Checklist
Run on a fresh site with the app installed. Mark Result with Pass/Fail and note the date after **you** run each test.

| # | Scenario | Steps | Expected | Result |
|---|---|---|---|---|
| 1 | Create course | Training Course → New, pass mark 70, validity 12 | Saved as CRS-0001 | |
| 2 | Invalid pass mark | Set pass mark 0 or 150 | Error blocks save | |
| 3 | Create session | New session, future dates, 3 participants | Saved as Draft, totals = 3 | |
| 4 | End before start | End date earlier than start | Error | |
| 5 | Start in past | New session with past start | Error | |
| 6 | Participant limit | Max 2, add 3 participants | Error | |
| 7 | Duplicate participant | Same ID twice | Error | |
| 8 | Inactive course/trainer | Pick inactive course or trainer | Not selectable / error | |
| 9 | Trainer double booking | Two overlapping sessions, same trainer, first Approved | Second blocked | |
| 10 | Submit with no participants | Empty table → Submit for Approval | Error | |
| 11 | Workflow happy path | Officer submits → Manager approves | State = Approved | |
| 12 | Reject / revise | Manager rejects → Officer revises | Rejected → Draft | |
| 13 | Scores & results | Approved: enter 80 / 40 / Absent | Pass / Fail / blank, Passed = 1 | |
| 14 | Complete too early | Complete before end date | Error | |
| 15 | Complete | After end date, Trainer/Manager completes | State = Completed | |
| 16 | Issue certificates | Click Issue Certificates | 1 certificate, expiry = end + validity | |
| 17 | Issue twice | Click again / button hidden | No duplicates | |
| 18 | Duplicate certificate | Create same participant+session manually | Error | |
| 19 | Revoke | Manager → Revoke with reason | Status Revoked | |
| 20 | Report | Certification Expiry, filters Course/Status/Expiring | Rows filtered, red/orange days | |
| 21 | Trainer visibility | Log in as trainer@fhc.test | Sees only own sessions | |
| 22 | Officer restrictions | Log in as officer | No Approve button; cannot delete | |
| 23 | Manager rights | Log in as manager | Approve, Reject, Revoke available | |
| 24 | Scheduler | `bench --site fhc.local execute fhc_training.tasks.mark_expired_certifications` | Past-expiry Active → Expired | |
| 25 | Automated tests | `bench ... run-tests --app fhc_training` | All pass | |
