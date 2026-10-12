# Live Technical Change Guide & Cheatsheet

**Federal Housing Corporation (FHC) — Practical Exam Assignment (Section 10)**  
**Objective:** Prepare the candidate to quickly, cleanly, and confidently implement and explain any live change requested by the evaluation committee during the presentation.

---

## Overview: How to Approach the Live Change
When the evaluator asks for a change:
1. **Repeat and clarify the requirement:** Confirm the DocType, field type, logic, or role affected.
2. **Explain before typing:** Briefly state which file you are editing (e.g. `training_session.py`, `training_session.js`, DocType JSON, or Report files).
3. **Make the edit cleanly:** Edit the file or apply via Desk.
4. **Run migrate / build if necessary:**
   - Python or JSON schema change: `bench --site fhc.local migrate`
   - Client JS change: Hard refresh in browser (`Ctrl + Shift + R`).
5. **Demonstrate the change in the UI:** Show the new behavior working and explain why the solution is robust.

---

## Scenario 1: Adding a Field to a DocType
**Example Prompt:** *"Please add a field called 'Training Room / Venue Details' or 'Budget / Cost per Participant' to the Training Session."*

### Steps:
1. Open `fhc_training/fhc_training/doctype/training_session/training_session.json` (or use Desk > DocType > Training Session).
2. To add a Data field `room_number`:
   Insert into the `"fields"` array:
   ```json
   {
     "fieldname": "room_number",
     "fieldtype": "Data",
     "label": "Room / Venue Details",
     "insert_after": "venue"
   }
   ```
3. Run schema update:
   ```bash
   bench --site fhc.local migrate
   ```
4. **UI Explanation:** Reload the Training Session form. The "Room / Venue Details" input is now visible immediately below "Venue".

---

## Scenario 2: Changing a Validation Rule
**Example Prompt:** *"Change the passing score rule so that no course can have a passing score lower than 50, or prevent sessions from having more than 30 participants."*

### Steps:
1. Open `fhc_training/fhc_training/doctype/training_session/training_session.py`.
2. Locate `validate_participants()`:
   ```python
   def validate_participants(self):
       if (self.max_participants or 0) <= 0:
           frappe.throw(_("Max Participants must be greater than zero."))
       # Add the new rule requested by the evaluator:
       if self.max_participants > 30:
           frappe.throw(_("Maximum participants cannot exceed 30 per corporate policy."))
   ```
3. Save the file.
4. **UI Explanation:** Try saving a Training Session with `max_participants = 35`. Frappe instantly throws the validation banner: `"Maximum participants cannot exceed 30 per corporate policy."`

---

## Scenario 3: Modifying a Workflow Condition or Transition
**Example Prompt:** *"Allow the Training Manager to send an Approved session back to Draft for revisions before it is Completed."*

### Steps:
1. Open Desk > **Workflow** > `Training Session Approval`.
2. Scroll to the **Transitions** table.
3. Add a new transition row:
   - **State:** `Approved`
   - **Action:** `Revise`
   - **Next State:** `Draft`
   - **Allowed:** `Training Manager`
4. Click **Save**.
5. Export fixtures so the change is persisted in code:
   ```bash
   bench --site fhc.local export-fixtures --app fhc_training
   ```
6. **UI Explanation:** Log in as Training Manager. On an `Approved` session, a new workflow button "Revise" is now available, smoothly resetting the state back to `Draft`.

---

## Scenario 4: Adjusting Role Permissions
**Example Prompt:** *"Give the Training Officer read-only access to view Certifications, but prevent them from revoking or cancelling."*

### Steps:
1. Open `fhc_training/fhc_training/doctype/certification/certification.json` (or Role Permissions Manager).
2. In `"permissions"` array, add or verify:
   ```json
   {
     "role": "Training Officer",
     "read": 1,
     "write": 0,
     "create": 0,
     "delete": 0
   }
   ```
3. Check `certification.py`: The `revoke()` method is guarded by:
   ```python
   frappe.only_for(("System Manager", "Training Manager"))
   ```
   So Officers cannot invoke revocation even if attempted via API.
4. **UI Explanation:** Log in as `officer@fhc.test`. Open Certification list. Officers can inspect certificates, but the "Revoke" button is hidden and write actions are disabled.

---

## Scenario 5: Adding a Report Filter
**Example Prompt:** *"Add a Trainer filter or Date Range filter to the Certification Expiry Script Report."*

### Steps:
1. Open `fhc_training/fhc_training/report/certification_expiry/certification_expiry.js`.
2. Add a new filter to the `filters` array:
   ```javascript
   {
       "fieldname": "trainer",
       "label": __("Trainer"),
       "fieldtype": "Link",
       "options": "Trainer"
   }
   ```
3. Open `fhc_training/fhc_training/report/certification_expiry/certification_expiry.py`:
4. Update `get_data(filters)`:
   ```python
   if filters.get("trainer"):
       # Join on Training Session or subquery
       session_names = frappe.get_all("Training Session", filters={"trainer": filters.trainer}, pluck="name")
       conditions["training_session"] = ["in", session_names or [""]]
   ```
5. Reload the report page (`Ctrl + Shift + R`).
6. **UI Explanation:** The report now features the new "Trainer" dropdown filter, dynamically narrowing records to only certificates issued under that instructor.

---

## Scenario 6: Changing Client-Side Form Behavior
**Example Prompt:** *"Show an alert banner or highlight in red when the number of participants reaches 100% capacity."*

### Steps:
1. Open `fhc_training/fhc_training/doctype/training_session/training_session.js`.
2. In `update_summary(frm)`:
   ```javascript
   function update_summary(frm) {
       const rows = frm.doc.participants || [];
       frm.set_value("total_participants", rows.length);
       frm.set_value("passed_count", rows.filter((r) => r.result === "Pass").length);

       if (frm.doc.max_participants && rows.length === frm.doc.max_participants) {
           frappe.show_alert({
               message: __("Warning: Session has reached full capacity ({0}/{0})!", [frm.doc.max_participants]),
               indicator: "orange"
           });
       }
   }
   ```
3. Save the file and hard-refresh the form in the browser.
4. **UI Explanation:** When adding the final allowed participant row, the orange toast alert notifies the user in real time that maximum capacity is reached.

---

## Key Bench Commands Reference for Live Demo
| Task | Command |
|---|---|
| Apply DocType Schema Changes | `bench --site fhc.local migrate` |
| Clear Server Cache | `bench --site fhc.local clear-cache` |
| Export Fixtures to Repo | `bench --site fhc.local export-fixtures --app fhc_training` |
| Run Automated Test Suite | `bench --site fhc.local run-tests --app fhc_training` |
| Execute Nightly Scheduler Task | `bench --site fhc.local execute fhc_training.tasks.mark_expired_certifications` |
