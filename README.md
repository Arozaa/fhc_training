# FHC Training – Training and Certification Management System

A custom Frappe app (module **FHC Training**) for planning training sessions, recording attendance and scores,
approving sessions through a workflow, and issuing/tracking certificates until they expire.

## 1. Purpose
FHC needs one place to manage courses, trainers, scheduled sessions, who attended, who passed, and which
certificates are about to expire. This app replaces spreadsheets with a controlled, role-based process.

## 2. Environment (Verified System Specifications)
| Item | Version used | Notes |
|---|---|---|
| OS | Ubuntu 22.04.5 LTS on WSL2 (Windows host) |
| Python | 3.10.12 |
| Node.js / Yarn | v18.20.8 / 1.22.22 |
| MariaDB | 10.6.23 |
| Redis | 6.0.16 |
| Frappe Framework | 15.122.0 (branch `version-15`) | Active production/dev release |
| ERPNext | 15.122.0 (branch `version-15`) | Core ERP module suite |
| Frappe Bench | 5.31.0 | CLI bench tool |

### Environment setup commands (Ubuntu / WSL2)
```bash
sudo apt update && sudo apt install -y git python3-dev python3-venv python3-pip redis-server \
  mariadb-server mariadb-client libmariadb-dev pkg-config xvfb libfontconfig wkhtmltopdf curl
# Node 18 via nvm, then: npm install -g yarn
sudo mysql_secure_installation          # also set utf8mb4 in /etc/mysql/mariadb.conf.d/ (see Frappe docs)
pip3 install frappe-bench
bench init --frappe-branch version-15 frappe-bench && cd frappe-bench
bench new-site fhc.local --admin-password <choose> --mariadb-root-password <root-pw>
bench get-app erpnext --branch version-15
bench --site fhc.local install-app erpnext
bench use fhc.local
bench start        # open http://fhc.local:8000 (add "127.0.0.1 fhc.local" to /etc/hosts if needed)
```
Follow the official Frappe installation guide for details specific to your OS.

## 3. Install this app
```bash
cd ~/frappe-bench
bench get-app fhc_training <path-or-url-of-this-repo>
bench --site fhc.local install-app fhc_training     # also imports roles + workflow fixtures
bench --site fhc.local migrate
bench build --app fhc_training && bench restart
```
Optional demo data and users (password is passed by you, never stored in Git):
```bash
bench --site fhc.local execute fhc_training.setup.sample_data.create_demo_users --kwargs "{'password': 'YOUR-PASSWORD'}"
bench --site fhc.local execute fhc_training.setup.sample_data.create_sample_data
```

## 4. Data model
| DocType | Type | Purpose | Naming |
|---|---|---|---|
| Training Course | Master | What is taught, pass mark, certificate validity | `CRS-.####` |
| Trainer | Master | Who teaches; optional link to a User | `TRN-.####` |
| Training Session | Transaction (workflow) | A scheduled run of a course | `TS-.YYYY.-.####` |
| Training Participant | **Child table** of Session | Attendee, attendance, score, result, certificate | row |
| Certification | Transaction | Certificate issued to one participant | `CERT-.YYYY.-.#####` |

Links: Session → Course, Session → Trainer, Certification → Course, Certification → Session, Participant → Certification.

## 5. Roles
| Role | Can do |
|---|---|
| Training Officer | Create/edit courses, trainers, draft sessions; submit for approval; issue certificates |
| Training Manager | Everything, plus approve/reject/complete/cancel sessions and revoke certificates |
| Trainer | Read-only masters; sees **only own sessions**; enters attendance/scores; completes approved sessions |

## 6. Workflow – "Training Session Approval"
`Draft → (Submit for Approval: Officer) → Pending Approval → (Approve: Manager) → Approved → (Complete: Trainer/Manager) → Completed`
Also: Pending Approval → Rejected (Manager) → Draft (Officer, "Revise"); Approved → Cancelled (Manager).

## 7. Main features / business rules
- End date ≥ start date; new sessions cannot start in the past.
- Course must be active, trainer must be Active; a trainer cannot hold two overlapping Pending/Approved sessions.
- Participant limit and duplicate-participant checks; scores must be 0–100.
- Pass/Fail calculated automatically against the course pass mark once the session is Approved.
- Cannot submit without participants; cannot complete before the end date.
- **Issue Certificates** button creates one certificate per passing participant (idempotent), expiry from course validity.
- Daily scheduler marks expired certificates; **Revoke** button (Manager) requires a reason.
- Colour-coded list indicators, form dashboard indicators, connections panels on Course/Trainer/Session.
- Script Report **Certification Expiry** with filters: Course, Status, Expiring Within (Days).
- Row-level permission: Trainers only see their own sessions (`permission_query_conditions` + `has_permission`).

## 8. Reproducibility
Roles, workflow states, workflow actions and the workflow itself are exported as **fixtures** (`fhc_training/fixtures`)
and declared in `hooks.py`, so `install-app` recreates them on any compatible site. After changing them in the UI run
`bench --site fhc.local export-fixtures --app fhc_training` and commit the result.

## 9. Testing
Automated: `bench --site fhc.local set-config allow_tests true && bench --site fhc.local run-tests --app fhc_training`
Manual checklist: see `docs/TEST_CHECKLIST.md` (record your own results and screenshots).

## 10. Project layout
```
fhc_training/
  hooks.py  tasks.py  fixtures/  setup/sample_data.py
  fhc_training/            # the module
    doctype/ (course, trainer, training_participant, training_session, certification)
    report/certification_expiry/
```

## 11. Setup challenges encountered and how they were solved
| Problem | Cause | Solution |
|---|---|---|
| `bench` not recognised in Windows PowerShell | Bench only runs on Linux | Installed WSL2 with Ubuntu 22.04 and worked inside it |
| `new-site` failed: MariaDB error 1698 "Access denied for user 'root'" | MariaDB root used socket authentication instead of a password | Set a root password with `ALTER USER 'root'@'localhost' IDENTIFIED BY ...` |
| "Site already exists" after a failed `new-site` | Half-created site left behind | `bench drop-site` then `bench new-site` again |
| `install-app erpnext` failed: Redis connection refused on port 11000 | The bench Redis instances were not running | Ran `bench start` first, then installed ERPNext from a second terminal |
| Browser showed 404 on localhost:8000 | Bench had no default site after the site was recreated | `bench use fhc.local` and `bench set-config -g default_site fhc.local`, then restarted bench |
| Demo-user creation rejected the password | Frappe's password-strength policy | Used a stronger password supplied on the command line |
| A second WSL window could not find the bench | Two Ubuntu distributions installed, with separate users | Opened the correct distro with `wsl -d Ubuntu-22.04 -u <user>` |
| Trainer could not see sessions | The Trainer record had no linked System User | Set the `user` field on the Trainer record |

Note: `bench start` must be running while installing apps, because installation uses the Redis queue.
