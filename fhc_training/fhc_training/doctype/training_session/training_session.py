import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_months, flt, getdate, today

BLOCKING_STATES = ("Pending Approval", "Approved")  # states that "reserve" a trainer
RESULT_STATES = ("Approved", "Completed")           # states where scores become Pass/Fail
MAX_SESSION_CAPACITY = 30  # corporate limit on participants per session
STAFF_ROLES = {"System Manager", "Training Manager", "Training Officer"}


class TrainingSession(Document):
    # ------------------------------------------------------------------ validation
    def validate(self):
        self.validate_dates()
        self.validate_course_and_trainer()
        self.validate_trainer_availability()
        self.validate_participants()
        self.calculate_results()
        self.validate_workflow_rules()

    def validate_dates(self):
        if getdate(self.end_date) < getdate(self.start_date):
            frappe.throw(_("End Date cannot be before Start Date."))
        if self.is_new() and getdate(self.start_date) < getdate(today()):
            frappe.throw(_("Start Date cannot be in the past for a new session."))

    def validate_course_and_trainer(self):
        if (self.is_new() or self.has_value_changed("course")) and not frappe.db.get_value(
            "Training Course", self.course, "is_active"
        ):
            frappe.throw(_("Course {0} is inactive and cannot be scheduled.").format(self.course))
        if (self.is_new() or self.has_value_changed("trainer")) and frappe.db.get_value(
            "Trainer", self.trainer, "status"
        ) != "Active":
            frappe.throw(_("Trainer {0} is not Active.").format(self.trainer))

    def validate_trainer_availability(self):
        """A trainer cannot run two overlapping sessions that are pending or approved."""
        clash = frappe.get_all(
            "Training Session",
            filters=[
                ["trainer", "=", self.trainer],
                ["name", "!=", self.name or ""],
                ["workflow_state", "in", list(BLOCKING_STATES)],
                ["start_date", "<=", self.end_date],
                ["end_date", ">=", self.start_date],
            ],
            pluck="name",
            limit=1,
        )
        if clash:
            frappe.throw(
                _("Trainer {0} is already booked in session {1} during these dates.").format(self.trainer, clash[0])
            )

    def validate_participants(self):
        if (self.max_participants or 0) <= 0:
            frappe.throw(_("Max Participants must be greater than zero."))
        if self.max_participants > MAX_SESSION_CAPACITY:
            frappe.throw(
                _("Max Participants cannot exceed {0} per session.").format(MAX_SESSION_CAPACITY)
            )    
        if len(self.participants) > self.max_participants:
            frappe.throw(
                _("Participants ({0}) exceed the maximum allowed ({1}).").format(
                    len(self.participants), self.max_participants
                )
            )
        seen = set()
        for row in self.participants:
            row.participant_id = (row.participant_id or "").strip().upper()
            if row.participant_id in seen:
                frappe.throw(_("Row {0}: Participant {1} is listed more than once.").format(row.idx, row.participant_id))
            seen.add(row.participant_id)
            if row.score is not None and not 0 <= flt(row.score) <= 100:
                frappe.throw(_("Row {0}: Score must be between 0 and 100.").format(row.idx))

    def calculate_results(self):
        """Pass/Fail is only derived once the session is approved (scores are being captured)."""
        for row in self.participants:
            if self.workflow_state in RESULT_STATES and row.attendance == "Present":
                row.result = "Pass" if flt(row.score) >= flt(self.passing_score) else "Fail"
            else:
                row.result = ""
        self.total_participants = len(self.participants)
        self.passed_count = sum(1 for r in self.participants if r.result == "Pass")

    def validate_workflow_rules(self):
        if self.workflow_state == "Pending Approval" and not self.participants:
            frappe.throw(_("Add at least one participant before submitting for approval."))
        if self.workflow_state == "Completed":
            if getdate(self.end_date) > getdate(today()):
                frappe.throw(_("A session cannot be completed before its End Date ({0}).").format(self.end_date))
            if not self.participants:
                frappe.throw(_("Cannot complete a session without participants."))


# ---------------------------------------------------------------------- actions
@frappe.whitelist()
def issue_certificates(session_name):
    """Create a Certification for every participant who passed and has none yet."""
    frappe.only_for(("System Manager", "Training Manager", "Training Officer"))
    session = frappe.get_doc("Training Session", session_name)
    session.check_permission("write")
    if session.workflow_state != "Completed":
        frappe.throw(_("Certificates can only be issued for Completed sessions."))

    validity = frappe.db.get_value("Training Course", session.course, "validity_months") or 0
    created = []
    for row in session.participants:
        if row.result != "Pass" or row.certificate:
            continue
        cert = frappe.get_doc(
            {
                "doctype": "Certification",
                "participant_id": row.participant_id,
                "participant_name": row.participant_name,
                "email": row.email,
                "course": session.course,
                "training_session": session.name,
                "issue_date": session.end_date,
                "expiry_date": add_months(session.end_date, validity) if validity else None,
                "score": row.score,
            }
        ).insert()
        row.db_set("certificate", cert.name)
        created.append(cert.name)
    return created


# ------------------------------------------------------------------ permissions
def _trainer_names(user):
    return frappe.get_all("Trainer", filters={"user": user}, pluck="name")


def get_permission_query_conditions(user=None):
    """SQL condition added to every list query: Trainers only see their own sessions."""
    user = user or frappe.session.user
    roles = set(frappe.get_roles(user))
    if user == "Administrator" or roles & STAFF_ROLES:
        return ""
    if "Trainer" in roles:
        names = _trainer_names(user)
        if names:
            quoted = ", ".join(frappe.db.escape(n) for n in names)
            return f"`tabTraining Session`.`trainer` in ({quoted})"
    return "1=0"


def has_permission(doc, user=None, ptype=None, **kwargs):
    """Same rule as above, applied to a single document."""
    user = user or frappe.session.user
    roles = set(frappe.get_roles(user))
    if user == "Administrator" or roles & STAFF_ROLES:
        return True
    if "Trainer" in roles:
        return doc.trainer in _trainer_names(user)
    return False
